# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008 ojnkpjg
# Copyright (C) 2008-2011, 2014, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2019 Michael Wiencek
# Copyright (C) 2012-2013, 2016-2017 Wieland Hoffmann
# Copyright (C) 2013, 2018 Calvin Walton
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2024 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2022 skelly37
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Rakim Middya
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from collections import (
    OrderedDict,
    defaultdict,
    namedtuple,
)
from enum import IntEnum
import traceback

from PyQt6 import QtNetwork

from picard import log
from picard.album_requests import (
    TaskInfo,
    TaskType,
)
from picard.cluster import Cluster
from picard.collection import add_release_to_user_collections
from picard.config import get_config
from picard.const import VARIOUS_ARTISTS_ID
from picard.file import File
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.item import MetadataItem
from picard.mbjson import (
    medium_to_metadata,
    release_group_to_metadata,
    release_to_metadata,
    track_to_metadata,
)
from picard.metadata import (
    Metadata,
    run_album_metadata_processors,
    run_track_metadata_processors,
)
from picard.plugin import PluginFunctions
from picard.script import (
    ScriptError,
    ScriptParser,
    iter_active_tagging_scripts,
)
from picard.track import Track
from picard.util import (
    find_best_match,
    format_time,
    mbid_validate,
)
from picard.util.textencoding import asciipunct


RECORDING_QUERY_LIMIT = 100


def _create_artist_node_dict(source_node):
    return {x['artist']['id']: x['artist'] for x in source_node['artist-credit']}


def _copy_artist_nodes(source, target_node):
    for credit in target_node['artist-credit']:
        artist_node = source.get(credit['artist']['id'])
        if artist_node:
            credit['artist'] = artist_node


class AlbumArtist(MetadataItem):
    def __init__(self, album_artist_id):
        super().__init__(album_artist_id)


class AlbumStatus(IntEnum):
    NONE = 0
    LOADING = 1
    ERROR = 2
    LOADED = 3


class ParseResult(IntEnum):
    PARSED = 0
    REDIRECT = 1
    MISSING_TRACK_RELS = 2


class TracksCache:
    """Cache for track lookups by recording/track ID and track/disc numbers."""

    def __init__(self):
        """Initialize an empty cache"""
        self._cache = defaultdict(lambda: None)
        self._initialized = False

    def build(self, tracks):
        """Populate the cache with tracks, creating lookup keys from their metadata.

        For each track, creates cache entries with combinations of:
        - recording ID
        - track ID
        - track number
        - disc number

        Args:
            tracks: List of Track objects to add to the cache
        """
        for track in tracks:
            tm_recordingid = track.orig_metadata['musicbrainz_recordingid']
            tm_trackid = track.orig_metadata['musicbrainz_trackid']
            tm_tracknumber = track.orig_metadata['tracknumber']
            tm_discnumber = track.orig_metadata['discnumber']
            for tup in (
                (tm_recordingid, tm_tracknumber, tm_discnumber),
                (tm_recordingid, tm_tracknumber),
                (tm_recordingid,),
                (tm_trackid, tm_tracknumber, tm_discnumber),
                (tm_trackid, tm_tracknumber),
                (tm_trackid,),
            ):
                self._cache[tup] = track
        self._initialized = True

    def get_track(self, mbid, tracknumber=None, discnumber=None):
        """Get track from cache by ID and optional track/disc numbers."""
        if tracknumber and discnumber:
            track = self._cache[(mbid, tracknumber, discnumber)]
            if track:
                return track
        if tracknumber:
            track = self._cache[(mbid, tracknumber)]
            if track:
                return track
        return self._cache[(mbid,)]

    def __bool__(self):
        """Returns True if cache was initialized"""
        return self._initialized


class Album(MetadataItem):
    def __init__(self, album_id, discid=None):
        super().__init__(album_id)
        self.tracks = []
        self.loaded = False
        self.load_request = None
        self.release_group = None
        self._files_count = 0
        self._pending_tasks = {}
        self._tracks_loaded = False
        self._discids = set()
        self._recordings_map = {}
        if discid:
            self._discids.add(discid)
        self._after_load_callbacks = []
        self.unmatched_files = Cluster(_("Unmatched Files"), special=True, related_album=self, hide_if_empty=True)
        self.unmatched_files.metadata_images_changed.connect(self.update_metadata_images)
        self.status = AlbumStatus.NONE
        self._album_artists = []
        self.update_children_metadata_attrs = {'metadata', 'orig_metadata'}

    def __repr__(self):
        return '<Album %s %r>' % (self.id, self.metadata['album'])

    def add_task(self, task_id, task_type, description, timeout=None, plugin_id=None, request_factory=None):
        """Add a pending task that must complete before album finalization."""
        import time

        if timeout is not None:
            network_timeout = get_config().setting['network_transfer_timeout_seconds']
            if timeout > network_timeout:
                log.warning(
                    "Task %s has timeout %.1fs which exceeds network timeout %.1fs. "
                    "Capping to network timeout to ensure proper cleanup.",
                    task_id,
                    timeout,
                    network_timeout,
                )
                timeout = network_timeout

        task_info = TaskInfo(
            task_id=task_id,
            type=task_type,
            description=description,
            started_at=time.time(),
            timeout=timeout,
            plugin_id=plugin_id,
        )
        self._pending_tasks[task_id] = task_info
        log.debug("Added %s task %s: %s", task_type.name, task_id, description)

        # If request_factory provided, create and register request atomically
        if request_factory:
            request = request_factory()
            self._pending_tasks[task_id].request = request

    def complete_task(self, task_id):
        """Mark a task as complete."""
        if task_id in self._pending_tasks:
            task_info = self._pending_tasks.pop(task_id)
            log.debug("Completed %s task %s after %.2fs", task_info.type.name, task_id, task_info.elapsed_time())
        else:
            log.warning("Attempted to complete unknown task: %s", task_id)

    def cancel_tasks(self):
        """Cancel all pending tasks and abort their network operations."""
        for task_id, task_info in list(self._pending_tasks.items()):
            log.debug("Canceling %s request %s: %s", task_info.type.name, task_id, task_info.description)
            if task_info.request:
                try:
                    self.tagger.webservice.abort_task(task_info.request)
                except (RuntimeError, ValueError, AttributeError):
                    # Task may already be completed or invalid
                    pass
        self._pending_tasks.clear()

    def check_timed_out_tasks(self):
        """Check for and abort tasks that have exceeded their timeout."""
        for task_id, task_info in list(self._pending_tasks.items()):
            if task_info.is_timed_out():
                log.warning(
                    "Task %s timed out after %.2fs (timeout: %.2fs): %s",
                    task_id,
                    task_info.elapsed_time(),
                    task_info.timeout,
                    task_info.description,
                )
                if task_info.request:
                    try:
                        task_info.request.abort()
                    except RuntimeError:
                        pass
                self._pending_tasks.pop(task_id, None)

    def has_critical_tasks(self):
        """Check if there are any critical tasks pending."""
        return any(r.type == TaskType.CRITICAL for r in self._pending_tasks.values())

    def get_pending_tasks(self):
        """Get all pending tasks for debugging."""
        return dict(self._pending_tasks)

    def _warn_deprecated_requests(self, operation):
        """Emit deprecation warning for album._requests usage (once per location)."""
        from picard.plugin3.api import PluginApi

        PluginApi.deprecation_warning(
            "Using deprecated album._requests (%s). Use api.add_album_task() and api.complete_album_task() instead.",
            operation,
            frame_depth=4,
        )

    @property
    def _requests(self):
        """Compatibility property for old plugins using album._requests.
        Returns count of critical requests only."""
        self._warn_deprecated_requests('read')
        return sum(1 for r in self._pending_tasks.values() if r.type == TaskType.CRITICAL)

    @_requests.setter
    def _requests(self, value):
        """Compatibility setter for old plugins.
        Logs a warning but doesn't break functionality."""
        self._warn_deprecated_requests('write')

    def iterfiles(self, save=False):
        for track in self.tracks:
            yield from track.iterfiles()
        if not save:
            yield from self.unmatched_files.iterfiles()

    def iter_correctly_matched_tracks(self):
        yield from (track for track in self.tracks if track.num_linked_files == 1)

    def append_album_artist(self, album_artist_id):
        """Append artist id to the list of album artists
        and return an AlbumArtist instance"""
        album_artist = AlbumArtist(album_artist_id)
        self._album_artists.append(album_artist)
        return album_artist

    def add_discid(self, discid):
        if not discid:
            return
        self._discids.add(discid)
        for track in self.tracks:
            medium_discids = track.metadata.getall('~musicbrainz_discids')
            track_discids = list(self._discids.intersection(medium_discids))
            if track_discids:
                track.metadata['musicbrainz_discid'] = track_discids
                track.update()
                for file in track.files:
                    file.metadata['musicbrainz_discid'] = track_discids
                    file.update()

    def get_next_track(self, track):
        try:
            index = self.tracks.index(track)
            return self.tracks[index + 1]
        except (IndexError, ValueError):
            return None

    def get_album_artists(self):
        """Returns the list of album artists (as AlbumArtist objects)"""
        return self._album_artists

    def _run_album_metadata_processors(self):
        try:
            run_album_metadata_processors(self, self._new_metadata, self._release_node)
        except BaseException:
            self.error_append(traceback.format_exc())

    def _parse_release(self, release_node):
        """Parse release node from MusicBrainz API data"""
        log.debug("Loading release %r …", self.id)
        self._tracks_loaded = False

        if self._hande_release_redirect(release_node):
            return ParseResult.REDIRECT

        self._release_node = release_node
        self._setup_release_artist_nodes(release_node)
        self._setup_release_group(release_node)
        self._setup_release_metadata(release_node)

        # Add album to collections
        add_release_to_user_collections(release_node)

        if self._needs_track_relationships(release_node):
            return ParseResult.MISSING_TRACK_RELS

        return ParseResult.PARSED

    def _hande_release_redirect(self, release_node):
        """Handle release redirect"""
        release_id = release_node['id']
        if release_id == self.id:
            return False

        self.tagger.mbid_redirects[self.id] = release_id
        album = self.tagger.albums.get(release_id)
        if album:
            log.debug("Release %r already loaded", release_id)
            album.match_files(self.unmatched_files.files)
            album.update()
            self.tagger.remove_album(self)
            return True

        del self.tagger.albums[self.id]
        self.tagger.albums[release_id] = self
        self.id = release_id
        return False

    def _setup_release_artist_nodes(self, release_node):
        """Setup release artist nodes for supplementary data"""
        # Make the release artist nodes available, since they may
        # contain supplementary data (aliases, tags, genres, ratings)
        # which aren't present in the release group, track, or
        # recording artist nodes. We can copy them into those places
        # wherever the IDs match, so that the data is shared and
        # available for use in mbjson.py and external plugins.
        self._release_artist_nodes = _create_artist_node_dict(release_node)

    def _setup_release_group(self, release_node):
        """Process and setup release group data"""
        rg_node = release_node['release-group']
        rg = self.release_group = self.tagger.get_release_group_by_id(rg_node['id'])
        rg.loaded_albums.add(self.id)
        rg.refcount += 1
        _copy_artist_nodes(self._release_artist_nodes, rg_node)
        release_group_to_metadata(rg_node, rg.metadata, rg)

    def _setup_release_metadata(self, release_node):
        """Process and setup release metadata"""
        metadata = self._new_metadata
        metadata.length = 0
        metadata.copy(self.release_group.metadata)
        release_to_metadata(release_node, metadata, album=self)
        self._release_metadata_customization(metadata, release_node)

    def _release_metadata_customization(self, metadata, release_node):
        """Apply modifications to release metadata"""
        config = get_config()

        # Custom VA name
        if metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
            metadata['albumartistsort'] = metadata['albumartist'] = config.setting['va_name']

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            metadata.apply_func(asciipunct)

        metadata['totaldiscs'] = len(release_node['media'])

    def _needs_track_relationships(self, release_node):
        """Check if track relationships needs to be loaded"""
        config = get_config()
        if not config.setting['track_ars']:
            return False

        try:
            for medium_node in release_node['media']:
                if medium_node['track-count']:
                    return 'relations' not in medium_node['tracks'][0]['recording']
        except KeyError:
            pass
        return False

    def _release_request_finished(self, document, http, error):
        if self.load_request is None:
            return
        self.load_request = None
        parse_result = None
        try:
            if error:
                self.error_append(http.errorString())
                # Fix for broken NAT releases
                if error == QtNetwork.QNetworkReply.NetworkError.ContentNotFoundError:
                    config = get_config()
                    nats = False
                    nat_name = config.setting['nat_name']
                    files = list(self.unmatched_files.files)
                    for file in files:
                        recordingid = file.metadata['musicbrainz_recordingid']
                        if mbid_validate(recordingid) and file.metadata['album'] == nat_name:
                            nats = True
                            self.tagger.move_file_to_nat(file, recordingid)
                            self.tagger.nats.update()
                    if nats and not self.get_num_unmatched_files():
                        self.tagger.remove_album(self)
                        error = False
            else:
                try:
                    parse_result = self._parse_release(document)
                    config = get_config()
                    if parse_result == ParseResult.MISSING_TRACK_RELS:
                        log.debug(
                            "Recording relationships not loaded in initial request for %r, issuing separate requests",
                            self,
                        )
                        self._request_recording_relationships()
                    elif parse_result == ParseResult.PARSED:
                        self._run_album_metadata_processors()
                    elif parse_result == ParseResult.REDIRECT:
                        error = False
                except Exception:
                    error = True
                    self.error_append(traceback.format_exc())
        finally:
            self.complete_task('release_metadata')
            if parse_result == ParseResult.PARSED or error:
                self._finalize_loading(error)

    def _request_recording_relationships(self, offset=0, limit=RECORDING_QUERY_LIMIT):
        inc = (
            'artist-rels',
            'recording-rels',
            'release-rels',
            'url-rels',
            'work-rels',
            'work-level-rels',
        )
        log.debug("Loading recording relationships for %r (offset=%i, limit=%i)", self, offset, limit)
        request_id = f'recording_rels_{offset}'

        def create_request():
            self.load_request = self.tagger.mb_api.browse_recordings(
                self._recordings_request_finished,
                inc=inc,
                release=self.id,
                limit=limit,
                offset=offset,
            )
            return self.load_request

        self.add_task(
            request_id,
            TaskType.CRITICAL,
            f'Recording relationships (offset={offset}, limit={limit})',
            request_factory=create_request,
        )

    def _recordings_request_finished(self, document, http, error):
        offset = document.get('recording-offset', 0) if not error else 0
        request_id = f'recording_rels_{offset}'

        if error:
            self.error_append(http.errorString())
            self.complete_task(request_id)
            self._finalize_loading(error)
        else:
            for recording in document.get('recordings', []):
                recording_id = recording.get('id')
                if recording_id:
                    self._recordings_map[recording_id] = recording
            count = document.get('recording-count', 0)
            next_offset = offset + RECORDING_QUERY_LIMIT
            if next_offset < count:
                self.complete_task(request_id)
                self._request_recording_relationships(offset=next_offset)
            else:
                # Merge separately loaded recording relationships into release node
                self._merge_release_recording_relationships()
                self._run_album_metadata_processors()
                self.complete_task(request_id)
                self._finalize_loading(error)

    def _merge_recording_relationships(self, track_node):
        if 'relations' not in track_node['recording']:
            recording = self._recordings_map.get(track_node['recording']['id'])
            if recording:
                track_node['recording']['relations'] = recording.get('relations', [])

    def _merge_release_recording_relationships(self):
        for medium_node in self._release_node['media']:
            pregap_node = medium_node.get('pregap')
            if pregap_node:
                self._merge_recording_relationships(pregap_node)

            for track_node in medium_node.get('tracks', []):
                self._merge_recording_relationships(track_node)

            for track_node in medium_node.get('data-tracks', []):
                self._merge_recording_relationships(track_node)

        self._recordings_map = {}

    def _finalize_loading_track(self, track_node, metadata, artists, extra_metadata=None):
        # As noted in `_parse_release` above, the release artist nodes
        # may contain supplementary data that isn't present in track
        # artist nodes. Similarly, the track artists may contain
        # information which the recording artists don't. Copy this
        # information across to wherever the artist IDs match.
        _copy_artist_nodes(self._release_artist_nodes, track_node)
        _copy_artist_nodes(self._release_artist_nodes, track_node['recording'])
        _copy_artist_nodes(_create_artist_node_dict(track_node), track_node['recording'])

        track = Track(track_node['recording']['id'], self)
        self._new_tracks.append(track)

        # Get track metadata
        tm = track.metadata
        tm.copy(metadata)
        track_to_metadata(track_node, track)
        track._customize_metadata()

        self._new_metadata.length += tm.length
        artists.add(tm['artist'])
        if extra_metadata:
            tm.update(extra_metadata)

        # Run track metadata plugins
        try:
            run_track_metadata_processors(self, tm, track_node, self._release_node)
        except BaseException:
            self.error_append(traceback.format_exc())

        return track

    def _load_tracks(self):
        artists = set()
        all_media = []
        absolutetracknumber = 0

        def _load_track(node, mm, artists, extra_metadata):
            nonlocal absolutetracknumber
            absolutetracknumber += 1
            extra_metadata['~absolutetracknumber'] = absolutetracknumber
            self._finalize_loading_track(node, mm, artists, extra_metadata)

        va = self._new_metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID

        djmix_ars = {}
        if hasattr(self._new_metadata, '_djmix_ars'):
            djmix_ars = self._new_metadata._djmix_ars

        for medium_node in self._release_node['media']:
            mm = Metadata()
            mm.copy(self._new_metadata)
            medium_to_metadata(medium_node, mm)
            fmt = medium_node.get('format')
            if fmt:
                all_media.append(fmt)

            for dj in djmix_ars.get(mm['discnumber'], []):
                mm.add('djmixer', dj)

            if va:
                mm['compilation'] = '1'
            else:
                del mm['compilation']

            if 'discs' in medium_node:
                discids = [disc.get('id') for disc in medium_node['discs']]
                mm['~musicbrainz_discids'] = discids
                mm['musicbrainz_discid'] = list(self._discids.intersection(discids))

            pregap_node = medium_node.get('pregap')
            if pregap_node:
                mm['~discpregap'] = '1'
                _load_track(pregap_node, mm, artists, {'~pregap': '1'})

            for track_node in medium_node.get('tracks', []):
                _load_track(track_node, mm, artists, {})

            for track_node in medium_node.get('data-tracks', []):
                _load_track(track_node, mm, artists, {'~datatrack': '1'})

        totalalbumtracks = absolutetracknumber
        self._new_metadata['~totalalbumtracks'] = totalalbumtracks
        # Generate a list of unique media, but keep order of first appearance
        self._new_metadata['media'] = " / ".join(list(OrderedDict.fromkeys(all_media)))

        multiartists = len(artists) > 1
        for track in self._new_tracks:
            track.metadata['~totalalbumtracks'] = totalalbumtracks
            if multiartists:
                track.metadata['~multiartist'] = '1'
        # Preserve release JSON for session export after load finished
        self._release_node_cache = self._release_node
        del self._release_node
        del self._release_artist_nodes
        self._tracks_loaded = True

    def _finalize_loading_album(self):
        with self.suspend_metadata_images_update:
            for track in self._new_tracks:
                track.orig_metadata.copy(track.metadata)
                track.metadata_images_changed.connect(self.update_metadata_images)

            # Prepare parser for user's script
            for script in iter_active_tagging_scripts():
                parser = ScriptParser()
                for track in self._new_tracks:
                    # Run tagger script for each track
                    try:
                        parser.eval(script.content, track.metadata)
                    except ScriptError:
                        log.exception("Failed to run tagger script %s on track", script.name)
                    track.metadata.strip_whitespace()
                    track.scripted_metadata.update(track.metadata)
                # Run tagger script for the album itself
                try:
                    parser.eval(script.content, self._new_metadata)
                except ScriptError:
                    log.exception("Failed to run tagger script %s on album", script.name)
                self._new_metadata.strip_whitespace()

            unmatched_files = [file for track in self.tracks for file in track.files]
            self.metadata = self._new_metadata
            self.orig_metadata.copy(self.metadata)
            self.orig_metadata.images.clear()
            self.tracks = self._new_tracks
            del self._new_metadata
            del self._new_tracks
            self.loaded = True
            self.status = AlbumStatus.LOADED
            self.match_files(unmatched_files + self.unmatched_files.files)
        self.update_metadata_images()
        self.update()

        # Trigger re-sort after album is fully loaded to ensure accurate match quality sorting
        # See the module: picard/ui/itemviews/match_quality_column.py
        # Without this, the sorting calcs never retrigger
        if self.ui_item:
            tree_widget = self.ui_item.treeWidget()
            if tree_widget and tree_widget.isSortingEnabled():
                # Clear cached sort keys for this item to force recalculation
                self.ui_item._sortkeys.clear()
                # Trigger re-sort by calling sortByColumn with current sort column
                current_sort_column = tree_widget.sortColumn()
                if current_sort_column >= 0:
                    tree_widget.sortByColumn(current_sort_column, tree_widget.header().sortIndicatorOrder())

        self.tagger.window.set_statusbar_message(
            N_('Album %(id)s loaded: %(artist)s - %(album)s'),
            {
                'id': self.id,
                'artist': self.metadata['albumartist'],
                'album': self.metadata['album'],
            },
            timeout=3000,
        )
        for func, _run_on_error in self._after_load_callbacks:
            func()
        self._after_load_callbacks = []
        if self.ui_item.isSelected():
            self.tagger.window.refresh_metadatabox()
            self.tagger.window.cover_art_box.update_metadata()

    def _finalize_loading(self, error):
        if self.loaded:
            # This is not supposed to happen, _finalize_loading should only
            # be called once after all requests finished.
            import inspect

            stack = inspect.stack()
            args = [self]
            msg = "Album._finalize_loading called for already loaded album %r"
            if len(stack) > 1:
                f = stack[1]
                msg += " at %s:%d in %s"
                args.extend((f.filename, f.lineno, f.function))
            log.warning(msg, *args)
            return

        # Check for and abort timed out requests
        self.check_timed_out_tasks()

        if error:
            self.metadata.clear()
            self.status = AlbumStatus.ERROR
            self.update()
            if not self.has_critical_tasks():
                del self._new_metadata
                del self._new_tracks
                self.loaded = True
                for func, run_on_error in self._after_load_callbacks:
                    if run_on_error:
                        func()
            return

        if self.has_critical_tasks():
            return

        if not self._tracks_loaded:
            self._load_tracks()

        if not self.has_critical_tasks():
            self._finalize_loading_album()

    def load(self, priority=False, refresh=False):
        if self.has_critical_tasks():
            log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message(
            N_("Loading album %(id)s …"),
            {'id': self.id},
        )
        self.loaded = False
        self.status = AlbumStatus.LOADING
        if self.release_group:
            self.release_group.loaded = False
            self.release_group.genres.clear()
        self.metadata.clear()
        self.genres.clear()
        self.update(update_selection=False)
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._pending_tasks.clear()
        self.add_task('release_metadata', TaskType.CRITICAL, f'Release metadata for {self.id}')
        self.clear_errors()
        config = get_config()
        require_authentication = False
        inc = {
            'aliases',
            'annotation',
            'artist-credits',
            'artists',
            'collections',
            'discids',
            'isrcs',
            'labels',
            'media',
            'recordings',
            'release-groups',
        }
        if self.tagger.webservice.oauth_manager.is_authorized():
            require_authentication = True
            inc |= {'user-collections'}
        if config.setting['release_ars'] or config.setting['track_ars']:
            inc |= {
                'artist-rels',
                'recording-rels',
                'release-group-level-rels',
                'release-rels',
                'series-rels',
                'url-rels',
                'work-rels',
            }
            if config.setting['track_ars']:
                inc |= {
                    'recording-level-rels',
                    'work-level-rels',
                }
        require_authentication = self.set_genre_inc_params(inc, config) or require_authentication
        if config.setting['enable_ratings']:
            require_authentication = True
            inc |= {'user-ratings'}

        def create_request():
            self.load_request = self.tagger.mb_api.get_release_by_id(
                self.id,
                self._release_request_finished,
                inc=inc,
                mblogin=require_authentication,
                priority=priority,
                refresh=refresh,
            )
            return self.load_request

        self.add_task(
            'release_metadata',
            TaskType.CRITICAL,
            'Release metadata',
            request_factory=create_request,
        )

    def run_when_loaded(self, func, run_on_error=False):
        if self.loaded:
            func()
        else:
            self._after_load_callbacks.append((func, run_on_error))

    def stop_loading(self):
        if self.load_request:
            self.tagger.webservice.remove_task(self.load_request)
            self.load_request = None

    def update(self, update_tracks=True, update_selection=True):
        if self.ui_item:
            self.ui_item.update(update_tracks, update_selection=update_selection)

    def add_file(self, track, file, new_album=True):
        self._files_count += 1
        if new_album:
            self.update(update_tracks=False)
            self.add_metadata_images_from_children([file])

    def remove_file(self, track, file, new_album=True):
        self._files_count -= 1
        if new_album:
            self.update(update_tracks=False)
            self.remove_metadata_images_from_children([file])

    @staticmethod
    def _match_files(files, tracks, unmatched_files, threshold=0):
        """Match files to tracks on this album, based on metadata similarity or recordingid."""
        SimMatchAlbum = namedtuple('SimMatchAlbum', 'similarity track')
        no_match = SimMatchAlbum(similarity=-1, track=unmatched_files)

        tracks_cache = TracksCache()

        for file in list(files):
            if file.state == File.REMOVED:
                continue

            # If we have a recordingid or trackid to match against, use that in priority
            # if recordingid and trackid do point to different tracks, compare the file
            # and track durations to find the better match.
            metadata = file.metadata
            recordingid = file.match_recordingid or metadata['musicbrainz_recordingid']
            trackid = metadata['musicbrainz_trackid']
            tracknumber = metadata['tracknumber']
            discnumber = metadata['discnumber']

            def mbid_candidates():
                if not tracks_cache:
                    tracks_cache.build(tracks)
                for mbid in (recordingid, trackid):
                    if mbid and mbid_validate(mbid):
                        track = tracks_cache.get_track(mbid, tracknumber, discnumber)
                        if track:
                            similarity = track.metadata.length_score(track.metadata.length, metadata.length)
                            yield SimMatchAlbum(similarity=similarity, track=track)

            best_match = find_best_match(mbid_candidates(), no_match)
            if best_match.result != no_match:
                yield (file, best_match.result.track)
                continue

            # try to match by similarity
            def similarity_candidates():
                for track in tracks:
                    similarity = track.metadata.compare(file.orig_metadata)
                    if similarity >= threshold:
                        yield SimMatchAlbum(similarity=similarity, track=track)

            best_match = find_best_match(similarity_candidates(), no_match)
            yield (file, best_match.result.track)

    def match_files(self, files):
        """Match and move files to tracks on this album, based on metadata similarity or recordingid."""
        if self.loaded:
            config = get_config()
            threshold = config.setting['track_matching_threshold']
            moves = self._match_files(files, self.tracks, self.unmatched_files, threshold=threshold)
            with self.tagger.window.metadata_box.ignore_updates:
                for file, target in moves:
                    file.move(target)
        else:
            with self.tagger.window.metadata_box.ignore_updates:
                for file in list(files):
                    file.move(self.unmatched_files)

    @property
    def can_save(self):
        return self._files_count > 0

    @property
    def can_remove(self):
        return True

    @property
    def can_edit_tags(self):
        return True

    @property
    def can_analyze(self):
        return False

    @property
    def can_autotag(self):
        return False

    @property
    def can_refresh(self):
        return True

    @property
    def can_view_info(self):
        return self.loaded or bool(self.errors)

    @property
    def is_album_like(self):
        return True

    def get_num_matched_tracks(self):
        return sum(1 for track in self.tracks if track.is_linked())

    def get_num_unmatched_files(self):
        return len(self.unmatched_files.files)

    def get_num_total_files(self):
        return self._files_count + len(self.unmatched_files.files)

    def is_complete(self):
        if not self.tracks:
            return False
        for track in self.tracks:
            if not track.is_complete():
                return False
        return not self.get_num_unmatched_files()

    def is_modified(self):
        return any(self._iter_unsaved_files())

    def get_num_unsaved_files(self):
        return sum(1 for file in self._iter_unsaved_files())

    def _iter_unsaved_files(self):
        yield from (file for file in self.iterfiles(save=True) if not file.is_saved())

    def column(self, column):
        if column == 'title':
            if self.status == AlbumStatus.LOADING:
                title = _("[loading album information]")
            elif self.status == AlbumStatus.ERROR:
                title = _("[could not load album %s]") % self.id
            else:
                title = self.metadata['album']

            if self.tracks:
                elems = ['%d/%d' % (self.get_num_matched_tracks(), len(self.tracks))]
                unmatched = self.get_num_unmatched_files()
                if unmatched:
                    elems.append('%d?' % (unmatched,))
                unsaved = self.get_num_unsaved_files()
                if unsaved:
                    elems.append('%d*' % (unsaved,))
                ca_detailed = self.cover_art_description_detailed()
                if ca_detailed:
                    elems.append(ca_detailed)

                return '%s\u200e (%s)' % (title, '; '.join(elems))
            else:
                return title
        elif column == '~length':
            length = self.metadata.length
            if length:
                return format_time(length)
            else:
                return ''
        elif column == 'artist':
            return self.metadata['albumartist']
        elif column == 'tracknumber':
            return self.metadata['~totalalbumtracks']
        elif column == 'discnumber':
            return self.metadata['totaldiscs']
        elif column == 'covercount':
            return self.cover_art_description()
        elif column == 'coverdimensions':
            return self.cover_art_dimensions()
        else:
            return self.metadata[column]

    def switch_release_version(self, mbid):
        if mbid == self.id:
            return
        for file in list(self.iterfiles(True)):
            file.move(self.unmatched_files)
        album = self.tagger.albums.get(mbid)
        if album:
            album.match_files(self.unmatched_files.files)
            album.update()
            self.tagger.remove_album(self)
        else:
            del self.tagger.albums[self.id]
            self.release_group.loaded_albums.discard(self.id)
            self.id = mbid
            self.tagger.albums[mbid] = self
            self.load(priority=True, refresh=True)

    def update_metadata_images(self):
        if self.suspend_metadata_images_update:
            return

        if self.update_metadata_images_from_children():
            self.update(update_tracks=False)
            self.metadata_images_changed.emit()

    def keep_original_images(self):
        with self.suspend_metadata_images_update:
            for track in self.tracks:
                track.keep_original_images()
            for file in list(self.unmatched_files.files):
                file.keep_original_images()

    def children_metadata_items(self):
        for track in self.tracks:
            yield track
            yield from track.files
        yield from self.unmatched_files.files


class NatAlbum(Album):
    def __init__(self):
        super().__init__('NATS')
        self.loaded = True
        self.update()

    def update(self, update_tracks=True, update_selection=True):
        config = get_config()
        old_album_title = self.metadata['album']
        self.metadata['album'] = config.setting['nat_name']
        with self.suspend_metadata_images_update:
            for track in self.tracks:
                if old_album_title == track.metadata['album']:
                    track.metadata['album'] = self.metadata['album']
                for file in track.files:
                    track.update_file_metadata(file)
        super().update(update_tracks=update_tracks, update_selection=update_selection)

    def _finalize_loading(self, error):
        self.update()

    @property
    def can_refresh(self):
        return False

    @property
    def can_browser_lookup(self):
        return False

    @property
    def can_view_info(self):
        return False


album_post_removal_processors = PluginFunctions(label='album_post_removal_processors')


def run_album_post_removal_processors(album_object):
    album_post_removal_processors.run(album_object)

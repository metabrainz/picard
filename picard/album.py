# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2009, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008 ojnkpjg
# Copyright (C) 2008-2011, 2014, 2018-2020 Philipp Wolfer
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2019 Michael Wiencek
# Copyright (C) 2012-2013, 2016-2017 Wieland Hoffmann
# Copyright (C) 2013, 2018 Calvin Walton
# Copyright (C) 2013-2015, 2017 Sophist-UK
# Copyright (C) 2013-2015, 2017-2019 Laurent Monin
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2019 Joel Lintunen
# Copyright (C) 2020 Gabriel Ferreira
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
import traceback

from PyQt5 import (
    QtCore,
    QtNetwork,
)

from picard import log
from picard.cluster import Cluster
from picard.collection import add_release_to_user_collections
from picard.config import get_config
from picard.const import VARIOUS_ARTISTS_ID
from picard.dataobj import DataObject
from picard.file import File
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
from picard.plugin import (
    PluginFunctions,
    PluginPriority,
)
from picard.script import (
    ScriptError,
    ScriptParser,
    enabled_tagger_scripts_texts,
)
from picard.track import Track
from picard.util import (
    find_best_match,
    format_time,
    mbid_validate,
    process_events_iter,
)
from picard.util.imagelist import (
    add_metadata_images,
    remove_metadata_images,
    update_metadata_images,
)
from picard.util.textencoding import asciipunct

from picard.ui.item import Item


def _create_artist_node_dict(source_node):
    return {x['artist']['id']: x['artist'] for x in source_node['artist-credit']}


def _copy_artist_nodes(source, target_node):
    for credit in target_node['artist-credit']:
        artist_node = source.get(credit['artist']['id'])
        if artist_node:
            credit['artist'] = artist_node


class AlbumArtist(DataObject):
    def __init__(self, album_artist_id):
        super().__init__(album_artist_id)


class Album(DataObject, Item):

    metadata_images_changed = QtCore.pyqtSignal()
    release_group_loaded = QtCore.pyqtSignal()

    def __init__(self, album_id, discid=None):
        DataObject.__init__(self, album_id)
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        self.tracks = []
        self.loaded = False
        self.load_task = None
        self.release_group = None
        self._files = 0
        self._requests = 0
        self._tracks_loaded = False
        self._discids = set()
        if discid:
            self._discids.add(discid)
        self._after_load_callbacks = []
        self.unmatched_files = Cluster(_("Unmatched Files"), special=True, related_album=self, hide_if_empty=True)
        self.unmatched_files.metadata_images_changed.connect(self.update_metadata_images)
        self.status = None
        self._album_artists = []
        self.update_metadata_images_enabled = True

    def __repr__(self):
        return '<Album %s %r>' % (self.id, self.metadata["album"])

    def iterfiles(self, save=False):
        for track in self.tracks:
            yield from track.iterfiles()
        if not save:
            yield from self.unmatched_files.iterfiles()

    def enable_update_metadata_images(self, enabled):
        self.update_metadata_images_enabled = enabled

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

    def _parse_release(self, release_node):
        log.debug("Loading release %r ...", self.id)
        self._tracks_loaded = False
        release_id = release_node['id']
        if release_id != self.id:
            self.tagger.mbid_redirects[self.id] = release_id
            album = self.tagger.albums.get(release_id)
            if album:
                log.debug("Release %r already loaded", release_id)
                album.match_files(self.unmatched_files.files)
                album.update()
                self.tagger.remove_album(self)
                return False
            else:
                del self.tagger.albums[self.id]
                self.tagger.albums[release_id] = self
                self.id = release_id

        # Make the release artist nodes available, since they may
        # contain supplementary data (aliases, tags, genres, ratings)
        # which aren't present in the release group, track, or
        # recording artist nodes. We can copy them into those places
        # wherever the IDs match, so that the data is shared and
        # available for use in mbjson.py and external plugins.
        self._release_artist_nodes = _create_artist_node_dict(release_node)

        # Get release metadata
        m = self._new_metadata
        m.length = 0

        rg_node = release_node['release-group']
        rg = self.release_group = self.tagger.get_release_group_by_id(rg_node['id'])
        rg.loaded_albums.add(self.id)
        rg.refcount += 1

        _copy_artist_nodes(self._release_artist_nodes, rg_node)
        release_group_to_metadata(rg_node, rg.metadata, rg)
        m.copy(rg.metadata)
        release_to_metadata(release_node, m, album=self)

        config = get_config()

        # Custom VA name
        if m['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
            m['albumartistsort'] = m['albumartist'] = config.setting['va_name']

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            m.apply_func(asciipunct)

        m['totaldiscs'] = len(release_node['media'])

        # Add album to collections
        add_release_to_user_collections(release_node)

        # Run album metadata plugins
        try:
            run_album_metadata_processors(self, m, release_node)
        except BaseException:
            self.error_append(traceback.format_exc())

        self._release_node = release_node
        return True

    def _release_request_finished(self, document, http, error):
        if self.load_task is None:
            return
        self.load_task = None
        parsed = False
        try:
            if error:
                self.error_append(http.errorString())
                # Fix for broken NAT releases
                if error == QtNetwork.QNetworkReply.ContentNotFoundError:
                    config = get_config()
                    nats = False
                    nat_name = config.setting["nat_name"]
                    files = list(self.unmatched_files.files)
                    for file in files:
                        recordingid = file.metadata["musicbrainz_recordingid"]
                        if mbid_validate(recordingid) and file.metadata["album"] == nat_name:
                            nats = True
                            self.tagger.move_file_to_nat(file, recordingid)
                            self.tagger.nats.update()
                    if nats and not self.get_num_unmatched_files():
                        self.tagger.remove_album(self)
                        error = False
            else:
                try:
                    parsed = self._parse_release(document)
                except Exception:
                    error = True
                    self.error_append(traceback.format_exc())
        finally:
            self._requests -= 1
            if parsed or error:
                self._finalize_loading(error)
        # does http need to be set to None to free the memory used by the network response?
        # http://qt-project.org/doc/qt-5/qnetworkaccessmanager.html says:
        #     After the request has finished, it is the responsibility of the user
        #     to delete the QNetworkReply object at an appropriate time.
        #     Do not directly delete it inside the slot connected to finished().
        #     You can use the deleteLater() function.

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.status = _("[could not load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
            if not self._requests:
                self.loaded = True
                for func, always in self._after_load_callbacks:
                    if always:
                        func()
            return

        if self._requests > 0:
            return

        if not self._tracks_loaded:
            artists = set()
            all_media = []
            absolutetracknumber = 0

            va = self._new_metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID

            djmix_ars = {}
            if hasattr(self._new_metadata, "_djmix_ars"):
                djmix_ars = self._new_metadata._djmix_ars

            for medium_node in self._release_node['media']:
                mm = Metadata()
                mm.copy(self._new_metadata)
                medium_to_metadata(medium_node, mm)
                format = medium_node.get('format')
                if format:
                    all_media.append(format)

                for dj in djmix_ars.get(mm["discnumber"], []):
                    mm.add("djmixer", dj)

                if va:
                    mm["compilation"] = "1"
                else:
                    del mm["compilation"]

                if 'discs' in medium_node:
                    discids = [disc.get('id') for disc in medium_node['discs']]
                    mm['~musicbrainz_discids'] = discids
                    mm['musicbrainz_discid'] = list(self._discids.intersection(discids))

                if "pregap" in medium_node:
                    absolutetracknumber += 1
                    mm['~discpregap'] = '1'
                    extra_metadata = {
                        '~pregap': '1',
                        '~absolutetracknumber': absolutetracknumber,
                    }
                    self._finalize_loading_track(medium_node['pregap'], mm, artists, extra_metadata)

                track_count = medium_node['track-count']
                if track_count:
                    tracklist_node = medium_node['tracks']
                    for track_node in tracklist_node:
                        absolutetracknumber += 1
                        extra_metadata = {
                            '~absolutetracknumber': absolutetracknumber,
                        }
                        self._finalize_loading_track(track_node, mm, artists, extra_metadata)

                if "data-tracks" in medium_node:
                    for track_node in medium_node['data-tracks']:
                        absolutetracknumber += 1
                        extra_metadata = {
                            '~datatrack': '1',
                            '~absolutetracknumber': absolutetracknumber,
                        }
                        self._finalize_loading_track(track_node, mm, artists, extra_metadata)

            totalalbumtracks = absolutetracknumber
            self._new_metadata['~totalalbumtracks'] = totalalbumtracks
            # Generate a list of unique media, but keep order of first appearance
            self._new_metadata['media'] = " / ".join(list(OrderedDict.fromkeys(all_media)))

            for track in self._new_tracks:
                track.metadata["~totalalbumtracks"] = totalalbumtracks
                if len(artists) > 1:
                    track.metadata["~multiartist"] = "1"
            del self._release_node
            del self._release_artist_nodes
            self._tracks_loaded = True

        if not self._requests:
            self.enable_update_metadata_images(False)
            for track in self._new_tracks:
                track.orig_metadata.copy(track.metadata)
                track.metadata_images_changed.connect(self.update_metadata_images)

            # Prepare parser for user's script
            for s_name, s_text in enabled_tagger_scripts_texts():
                parser = ScriptParser()
                for track in self._new_tracks:
                    # Run tagger script for each track
                    try:
                        parser.eval(s_text, track.metadata)
                    except ScriptError:
                        log.exception("Failed to run tagger script %s on track", s_name)
                    track.metadata.strip_whitespace()
                    track.scripted_metadata.update(track.metadata)
                # Run tagger script for the album itself
                try:
                    parser.eval(s_text, self._new_metadata)
                except ScriptError:
                    log.exception("Failed to run tagger script %s on album", s_name)
                self._new_metadata.strip_whitespace()

            unmatched_files = [file for track in self.tracks for file in track.files]
            self.metadata = self._new_metadata
            self.orig_metadata.copy(self.metadata)
            self.orig_metadata.images.clear()
            self.tracks = self._new_tracks
            del self._new_metadata
            del self._new_tracks
            self.loaded = True
            self.status = None
            self.match_files(unmatched_files + self.unmatched_files.files)
            self.enable_update_metadata_images(True)
            self.update()
            self.tagger.window.set_statusbar_message(
                N_('Album %(id)s loaded: %(artist)s - %(album)s'),
                {
                    'id': self.id,
                    'artist': self.metadata['albumartist'],
                    'album': self.metadata['album']
                },
                timeout=3000
            )
            for func, always in self._after_load_callbacks:
                func()
            self._after_load_callbacks = []
            if self.item.isSelected():
                self.tagger.window.refresh_metadatabox()

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
        artists.add(tm["artist"])
        if extra_metadata:
            tm.update(extra_metadata)

        # Run track metadata plugins
        try:
            run_track_metadata_processors(self, tm, track_node, self._release_node)
        except BaseException:
            self.error_append(traceback.format_exc())

        return track

    def load(self, priority=False, refresh=False):
        if self._requests:
            log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message(
            N_('Loading album %(id)s ...'),
            {'id': self.id}
        )
        self.loaded = False
        self.status = _("[loading album information]")
        if self.release_group:
            self.release_group.loaded = False
            self.release_group.genres.clear()
        self.metadata.clear()
        self.genres.clear()
        self.update(update_selection=False)
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._requests = 1
        self.clear_errors()
        config = get_config()
        require_authentication = False
        inc = ['release-groups', 'media', 'discids', 'recordings', 'artist-credits',
               'artists', 'aliases', 'labels', 'isrcs', 'collections', 'annotation']
        if self.tagger.webservice.oauth_manager.is_authorized():
            require_authentication = True
            inc += ['user-collections']
        if config.setting['release_ars'] or config.setting['track_ars']:
            inc += ['artist-rels', 'release-rels', 'url-rels', 'recording-rels', 'work-rels']
            if config.setting['track_ars']:
                inc += ['recording-level-rels', 'work-level-rels']
        require_authentication = self.set_genre_inc_params(inc) or require_authentication
        if config.setting['enable_ratings']:
            require_authentication = True
            inc += ['user-ratings']
        self.load_task = self.tagger.mb_api.get_release_by_id(
            self.id, self._release_request_finished, inc=inc,
            mblogin=require_authentication, priority=priority, refresh=refresh)

    def run_when_loaded(self, func, always=False):
        if self.loaded:
            func()
        else:
            self._after_load_callbacks.append((func, always))

    def stop_loading(self):
        if self.load_task:
            self.tagger.webservice.remove_task(self.load_task)
            self.load_task = None

    def update(self, update_tracks=True, update_selection=True):
        if self.item:
            self.item.update(update_tracks, update_selection=update_selection)

    def _add_file(self, track, file, new_album=True):
        self._files += 1
        if new_album:
            self.update(update_tracks=False)
            add_metadata_images(self, [file])

    def _remove_file(self, track, file, new_album=True):
        self._files -= 1
        if new_album:
            self.update(update_tracks=False)
            remove_metadata_images(self, [file])

    def _match_files(self, files, threshold=0):
        """Match files to tracks on this album, based on metadata similarity or recordingid."""
        tracks_cache = defaultdict(lambda: None)

        def build_tracks_cache():
            for track in self.tracks:
                tm_recordingid = track.orig_metadata['musicbrainz_recordingid']
                tm_tracknumber = track.orig_metadata['tracknumber']
                tm_discnumber = track.orig_metadata['discnumber']
                for tup in (
                    (tm_recordingid, tm_tracknumber, tm_discnumber),
                    (tm_recordingid, tm_tracknumber),
                    (tm_recordingid, )):
                    tracks_cache[tup] = track

        SimMatchAlbum = namedtuple('SimMatchAlbum', 'similarity track')

        for file in list(files):
            if file.state == File.REMOVED:
                continue
            # if we have a recordingid to match against, use that in priority
            recid = file.match_recordingid or file.metadata['musicbrainz_recordingid']
            if recid and mbid_validate(recid):
                if not tracks_cache:
                    build_tracks_cache()
                tracknumber = file.metadata['tracknumber']
                discnumber = file.metadata['discnumber']
                track = (tracks_cache[(recid, tracknumber, discnumber)]
                         or tracks_cache[(recid, tracknumber)]
                         or tracks_cache[(recid, )])
                if track:
                    yield (file, track)
                    continue

            # try to match by similarity
            def candidates():
                for track in process_events_iter(self.tracks):
                    yield SimMatchAlbum(
                        similarity=track.metadata.compare(file.orig_metadata),
                        track=track
                    )

            no_match = SimMatchAlbum(similarity=-1, track=self.unmatched_files)
            best_match = find_best_match(candidates, no_match)

            if best_match.similarity < threshold:
                yield (file, no_match.track)
            else:
                yield (file, best_match.result.track)

    def match_files(self, files):
        """Match and move files to tracks on this album, based on metadata similarity or recordingid."""
        if self.loaded:
            config = get_config()
            moves = self._match_files(files, threshold=config.setting['track_matching_threshold'])
            for file, target in moves:
                file.move(target)
        else:
            for file in list(files):
                file.move(self.unmatched_files)

    def can_save(self):
        return self._files > 0

    def can_remove(self):
        return True

    def can_edit_tags(self):
        return True

    def can_analyze(self):
        return False

    def can_autotag(self):
        return False

    def can_refresh(self):
        return True

    def can_view_info(self):
        return self.loaded or self.errors

    def is_album_like(self):
        return True

    def get_num_matched_tracks(self):
        num = 0
        for track in self.tracks:
            if track.is_linked():
                num += 1
        return num

    def get_num_unmatched_files(self):
        return len(self.unmatched_files.files)

    def get_num_total_files(self):
        return self._files + len(self.unmatched_files.files)

    def is_complete(self):
        if not self.tracks:
            return False
        for track in self.tracks:
            if not track.is_complete():
                return False
        if self.get_num_unmatched_files():
            return False
        else:
            return True

    def is_modified(self):
        if self.tracks:
            for track in self.tracks:
                for file in track.files:
                    if not file.is_saved():
                        return True
        return False

    def get_num_unsaved_files(self):
        count = 0
        for track in self.tracks:
            for file in track.files:
                if not file.is_saved():
                    count += 1
        return count

    def column(self, column):
        if column == 'title':
            if self.status is not None:
                title = self.status
            else:
                title = self.metadata['album']
            if self.tracks:
                linked_tracks = 0
                for track in self.tracks:
                    if track.is_linked():
                        linked_tracks += 1

                text = '%s\u200E (%d/%d' % (title, linked_tracks, len(self.tracks))
                unmatched = self.get_num_unmatched_files()
                if unmatched:
                    text += '; %d?' % (unmatched,)
                unsaved = self.get_num_unsaved_files()
                if unsaved:
                    text += '; %d*' % (unsaved,)
                # CoverArt.set_metadata uses the orig_metadata.images if metadata.images is empty
                # in order to show existing cover art if there's no cover art for a release. So
                # we do the same here in order to show the number of images consistently.
                if self.metadata.images:
                    metadata = self.metadata
                else:
                    metadata = self.orig_metadata

                number_of_images = len(metadata.images)
                if getattr(metadata, 'has_common_images', True):
                    text += ngettext("; %i image", "; %i images",
                                     number_of_images) % number_of_images
                else:
                    text += ngettext("; %i image not in all tracks", "; %i different images among tracks",
                                     number_of_images) % number_of_images
                return text + ')'
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
        if not self.update_metadata_images_enabled:
            return

        if update_metadata_images(self):
            self.update(False)
            self.metadata_images_changed.emit()

    def keep_original_images(self):
        self.enable_update_metadata_images(False)
        for track in self.tracks:
            track.keep_original_images()
        for file in list(self.unmatched_files.files):
            file.keep_original_images()
        self.enable_update_metadata_images(True)
        self.update_metadata_images()


class NatAlbum(Album):

    def __init__(self):
        super().__init__("NATS")
        self.loaded = True
        self.update()

    def update(self, update_tracks=True):
        config = get_config()
        self.enable_update_metadata_images(False)
        old_album_title = self.metadata["album"]
        self.metadata["album"] = config.setting["nat_name"]
        for track in self.tracks:
            if old_album_title == track.metadata["album"]:
                track.metadata["album"] = self.metadata["album"]
            for file in track.files:
                track.update_file_metadata(file)
        self.enable_update_metadata_images(True)
        super().update(update_tracks)

    def _finalize_loading(self, error):
        self.update()

    def can_refresh(self):
        return False

    def can_browser_lookup(self):
        return False


_album_post_removal_processors = PluginFunctions(label='album_post_removal_processors')


def register_album_post_removal_processor(function, priority=PluginPriority.NORMAL):
    """Registers an album-removed processor.
    Args:
        function: function to call after album removal, it will be passed the album object
        priority: optional, PluginPriority.NORMAL by default
    Returns:
        None
    """
    _album_post_removal_processors.register(function.__module__, function, priority)


def run_album_post_removal_processors(album_object):
    _album_post_removal_processors.run(album_object)

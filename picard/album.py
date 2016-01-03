# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006-2007 Lukáš Lalinský
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

import traceback
from PyQt4 import QtCore, QtNetwork
from picard import config, log
from picard.coverart import coverart
from picard.metadata import (Metadata,
                             register_album_metadata_processor,
                             run_album_metadata_processors,
                             run_track_metadata_processors)
from picard.dataobj import DataObject
from picard.file import File
from picard.track import Track
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import format_time, mbid_validate
from picard.util.textencoding import asciipunct
from picard.cluster import Cluster
from picard.collection import Collection, user_collections
from picard.mbxml import (
    release_group_to_metadata,
    release_to_metadata,
    medium_to_metadata,
    track_to_metadata,
)
from picard.const import VARIOUS_ARTISTS_ID

register_album_metadata_processor(coverart)


class AlbumArtist(DataObject):
    def __init__(self, id):
        DataObject.__init__(self, id)


class Album(DataObject, Item):

    release_group_loaded = QtCore.pyqtSignal()

    def __init__(self, id, discid=None):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.tracks = []
        self.loaded = False
        self.load_task = None
        self.release_group = None
        self._files = 0
        self._requests = 0
        self._tracks_loaded = False
        self._discid = discid
        self._after_load_callbacks = []
        self.unmatched_files = Cluster(_("Unmatched Files"), special=True, related_album=self, hide_if_empty=True)
        self.errors = []
        self.status = None
        self._album_artists = []

    def __repr__(self):
        return '<Album %s %r>' % (self.id, self.metadata[u"album"])

    def iterfiles(self, save=False):
        for track in self.tracks:
            for file in track.iterfiles():
                yield file
        if not save:
            for file in self.unmatched_files.iterfiles():
                yield file

    def append_album_artist(self, id):
        """Append artist id to the list of album artists
        and return an AlbumArtist instance"""
        album_artist = AlbumArtist(id)
        self._album_artists.append(album_artist)
        return album_artist

    def get_album_artists(self):
        """Returns the list of album artists (as AlbumArtist objects)"""
        return self._album_artists

    def _parse_release(self, document):
        log.debug("Loading release %r ...", self.id)
        self._tracks_loaded = False

        release_node = document.metadata[0].release[0]
        if release_node.id != self.id:
            self.tagger.mbid_redirects[self.id] = release_node.id
            album = self.tagger.albums.get(release_node.id)
            if album:
                log.debug("Release %r already loaded", release_node.id)
                album.match_files(self.unmatched_files.files)
                album.update()
                self.tagger.remove_album(self)
                return False
            else:
                del self.tagger.albums[self.id]
                self.tagger.albums[release_node.id] = self
                self.id = release_node.id

        # Get release metadata
        m = self._new_metadata
        m.length = 0

        rg_node = release_node.release_group[0]
        rg = self.release_group = self.tagger.get_release_group_by_id(rg_node.id)
        rg.loaded_albums.add(self.id)
        rg.refcount += 1

        release_group_to_metadata(rg_node, rg.metadata, rg)
        m.copy(rg.metadata)
        release_to_metadata(release_node, m, album=self)

        if self._discid:
            m['musicbrainz_discid'] = self._discid

        # Custom VA name
        if m['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
            m['albumartistsort'] = m['albumartist'] = config.setting['va_name']

        # Convert Unicode punctuation
        if config.setting['convert_punctuation']:
            m.apply_func(asciipunct)

        m['totaldiscs'] = release_node.medium_list[0].count

        # Add album to collections
        if "collection_list" in release_node.children:
            for node in release_node.collection_list[0].collection:
                if node.editor[0].text.lower() == config.persist["oauth_username"].lower():
                    if node.id not in user_collections:
                        user_collections[node.id] = \
                            Collection(node.id, node.name[0].text, node.release_list[0].count)
                    user_collections[node.id].releases.add(self.id)

        # Run album metadata plugins
        try:
            run_album_metadata_processors(self, m, release_node)
        except:
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
                self.error_append(unicode(http.errorString()))
                # Fix for broken NAT releases
                if error == QtNetwork.QNetworkReply.ContentNotFoundError:
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
                except:
                    error = True
                    self.error_append(traceback.format_exc())
        finally:
            self._requests -= 1
            if parsed or error:
                self._finalize_loading(error)
        # does http need to be set to None to free the memory used by the network response?
        # http://pyqt.sourceforge.net/Docs/PyQt4/qnetworkaccessmanager.html says:
        #     After the request has finished, it is the responsibility of the user
        #     to delete the QNetworkReply object at an appropriate time.
        #     Do not directly delete it inside the slot connected to finished().
        #     You can use the deleteLater() function.

    def error_append(self, msg):
        log.error(msg)
        self.errors.append(msg)

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.status = _("[could not load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
            return

        if self._requests > 0:
            return

        if not self._tracks_loaded:
            artists = set()
            totalalbumtracks = 0
            absolutetracknumber = 0
            va = self._new_metadata['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID

            djmix_ars = {}
            if hasattr(self._new_metadata, "_djmix_ars"):
                djmix_ars = self._new_metadata._djmix_ars

            for medium_node in self._release_node.medium_list[0].medium:
                mm = Metadata()
                mm.copy(self._new_metadata)
                medium_to_metadata(medium_node, mm)
                discpregap = False

                for dj in djmix_ars.get(mm["discnumber"], []):
                    mm.add("djmixer", dj)

                if "pregap" in medium_node.children:
                    discpregap = True
                    absolutetracknumber += 1
                    track = self._finalize_loading_track(medium_node.pregap[0], mm, artists, va, absolutetracknumber, discpregap)
                    track.metadata['~pregap'] = "1"

                for track_node in medium_node.track_list[0].track:
                    absolutetracknumber += 1
                    track = self._finalize_loading_track(track_node, mm, artists, va, absolutetracknumber, discpregap)

                if "data_track_list" in medium_node.children:
                    for track_node in medium_node.data_track_list[0].track:
                        absolutetracknumber += 1
                        track = self._finalize_loading_track(track_node, mm, artists, va, absolutetracknumber, discpregap)
                        track.metadata['~datatrack'] = "1"

            totalalbumtracks = str(absolutetracknumber)

            for track in self._new_tracks:
                track.metadata["~totalalbumtracks"] = totalalbumtracks
                if len(artists) > 1:
                    track.metadata["~multiartist"] = "1"
            del self._release_node
            self._tracks_loaded = True

        if not self._requests:
            # Prepare parser for user's script
            if config.setting["enable_tagger_script"]:
                script = config.setting["tagger_script"]
                if script:
                    parser = ScriptParser()
                    for track in self._new_tracks:
                        # Run tagger script for each track
                        try:
                            parser.eval(script, track.metadata)
                        except:
                            self.error_append(traceback.format_exc())
                        # Strip leading/trailing whitespace
                        track.metadata.strip_whitespace()
                    # Run tagger script for the album itself
                    try:
                        parser.eval(script, self._new_metadata)
                    except:
                        self.error_append(traceback.format_exc())
                    self._new_metadata.strip_whitespace()

            for track in self.tracks:
                for file in list(track.linked_files):
                    file.move(self.unmatched_files)
            self.metadata = self._new_metadata
            self.tracks = self._new_tracks
            del self._new_metadata
            del self._new_tracks
            self.loaded = True
            self.status = None
            self.match_files(self.unmatched_files.files)
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
            for func in self._after_load_callbacks:
                func()
            self._after_load_callbacks = []

    def _finalize_loading_track(self, track_node, metadata, artists, va, absolutetracknumber, discpregap):
        track = Track(track_node.recording[0].id, self)
        self._new_tracks.append(track)

        # Get track metadata
        tm = track.metadata
        tm.copy(metadata)
        track_to_metadata(track_node, track)
        track.metadata["~absolutetracknumber"] = absolutetracknumber
        track._customize_metadata()

        self._new_metadata.length += tm.length
        artists.add(tm["artist"])
        if va:
            tm["compilation"] = "1"
        if discpregap:
            tm["~discpregap"] = "1"

        # Run track metadata plugins
        try:
            run_track_metadata_processors(self, tm, self._release_node, track_node)
        except:
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
            self.release_group.folksonomy_tags.clear()
        self.metadata.clear()
        self.folksonomy_tags.clear()
        self.update()
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._requests = 1
        self.errors = []
        require_authentication = False
        inc = ['release-groups', 'media', 'recordings', 'artist-credits',
               'artists', 'aliases', 'labels', 'isrcs', 'collections']
        if config.setting['release_ars'] or config.setting['track_ars']:
            inc += ['artist-rels', 'release-rels', 'url-rels', 'recording-rels', 'work-rels']
            if config.setting['track_ars']:
                inc += ['recording-level-rels', 'work-level-rels']
        if config.setting['folksonomy_tags']:
            if config.setting['only_my_tags']:
                require_authentication = True
                inc += ['user-tags']
            else:
                inc += ['tags']
        if config.setting['enable_ratings']:
            require_authentication = True
            inc += ['user-ratings']
        self.load_task = self.tagger.xmlws.get_release_by_id(
            self.id, self._release_request_finished, inc=inc,
            mblogin=require_authentication, priority=priority, refresh=refresh)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self._after_load_callbacks.append(func)

    def stop_loading(self):
        if self.load_task:
            self.tagger.xmlws.remove_task(self.load_task)
            self.load_task = None

    def update(self, update_tracks=True):
        if self.item:
            self.item.update(update_tracks)

    def _add_file(self, track, file):
        self._files += 1
        self.update(update_tracks=False)

    def _remove_file(self, track, file):
        self._files -= 1
        self.update(update_tracks=False)

    def match_files(self, files, use_recordingid=True):
        """Match files to tracks on this album, based on metadata similarity or recordingid."""
        for file in list(files):
            if file.state == File.REMOVED:
                continue
            matches = []
            recordingid = file.metadata['musicbrainz_recordingid']
            if use_recordingid and mbid_validate(recordingid):
                matches = self._get_recordingid_matches(file, recordingid)
            if not matches:
                for track in self.tracks:
                    sim = track.metadata.compare(file.orig_metadata)
                    if sim >= config.setting['track_matching_threshold']:
                        matches.append((sim, track))
            if matches:
                matches.sort(reverse=True)
                file.move(matches[0][1])
            else:
                file.move(self.unmatched_files)

    def match_file(self, file, recordingid=None):
        """Match the file on a track on this album, based on recordingid or metadata similarity."""
        if file.state == File.REMOVED:
            return
        if recordingid is not None:
            matches = self._get_recordingid_matches(file, recordingid)
            if matches:
                matches.sort(reverse=True)
                file.move(matches[0][1])
                return
        self.match_files([file], use_recordingid=False)

    def _get_recordingid_matches(self, file, recordingid):
        matches = []
        tracknumber = file.metadata['tracknumber']
        discnumber = file.metadata['discnumber']
        for track in self.tracks:
            tm = track.metadata
            if recordingid == tm['musicbrainz_recordingid']:
                if tracknumber == tm['tracknumber']:
                    if discnumber == tm['discnumber']:
                        matches.append((4.0, track))
                        break
                    else:
                        matches.append((3.0, track))
                else:
                    matches.append((2.0, track))
        return matches

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
        return (self.loaded and self.metadata and self.metadata.images) or self.errors

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
        else:
            return True

    def is_modified(self):
        if self.tracks:
            for track in self.tracks:
                for file in track.linked_files:
                    if not file.is_saved():
                        return True
        return False

    def get_num_unsaved_files(self):
        count = 0
        for track in self.tracks:
            for file in track.linked_files:
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

                text = u'%s\u200E (%d/%d' % (title, linked_tracks, len(self.tracks))
                unmatched = self.get_num_unmatched_files()
                if unmatched:
                    text += '; %d?' % (unmatched,)
                unsaved = self.get_num_unsaved_files()
                if unsaved:
                    text += '; %d*' % (unsaved,)
                text += ungettext("; %i image", "; %i images",
                                  len(self.metadata.images)) % len(self.metadata.images)
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
        else:
            return ''

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


class NatAlbum(Album):

    def __init__(self):
        Album.__init__(self, id="NATS")
        self.loaded = True
        self.update()

    def update(self, update_tracks=True):
        self.metadata["album"] = config.setting["nat_name"]
        for track in self.tracks:
            track.metadata["album"] = self.metadata["album"]
            for file in track.linked_files:
                track.update_file_metadata(file)
        Album.update(self, update_tracks)

    def _finalize_loading(self, error):
        self.update()

    def can_refresh(self):
        return False

    def can_browser_lookup(self):
        return False

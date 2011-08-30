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
from collections import deque
from PyQt4 import QtCore
from picard.medium import Medium
from picard.metadata import Metadata, run_album_metadata_processors
from picard.dataobj import DataObject
from picard.file import File
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import format_time, partial, translate_artist, queue, mbid_validate
from picard.cluster import AlbumCluster, UnmatchedCluster
from picard.mbxml import release_to_metadata, media_formats_from_node, label_info_from_node
from picard.const import VARIOUS_ARTISTS_ID


class Album(DataObject, Item):

    release_group_loaded = QtCore.pyqtSignal()

    def __init__(self, id, discid=None):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.mediums = []
        self.tracks = []
        self.unmatched_files = UnmatchedCluster(album=self)
        self._discid = discid
        self._files = 0

        self.group_loaded = False
        self.group_id = None
        self.other_versions = []

        self.loaded = False
        self.load_task = None
        self._tracks_loaded = False
        self._requests = 0
        self._after_load_callbacks = queue.Queue()

        self.item = None
        self.format_str = None

    def __repr__(self):
        return '<Album %s %r>' % (self.id, self.metadata[u"album"])

    def iterfiles(self, save=False):
        for track in self.tracks:
            for file in track.iterfiles():
                yield file
        if not save:
            for file in self.unmatched_files.iterfiles():
                yield file

    def _parse_release(self, document):
        self.log.debug("Loading release %r", self.id)
        self._tracks_loaded = False

        release_node = document.metadata[0].release[0]
        if release_node.id != self.id:

            self.tagger.mbid_redirects[self.id] = release_node.id
            album = self.tagger.albums.get(release_node.id)

            if album:
                self.log.debug("Release %r already loaded", release_node.id)
                album.match_files(self.unmatched_files.files)
                album.update()
                self.remove()
                self.tagger.album_removed.emit(self)
                return False
            else:
                del self.tagger.albums[self.id]
                self.tagger.albums[release_node.id] = self
                self.id = release_node.id

        # Get release metadata
        m = self._new_metadata
        m.length = 0
        release_to_metadata(release_node, m, config=self.config, album=self)

        self.format_str = media_formats_from_node(release_node.medium_list[0])
        self.group_id = release_node.release_group[0].id

        if self._discid:
            m['musicbrainz_discid'] = self._discid

        # 'Translate' artist name
        if self.config.setting['translate_artist_names']:
            m['albumartist'] = translate_artist(m['albumartist'], m['albumartistsort'])

        # Custom VA name
        if m['musicbrainz_albumartistid'] == VARIOUS_ARTISTS_ID:
            m['albumartistsort'] = m['albumartist'] = self.config.setting['va_name']

        m["totaldiscs"] = release_node.medium_list[0].count

        # Run album metadata plugins
        try:
            run_album_metadata_processors(self, m, release_node)
        except:
            self.log.error(traceback.format_exc())

        self._release_node = release_node
        return True

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.metadata["album"] = _("[could not load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
            return

        if self._requests > 0:
            return

        if not self._tracks_loaded:
            self.artists = set()
            totalalbumtracks = 0

            for medium_node in self._release_node.medium_list[0].medium:
                medium = Medium(self, self._release_node, medium_node)
                totalalbumtracks += int(medium.metadata["totaltracks"])
                self.mediums.append(medium)

            totalalbumtracks = str(totalalbumtracks)

            for track in (t for med in self.mediums for t in med.tracks):
                tm = track.metadata
                if len(self.artists) > 1:
                    tm["compilation"] = "1"
                tm["~totalalbumtracks"] = totalalbumtracks

            del self.artists
            del self._release_node
            self._tracks_loaded = True

        if not self._requests:
            # Prepare parser for user's script
            if self.config.setting["enable_tagger_script"]:
                script = self.config.setting["tagger_script"]

                if script:
                    parser = ScriptParser()
                    for track in self._new_tracks:
                        # Run tagger script for each track
                        try:
                            parser.eval(script, track.metadata)
                        except:
                            self.log.error(traceback.format_exc())
                        # Strip leading/trailing whitespace
                        track.metadata.strip_whitespace()

                    # Run tagger script for the album itself
                    try:
                        parser.eval(script, self._new_metadata)
                    except:
                        self.log.error(traceback.format_exc())
                    self._new_metadata.strip_whitespace()

            for file in self.iterfiles(save=True):
                file.move(self.unmatched_files)

            self.metadata = self._new_metadata
            self.tracks = self._new_tracks
            del self._new_metadata
            del self._new_tracks

            self.loaded = True
            self.update()
            self.match_files(self.unmatched_files.files)
            self.tagger.window.set_statusbar_message("Album %s loaded", self.id, timeout=3000)

            while self._after_load_callbacks.qsize() > 0:
                func = self._after_load_callbacks.get()
                func()

    def _release_request_finished(self, document, reply, error):
        if self.load_task is None:
            return
        self.load_task = None
        parsed = False

        if error:
            self.log.error("%r", unicode(reply.errorString()))

            # Fix for broken NAT releases
            for file in list(self.unmatched_files.files):
                m = file.metadata
                trackid = m["musicbrainz_trackid"]
                if mbid_validate(trackid) and m["album"] == self.config.setting["nat_name"]:
                    self.tagger.move_file_to_nat(file, trackid)
                    self.tagger.nats.update()

            if not self.get_num_unmatched_files():
                self.tagger.remove_album(self)
        else:
            try:
                parsed = self._parse_release(document)
            except:
                self.log.error(traceback.format_exc())
                error = True

        self._requests -= 1
        if parsed or error:
            self._finalize_loading(error)

    def _parse_release_group(self, document):
        for node in document.metadata[0].release_list[0].release:
            v = {}
            v["mbid"] = node.id
            v["date"] = node.date[0].text if "date" in node.children else ""
            v["country"] = node.country[0].text if "country" in node.children else ""
            labels, catnums = label_info_from_node(node.label_info_list[0])
            v["labels"] = ", ".join(set(labels))
            v["catnums"] = ", ".join(set(catnums))
            v["tracks"] = " + ".join([m.track_list[0].count for m in node.medium_list[0].medium])
            v["format"] = media_formats_from_node(node.medium_list[0])
            self.other_versions.append(v)
        self.other_versions.sort(key=lambda x: x["date"])

    def _release_group_request_finished(self, document, http, error):
        if error:
            self.log.error("%r", unicode(http.errorString()))
            return
        try:
            self._parse_release_group(document)
            self.group_loaded = True
            self.release_group_loaded.emit()
        except:
            self.log.error(traceback.format_exc())

    def load(self):
        if self._requests:
            self.log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message('Loading album %s...', self.id)
        self.loaded = False
        self.mediums = []
        self.metadata.clear()
        self.metadata['album'] = _("[loading album information]")
        self.update(update_tracks=False)
        self._new_metadata = Metadata()
        self._new_tracks = []
        self._requests = 1
        require_authentication = False
        inc = ['release-groups', 'media', 'recordings', 'puids', 'artist-credits', 'labels', 'isrcs']
        if self.config.setting['release_ars'] or self.config.setting['track_ars']:
            inc += ['artist-rels', 'release-rels', 'url-rels', 'recording-rels', 'work-rels']
            if self.config.setting['track_ars']:
                inc += ['recording-level-rels', 'work-level-rels']
        if self.config.setting['folksonomy_tags']:
            if self.config.setting['only_my_tags']:
                require_authentication = True
                inc += ['user-tags']
            else:
                inc += ['tags']
        if self.config.setting['enable_ratings']:
            require_authentication = True
            inc += ['user-ratings']
        self.load_task = self.tagger.xmlws.get_release_by_id(
            self.id, self._release_request_finished, inc=inc,
            mblogin=require_authentication)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self._after_load_callbacks.put(func)

    def update(self, update_tracks=True):
        self.tagger.album_updated.emit(self, update_tracks)

    def remove(self):
        self.log.debug("Removing %r", self)
        if self.load_task:
            self.tagger.xmlws.remove_task(self.load_task)
            self.load_task = None
        for file in self.iterfiles():
            file.remove()
        del self.tagger.albums[self.id]
        if self == self.tagger.nats:
            self.tagger.nats = None

    def match_files(self, files, use_trackid=True):
        """Match files to tracks on this album, based on metadata similarity or trackid."""
        for file in list(files):
            matches = []
            trackid = file.metadata['musicbrainz_trackid']
            if use_trackid and mbid_validate(trackid):
                matches = self._get_trackid_matches(file, trackid)
            if not matches:
                for track in self.tracks:
                    sim = track.metadata.compare(file.orig_metadata)
                    if sim >= self.config.setting['track_matching_threshold']:
                        matches.append((sim, track))
            if matches:
                matches.sort(reverse=True)
                file.move(matches[0][1])
            else:
                if file.parent != self.unmatched_files:
                    file.move(self.unmatched_files)

    def match_file(self, file, trackid=None):
        """Match the file on a track on this album, based on trackid or metadata similarity."""
        if trackid is not None:
            matches = self._get_trackid_matches(file, trackid)
            if matches:
                matches.sort(reverse=True)
                file.move(matches[0][1])
                return
        self.match_files([file], use_trackid=False)

    def _get_trackid_matches(self, file, trackid):
        matches = []
        tracknumber = file.metadata['tracknumber']
        discnumber = file.metadata['discnumber']
        for track in self.tracks:
            tm = track.metadata
            if trackid == tm['musicbrainz_trackid']:
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
        return False

    def can_analyze(self):
        return False

    def can_autotag(self):
        return False

    def can_refresh(self):
        return True

    def get_num_matched_tracks(self):
        num = 0
        for track in self.tracks:
            if track.is_linked():
                num += 1
        return num

    def get_num_unmatched_files(self):
        return len(self.unmatched_files.files)

    def is_complete(self):
        if not self.tracks:
            return False
        for track in self.tracks:
            if len(track.linked_files) != 1:
                return False
        else:
            return True

    def get_num_unsaved_files(self):
        count = 0
        for track in self.tracks:
            for file in track.linked_files:
                if not file.is_saved():
                    count += 1
        return count

    def column(self, column):
        if column == 'title':
            if self.tracks:
                linked_tracks = 0
                for track in self.tracks:
                    if track.is_linked():
                        linked_tracks += 1
                text = u'%s\u200E (%d/%d' % (self.metadata['album'], linked_tracks, len(self.tracks))
                unmatched = self.get_num_unmatched_files()
                if unmatched:
                    text += '; %d?' % (unmatched,)
                unsaved = self.get_num_unsaved_files()
                if unsaved:
                    text += '; %d*' % (unsaved,)
                return text + ')'
            else:
                return self.metadata['album']
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
        for file in self.iterfiles(True):
            file.move(self.unmatched_files)
        album = self.tagger.albums.get(mbid)
        if album:
            album.match_files(self.unmatched_files.files)
            album.update()
            self.remove()
            self.tagger.album_removed.emit(self)
        else:
            del self.tagger.albums[self.id]
            self.id = mbid
            self.tagger.albums[mbid] = self
            self.load()


class NatAlbum(Album):

    def __init__(self):
        super(NatAlbum, self).__init__(id="NATS")
        self.loaded = True
        self.update()

    def update(self, update_tracks=True):
        self.metadata["album"] = self.config.setting["nat_name"]
        for track in self.tracks:
            track.metadata["album"] = self.metadata["album"]
            for file in track.linked_files:
                track.update_file(file)
        super(NatAlbum, self).update(update_tracks)

    def _finalize_loading(self, error):
        self.update()

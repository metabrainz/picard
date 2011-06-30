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
from PyQt4 import QtCore
from picard.metadata import Metadata, run_album_metadata_processors
from picard.dataobj import DataObject
from picard.file import File
from picard.track import Track
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import format_time, partial, translate_artist, queue, mbid_validate
from picard.cluster import Cluster
from picard.mbxml import release_to_metadata, track_to_metadata
from picard.const import RELEASE_FORMATS, VARIOUS_ARTISTS_ID


class Album(DataObject, Item):

    def __init__(self, id, discid=None):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.tracks = []
        self.loaded = False
        self.rgloaded = False
        self._files = 0
        self._requests = 0
        self._discid = discid
        self._after_load_callbacks = queue.Queue()
        self.other_versions = []
        self.unmatched_files = Cluster(_("Unmatched Files"), special=True, related_album=self, hide_if_empty=True)

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

        release_node = document.metadata[0].release[0]
        if release_node.id != self.id:
            album = self.tagger.get_album_by_id(release_node.id)
            self.tagger.albumids[self.id] = release_node.id
            self.id = release_node.id
            if album:
                album.match_files(self.unmatched_files.files)
                album.update()
                self.tagger.remove_album(self)
                self.log.debug("Release %r already loaded", self.id)
                return False

        # Get release metadata
        m = self._new_metadata
        m.length = 0
        release_to_metadata(release_node, m, config=self.config, album=self)

        if self._discid:
            m['musicbrainz_discid'] = self._discid

        if not self.rgloaded:
            releasegroupid = release_node.release_group[0].id
            self.tagger.xmlws.get_release_group_by_id(releasegroupid, self._release_group_request_finished)

        # 'Translate' artist name
        if self.config.setting['translate_artist_names']:
            m['albumartist'] = m['artist'] = translate_artist(m['artist'], m['artistsort'])

        # Custom VA name
        if m['musicbrainz_artistid'] == VARIOUS_ARTISTS_ID:
            m['albumartistsort'] = m['artistsort'] = m['albumartist'] = m['artist'] = self.config.setting['va_name']

        # Album metadata plugins
        try:
            run_album_metadata_processors(self, m, release_node)
        except:
            self.log.error(traceback.format_exc())

        # Prepare parser for user's script
        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = parser = None

        # Strip leading/trailing whitespace
        m.strip_whitespace()

        ignore_tags = [s.strip() for s in self.config.setting['ignore_tags'].split(',')]
        artists = set()

        m['totaldiscs'] = release_node.medium_list[0].count

        for medium in release_node.medium_list[0].medium:
            discnumber = medium.position[0].text
            track_list = medium.track_list[0]
            totaltracks = track_list.count
            discsubtitle = medium.title[0].text if "title" in medium.children else ""
            format = medium.format[0].text if "format" in medium.children else ""

            for node in track_list.track:
                t = Track(node.recording[0].id, self)
                self._new_tracks.append(t)

                # Get track metadata
                tm = t.metadata
                tm.copy(m)
                tm['discnumber'] = discnumber
                tm['discsubtitle'] = discsubtitle
                tm['totaltracks'] = totaltracks
                if format: tm['format'] = format

                track_to_metadata(node, config=self.config, track=t)
                t._customize_metadata(node, release_node, script, parser, ignore_tags)

                artists.add(tm['musicbrainz_artistid'])
                m.length += tm.length

        if len(artists) > 1:
            for t in self._new_tracks:
                t.metadata['compilation'] = '1'

        if script:
            # Run tagger script for the album itself
            try:
                parser.eval(script, m)
            except:
                self.log.error(traceback.format_exc())

        return True

    def _parse_release_group(self, document):
        releases = document.metadata[0].release_group[0].release_list[0].release
        for release in releases:
            version = {}
            version["mbid"] = release.id
            if "date" in release.children:
                version["date"] = release.date[0].text
            if "country" in release.children:
                version["country"] = release.country[0].text
            version["totaltracks"] = [int(m.track_list[0].count) for m in release.medium_list[0].medium]
            formats = {}
            for medium in release.medium_list[0].medium:
                if "format" in medium.children:
                    f = medium.format[0].text
                    if f in formats: formats[f] += 1
                    else: formats[f] = 1
            if formats:
                version["format"] = " + ".join(["%s%s" % (str(j)+u"×" if j>1 else "", RELEASE_FORMATS[i])
                    for i, j in formats.items()])
            self.other_versions.append(version)
        self.other_versions.sort(key=lambda x: x["date"])

    def _release_request_finished(self, document, http, error):
        parsed = False
        try:
            if error:
                self.log.error("%r", unicode(http.errorString()))
                # Fix for broken NAT releases
                files = list(self.unmatched_files.files)
                for file in files:
                    trackid = file.metadata["musicbrainz_trackid"]
                    if mbid_validate(trackid) and file.metadata["album"] == self.config.setting["nat_name"]:
                        self.tagger.move_file_to_nat(file, trackid)
                        self.tagger.nats.update()
                if not self.get_num_unmatched_files():
                    self.tagger.remove_album(self)
                    error = False
            else:
                try:
                    parsed = self._parse_release(document)
                except:
                    error = True
                    self.log.error(traceback.format_exc())
        finally:
            self._requests -= 1
            if parsed or error:
                self._finalize_loading(error)

    def _release_group_request_finished(self, document, http, error):
        try:
            if error:
                self.log.error("%r", unicode(http.errorString()))
            else:
                try:
                    self._parse_release_group(document)
                except:
                    error = True
                    self.log.error(traceback.format_exc())
        finally:
            self.rgloaded = True

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.metadata['album'] = _("[could not load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
        else:
            if not self._requests:
                for track in self.tracks:
                    for file in list(track.linked_files):
                        file.move(self.unmatched_files)
                self.metadata = self._new_metadata
                self.tracks = self._new_tracks
                del self._new_metadata
                del self._new_tracks
                self.loaded = True
                self.match_files(self.unmatched_files.files)
                self.update()
                self.tagger.window.set_statusbar_message('Album %s loaded', self.id, timeout=3000)
                while self._after_load_callbacks.qsize() > 0:
                    func = self._after_load_callbacks.get()
                    func()

    def load(self):
        if self._requests:
            self.log.info("Not reloading, some requests are still active.")
            return
        self.tagger.window.set_statusbar_message('Loading album %s...', self.id)
        self.loaded = False
        self.metadata.clear()
        self.metadata['album'] = _("[loading album information]")
        self.update()
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
        self.tagger.xmlws.get_release_by_id(self.id, self._release_request_finished, inc=inc,
                mblogin=require_authentication)

    def run_when_loaded(self, func):
        if self.loaded:
            func()
        else:
            self._after_load_callbacks.put(func)

    def update(self, update_tracks=True):
        self.tagger.emit(QtCore.SIGNAL("album_updated"), self, update_tracks)

    def _add_file(self, track, file):
        self._files += 1
        self.update(False)

    def _remove_file(self, track, file):
        self._files -= 1
        self.update(False)

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
                    count+=1
        return count

    def column(self, column):
        if column == 'title':
            if self.tracks:
                linked_tracks = 0
                for track in self.tracks:
                    if track.is_linked():
                        linked_tracks+=1
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

    def switch_release_version(self, version):
        self.id = version["mbid"]
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
                track.update_file_metadata(file)
        super(NatAlbum, self).update(update_tracks)

    def _finalize_loading(self, error):
        self.update()

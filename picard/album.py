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
from musicbrainz2.model import Relation
from musicbrainz2.utils import extractUuid, extractFragment
from musicbrainz2.webservice import Query, WebServiceError, ReleaseIncludes, TrackIncludes
from picard.metadata import Metadata, run_album_metadata_processors, run_track_metadata_processors
from picard.dataobj import DataObject
from picard.track import Track
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import format_time
from picard.cluster import Cluster
from picard.mbxml import release_to_metadata, track_to_metadata


class Album(DataObject, Item):

    def __init__(self, id):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        self.unmatched_files = Cluster(_("Unmatched Files"), special=2)
        self.tracks = []
        self.loaded = False
        self._files = 0
        self._requests = 0

    def __str__(self):
        return '<Album %s %r>' % (self.id, self.metadata[u"album"])

    def _parse_release(self, document):
        """Make album object from a parsed XML document."""
        m = self._new_metadata

        release_node = document.metadata[0].release[0]
        release_to_metadata(release_node, m)
        run_album_metadata_processors(self, m, release_node)

        for i, node in enumerate(release_node.track_list[0].track):
            t = Track(node.attribs['id'], self)
            self._new_tracks.append(t)
            tm = t.metadata
            tm.copy(m)
            track_to_metadata(node, tm)
            tm['tracknumber'] = str(i + 1)
            run_track_metadata_processors(self, m, release_node, node)

    def _release_request_finished(self, document, http, error):
        try:
            if error:
                self.log.error(unicode(http.errorString()))
            else:
                try:
                    self._parse_release(document)
                except:
                    error = True
                    self.log.error(traceback.format_exc())
        finally:
            self._requests -= 1
            self._finalize_loading(error)

    def _finalize_loading(self, error):
        if error:
            self.metadata.clear()
            self.metadata['album'] = _("[couldn't load album %s]") % self.id
            del self._new_metadata
            del self._new_tracks
            self.update()
        else:
            if not self._requests:
                for old_track, new_track in zip(self.tracks, self._new_tracks):
                    if old_track.linked_file:
                        new_track.linked_file = old_track.linked_file
                        new_track.linked_file.parent = new_track
                        new_track.linked_file.update(signal=False)
                for track in self.tracks[len(self._new_tracks):]:
                    if track.linked_file:
                        track.linked_file.move(self.unmatched_files)
                self.metadata = self._new_metadata
                self.tracks = self._new_tracks
                del self._new_metadata
                del self._new_tracks
                self.loaded = True
                self.update()
                self.tagger.window.set_statusbar_message('Album %s loaded', self.id, timeout=3000)
                self.match_files(self.unmatched_files.files)

    def load(self, force=False):
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
        self.tagger.xmlws.get_release_by_id(self.id, self._release_request_finished, inc=('tracks', 'artist', 'artist-rels', 'release-events'))

    def update(self, update_tracks=True):
        self.tagger.emit(QtCore.SIGNAL("album_updated"), self, update_tracks)

    def load_(self, force=False):
        self.tagger.window.set_statusbar_message('Loading release %s...', self.id)

        ws = self.tagger.get_web_service(cached=not force)
        query = Query(ws=ws)
        release = None
        try:
            inc = {'artist': True, 'releaseEvents': True, 'discs': True, 'tracks': True}
            if self.config.setting['release_ars']:
                inc['artistRelations'] = True
                inc['urlRelations'] = True
            release = query.getReleaseById(self.id, ReleaseIncludes(**inc))
        except WebServiceError, e:
            self.hasLoadError = True
            raise AlbumLoadError, e

        self.metadata.clear()
        self.metadata.from_release(release)
        self.metadata.from_relations(release.getRelations())

        if self.metadata["asin"] and self.config.setting["use_amazon_images"]:
            fileobj = ws.get_from_url(_AMAZON_IMAGE_URL % release.asin)
            data = fileobj.read()
            fileobj.close()
            if len(data) > 1000:
                self.metadata.add("~artwork", ("image/jpeg", data))

        run_album_metadata_processors(self.tagger, self.metadata, release)

        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
            parser = ScriptParser()
        else:
            script = None

        self.lock_for_write()
        self.tracks = []
        self.unlock()

        totaltracks = len(release.tracks)
        tracknum = 1
        duration = 0
        for track in release.tracks:
            if self.tagger.stopping:
                break
            self.tagger.window.set_statusbar_message('Loading release %s (track %d/%d)...', self.id, tracknum, totaltracks)
            tr = Track(extractUuid(track.id), self)
            tr.duration = track.duration or 0
            tr.metadata.copy(self.metadata)
            tr.metadata.from_track(track, release)
            # Load track relations
            if self.config.setting['track_ars']:
                try:
                    inc = TrackIncludes(artistRelations=True, urlRelations=True)
                    track = query.getTrackById(track.id, inc)
                except WebServiceError, e:
                    self.hasLoadError = True
                    raise AlbumLoadError, e
                tr.metadata.from_relations(track.getRelations())
            # Post-process the metadata
            run_track_metadata_processors(self.tagger, tr.metadata, release, track)
            if script:
                parser.eval(script, tr.metadata)
            self.lock_for_write()
            self.tracks.append(tr)
            self.unlock()
            duration += tr.duration
            tracknum += 1

        self.tagger.window.set_statusbar_message('Release %s loaded', self.id, timeout=3000)
        self.metadata["~#length"] = duration
        self.metadata["~length"] = format_time(duration)

    def _add_file(self, track, file):
        self._files += 1
        self.update(False)

    def _remove_file(self, track, file):
        self._files -= 1
        self.update(False)

    def match_files(self, files):
        """Match files on tracks on this album, based on metadata similarity."""
        matches = []
        for file in files:
            for track in self.tracks:
                sim = track.metadata.compare(file.orig_metadata)
                matches.append((sim, file, track))
            QtCore.QCoreApplication.processEvents()
        matches.sort(reverse=True)
        matched = {}
        for sim, file, track in matches:
            if sim < self.config.setting['track_matching_threshold']:
                break
            if file in matched:
                continue
            if track.linked_file and sim < track.linked_file.similarity:
                continue
            matched[file] = track
        unmatched = [f for f in files if f not in matched]
        for file, track in matched.items():
            file.move(track)
        for file in unmatched:
            file.move(self.unmatched_files)

    def match_file(self, file, trackid=None):
        """Match the file on a track on this album, based on trackid or metadata similarity."""
        if trackid is not None:
            for track in self.tracks:
                if track.metadata['musicbrainz_trackid'] == trackid:
                    file.move(track)
                    return
        self.match_files([file])

    def can_save(self):
        return self._files > 0

    def can_remove(self):
        return True

    def can_edit_tags(self):
        return False

    def can_analyze(self):
        return False

    def can_refresh(self):
        return True

    def column(self, column):
        if column == 'title':
            if self.tracks:
                return '%s (%d/%d)' % (self.metadata['album'], len(self.tracks), self._files)
            else:
                return self.metadata['album']
        elif column == '~length':
            length = self.metadata["~#length"]
            if length:
                return format_time(length)
            else:
                return ''
        elif column == 'artist':
            return self.metadata['albumartist']
        else:
            return ''

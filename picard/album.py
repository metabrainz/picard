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

from PyQt4 import QtCore
from musicbrainz2.model import Relation
from musicbrainz2.utils import extractUuid, extractFragment
from musicbrainz2.webservice import Query, WebServiceError, ReleaseIncludes, TrackIncludes
from picard.component import Component, ExtensionPoint
from picard.metadata import Metadata, run_album_metadata_processors, run_track_metadata_processors
from picard.dataobj import DataObject
from picard.track import Track
from picard.script import ScriptParser
from picard.ui.item import Item
from picard.util import needs_read_lock, needs_write_lock


_AMAZON_IMAGE_URL = "http://images.amazon.com/images/P/%s.01.LZZZZZZZ.jpg" 


class AlbumLoadError(Exception):
    pass


class Album(DataObject, Item):

    def __init__(self, id, title=None):
        DataObject.__init__(self, id)
        self.metadata = Metadata()
        if title:
            self.metadata[u"album"] = title
        self.unmatched_files = []
        self.files = []
        self.tracks = []
        self.loaded = False

    def __str__(self):
        return '<Album %s "%s">' % (self.id, self.metadata[u"album"])

    def load(self, force=False):
        self.tagger.set_statusbar_message('Loading release %s...', self.id)

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
            self.tagger.set_statusbar_message('Loading release %s (track %d/%d)...', self.id, tracknum, totaltracks)
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

        self.tagger.set_statusbar_message('Release %s loaded', self.id, timeout=3000)
        self.metadata["~#length"] = duration

    @needs_read_lock
    def getNumTracks(self):
        return len(self.tracks)

    @needs_write_lock
    def addUnmatchedFile(self, file):
        self.unmatched_files.append(file)
        self.emit(QtCore.SIGNAL("fileAdded(int)"), file.id)

    @needs_write_lock
    def addLinkedFile(self, track, file):
        index = self.tracks.index(track)
        self.files.append(file)
        self.emit(QtCore.SIGNAL("track_updated"), track)

    @needs_write_lock
    def removeLinkedFile(self, track, file):
        self.emit(QtCore.SIGNAL("track_updated"), track)

    @needs_read_lock
    def getNumUnmatchedFiles(self):
        return len(self.unmatched_files)

    @needs_read_lock
    def getNumTracks(self):
        return len(self.tracks)

    @needs_read_lock
    def getNumLinkedFiles(self):
        count = 0
        for track in self.tracks:
            if track.is_linked():
                count += 1
        return count

    @needs_write_lock
    def remove_file(self, file):
        index = self.unmatched_files.index(file)
        self.emit(QtCore.SIGNAL("fileAboutToBeRemoved"), index)
#        self.test = self.unmatched_files[index]
        del self.unmatched_files[index]
        print self.unmatched_files
        self.emit(QtCore.SIGNAL("fileRemoved"), index)

    def matchFile(self, file):
        bestMatch = 0.0, None
        for track in self.tracks:
            sim = file.orig_metadata.compare(track.metadata)
            if sim > bestMatch[0]:
                bestMatch = sim, track

        if bestMatch[1]:
            file.move_to_track(bestMatch[1])

    @needs_read_lock
    def can_save(self):
        """Return if this object can be saved."""
        if self.files:
            return True
        else:
            return False

    def can_remove(self):
        """Return if this object can be removed."""
        return True

    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return False

    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False

    def can_refresh(self):
        return True

    def match_files(self, files):
        """Match files on tracks on this album, based on metadata similarity."""
        matches = []
        for file in files:
            for track in self.tracks:
                sim = track.metadata.compare(file.orig_metadata)
                matches.append((sim, file, track))
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
        for file, track in matched.items():
            file.move(track)

    def match_file(self, file, trackid=None):
        """Match the file on a track on this album, based on trackid or metadata similarity."""
        if trackid is not None:
            for track in self.tracks:
                if track.metadata['musicbrainz_trackid'] == trackid:
                    file.move(track)
                    return
        self.match_files([file])

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
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
from musicbrainz2.webservice import Query, WebServiceError, ReleaseIncludes
from picard.api import IMetadataProcessor
from picard.component import Component, ExtensionPoint
from picard.metadata import Metadata
from picard.dataobj import DataObject
from picard.track import Track
from picard.util import needs_read_lock, needs_write_lock


_AMAZON_IMAGE_URL = "http://images.amazon.com/images/P/%s.01.LZZZZZZZ.jpg" 


class AlbumLoadError(Exception):
    pass


class MetadataProcessor(Component):

    processors = ExtensionPoint(IMetadataProcessor)

    def process_album_metadata(self, metadata, release):
        for processor in self.processors:
            processor.process_album_metadata(metadata, release)

    def process_track_metadata(self, metadata, release, track):
        for processor in self.processors:
            processor.process_track_metadata(metadata, release, track)


class Album(DataObject):

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
        self.tagger.log.debug(u"Loading album %r", self.id)

        ws = self.tagger.get_web_service(cached=not force)
        query = Query(ws=ws)
        release = None
        try:
            inc = ReleaseIncludes(artist=True, releaseEvents=True, discs=True,
                                  tracks=True, artistRelations=True)
            release = query.getReleaseById(self.id, inc)
        except WebServiceError, e:
            self.hasLoadError = True
            raise AlbumLoadError, e
        
        translate = self.config.setting["translate_artist_names"]

        self.metadata.clear()
        self.metadata.from_release(release)
        self.metadata.from_relations(release.getRelations())

        if self.metadata["asin"] and self.config.setting["use_amazon_images"]:
            fileobj = ws.get_from_url(
                _AMAZON_IMAGE_URL % release.asin)
            data = fileobj.read()
            fileobj.close()
            if len(data) > 1000:
                self.metadata.add("~artwork", ("image/jpeg", data))

        metadata_processor = MetadataProcessor(self.tagger)
        metadata_processor.process_album_metadata(self.metadata, release)

        if self.config.setting["enable_tagger_script"]:
            script = self.config.setting["tagger_script"]
        else:
            script = None

        self.lock_for_write()
        self.tracks = []
        self.unlock()

        tracknum = 1
        duration = 0
        for track in release.tracks:
            tr = Track(extractUuid(track.id), self)
            tr.duration = track.duration or 0
            tr.metadata.copy(self.metadata)
            tr.metadata.from_track(track, release)
            duration += tr.duration
            # Metadata processor plugins
            metadata_processor.process_track_metadata(tr.metadata, release, track)
            # User's script
            if script:
                self.tagger.evaluate_script(script, tr.metadata)
            self.lock_for_write()
            self.tracks.append(tr)
            self.unlock()
            tracknum += 1

        self.metadata["~#length"] = duration

        self.loaded = True

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

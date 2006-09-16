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

from PyQt4 import QtCore, QtGui
from threading import RLock
from musicbrainz2.webservice import Query, WebServiceError, ReleaseIncludes
from musicbrainz2.model import VARIOUS_ARTISTS_ID, NS_MMD_1
from musicbrainz2.utils import extractUuid, extractFragment
from picard.metadata import Metadata
from picard.util import format_time
from picard.dataobj import DataObject
from picard.track import Track
from picard.artist import Artist

class AlbumLoadError(Exception):
    pass

class Album(DataObject):

    def __init__(self, id, name, artist=None):
        DataObject.__init__(self, id, name)
        self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.metadata = Metadata()
        self.unmatched_files = []
        self.files = []
        self.artist = artist
        self.tracks = []
        self.duration = 0

    def __str__(self):
        return '<Album %s "%s">' % (self.id, self.name.decode("UTF-8"))
        
    def lock(self):
        self.mutex.lock()
        
    def unlock(self):
        self.mutex.unlock()
        
    def load(self):
        self.tagger.log.debug("Loading album %r", self.id)
        
        query = Query()
        release = None
        try:
            inc = ReleaseIncludes(artist=True, releaseEvents=True, discs=True, tracks=True)
            release = query.getReleaseById(self.id, inc)
        except WebServiceError, e:
            self.hasLoadError = True
            raise AlbumLoadError, e
            
        self.lock()

        self.metadata.clear()
        self.metadata["ALBUM"] = release.title
        self.metadata["ARTIST"] = release.artist.name
        self.metadata["ARTIST_SORTNAME"] = release.artist.sortName 
        self.metadata["ALBUMARTIST"] = release.artist.name
        self.metadata["ALBUMARTIST_SORTNAME"] = release.artist.sortName 
        self.metadata["MUSICBRAINZ_ALBUMID"] = extractUuid(release.id) 
        self.metadata["MUSICBRAINZ_ARTISTID"] = extractUuid(release.artist.id) 
        self.metadata["MUSICBRAINZ_ALBUMARTISTID"] = \
            extractUuid(release.artist.id) 
        self.metadata["TOTALTRACKS"] = str(len(release.tracks))
        
        self.name = release.title
        self.artist = Artist(release.artist.id, release.artist.name)
        
        self.duration = 0
        self.tracks = []
        tracknum = 1
        for track in release.tracks:
            if track.artist:
                artist = Artist(extractUuid(track.artist.id),
                                track.artist.name)
            else:
                artist = Artist(extractUuid(release.artist.id),
                                release.artist.name)
            tr = Track(extractUuid(track.id), track.title, artist, self)
            tr.duration = track.duration or 0
            tr.metadata.copy(self.metadata)
            tr.metadata["title"] = track.title
            if track.artist:
                tr.metadata["artist"] = artist.name
                tr.metadata["artist_sortname"] = track.artist.sortName
                tr.metadata["musicbrainz_artistid"] = extractUuid(artist.id)
            tr.metadata["musicbrainz_trackid"] = extractUuid(track.id)
            tr.metadata["tracknumber"] = str(tracknum)
            tr.metadata["~#length"] = tr.duration
            self.tracks.append(tr)
            self.duration += tr.duration
            tracknum += 1

        self.metadata["~#length"] = self.duration

        self.unlock()

    def getNumTracks(self):
        return len(self.tracks)
        
    def addUnmatchedFile(self, file):
        self.unmatched_files.append(file)
        self.emit(QtCore.SIGNAL("fileAdded(int)"), file.id)

    def addLinkedFile(self, track, file):
        index = self.tracks.index(track)
        self.files.append(file)
        self.emit(QtCore.SIGNAL("track_updated"), track)

    def removeLinkedFile(self, track, file):
        self.emit(QtCore.SIGNAL("track_updated"), track)

    def getNumUnmatchedFiles(self):
        return len(self.unmatched_files)

    def getNumTracks(self):
        return len(self.tracks)

    def getNumLinkedFiles(self):
        count = 0
        for track in self.tracks:
            if track.is_linked():
                count += 1
        return count

    def remove_file(self, file):
        index = self.unmatched_files.index(file)
        self.emit(QtCore.SIGNAL("fileAboutToBeRemoved"), index)
#        self.test = self.unmatched_files[index]
        del self.unmatched_files[index]
        print self.unmatched_files
        self.emit(QtCore.SIGNAL("fileRemoved"), index)

    def getName(self):
        if self.getNumTracks():
            return _(u"%s (%d / %d)") % (self.name, self.getNumTracks(), self.getNumLinkedFiles())
        else:
            return self.name

    def matchFile(self, file):
        bestMatch = 0.0, None
        for track in self.tracks:
            sim = file.get_similarity(track.metadata)
            if sim > bestMatch[0]:
                bestMatch = sim, track
                
        if bestMatch[1]:
            file.move_to_track(bestMatch[1])

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


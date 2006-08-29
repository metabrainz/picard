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
from picard.util import formatTime
from picard.dataobj import DataObject
from picard.track import Track
from picard.artist import Artist

class AlbumLoadError(Exception):
    pass

class Album(DataObject):

    def __init__(self, id, name, artist=None):
        DataObject.__init__(self, id, name)
        self._lock = RLock()
        self.unmatchedFiles = []
        self.artist = artist
        self.tracks = []
        self.duration = 0

    def __str__(self):
        return u'<Album %s, name %s>' % (self.id, self.name)
        
    def lock(self):
        self._lock.acquire()
        
    def unlock(self):
        self._lock.release()
        
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
            
        self.name = release.title
        self.artist = Artist(release.artist.id, release.artist.name)
        
        self.duration = 0
        self.tracks = []
        for track in release.tracks:
            if track.artist:
                artist = Artist(track.artist.id, track.artist.name)
            else:
                artist = Artist(release.artist.id, release.artist.name)
            tr = Track(track.id, track.title, artist, self)
            tr.duration = track.duration or 0
            self.tracks.append(tr)
            self.duration += tr.duration 
        
        self.unlock()

    def getNumTracks(self):
        return len(self.tracks)
        
    def addUnmatchedFile(self, file):
        self.unmatchedFiles.append(file)
        self.emit(QtCore.SIGNAL("fileAdded(int)"), file.id)

    def getNumUnmatchedFiles(self):
        return len(self.unmatchedFiles)
        
    numUnmatchedFiles = property(getNumUnmatchedFiles)

    def removeFile(self, file):
        index = self.unmatchedFiles.index(file)
        self.emit(QtCore.SIGNAL("fileAboutToBeRemoved"), index)
#        self.test = self.unmatchedFiles[index]
        del self.unmatchedFiles[index]
        print self.unmatchedFiles
        self.emit(QtCore.SIGNAL("fileRemoved"), index)


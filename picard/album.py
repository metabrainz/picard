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
        self.files = []
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
            
        mdata = Metadata()
        mdata["ALBUM"] = release.title
        mdata["ARTIST"] = release.artist.name
        mdata["ARTIST_SORTNAME"] = release.artist.sortName 
        mdata["ALBUMARTIST"] = release.artist.name
        mdata["ALBUMARTIST_SORTNAME"] = release.artist.sortName 
        mdata["MUSICBRAINZ_ALBUMID"] = release.id 
        mdata["MUSICBRAINZ_ARTISTID"] = release.artist.id 
        mdata["MUSICBRAINZ_ALBUMARTISTID"] = release.artist.id 
        mdata["TOTALTRACKS"] = len(release.tracks)
        
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
            tr.metadata.copy(mdata)
            tr.metadata["TITLE"] = track.title
            if track.artist:
                tr.metadata["ARTIST"] = artist.name
                tr.metadata["ARTIST_SORTNAME"] = track.artist.sortName
                tr.metadata["MUSICBRAINZ_ARTISTID"] = artist.id
            tr.metadata["MUSICBRAINZ_TRACKID"] = track.id
            self.tracks.append(tr)
            self.duration += tr.duration
        
        self.unlock()

    def getNumTracks(self):
        return len(self.tracks)
        
    def addUnmatchedFile(self, file):
        self.unmatchedFiles.append(file)
        self.emit(QtCore.SIGNAL("fileAdded(int)"), file.id)

    def addLinkedFile(self, track, file):
        index = self.tracks.index(track)
        self.files.append(file)
        self.emit(QtCore.SIGNAL("trackUpdated"), track)

    def removeLinkedFile(self, track, file):
        self.emit(QtCore.SIGNAL("trackUpdated"), track)

    def getNumUnmatchedFiles(self):
        return len(self.unmatchedFiles)

    def getNumTracks(self):
        return len(self.tracks)

    def getNumLinkedFiles(self):
        count = 0
        for track in self.tracks:
            if track.isLinked():
                count += 1
        return count

    def removeFile(self, file):
        index = self.unmatchedFiles.index(file)
        self.emit(QtCore.SIGNAL("fileAboutToBeRemoved"), index)
#        self.test = self.unmatchedFiles[index]
        del self.unmatchedFiles[index]
        print self.unmatchedFiles
        self.emit(QtCore.SIGNAL("fileRemoved"), index)

    def getName(self):
        if self.getNumTracks():
            return _(u"%s (%d / %d)") % (self.name, self.getNumTracks(), self.getNumLinkedFiles())
        else:
            return self.name


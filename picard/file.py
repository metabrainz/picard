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
import os.path
from picard.metadata import Metadata

class AudioProperties(object):
    
    def __init__(self):
        self.length = 0
        self.bitrate = 0

class File(QtCore.QObject):
    
    _idCounter = 1
    
    def __init__(self, fileName):
        QtCore.QObject.__init__(self)
        assert(isinstance(fileName, unicode))
        self._lock = QtCore.QMutex()
        self._id = File._idCounter
        File._idCounter += 1
        self.fileName = fileName
        self.baseFileName = os.path.basename(fileName)
        self.album = None
        
        self.localMetadata = Metadata()
        self.serverMetadata = Metadata()
        self.audioProperties = AudioProperties()

    def lock(self):
        self._lock.lock()
        
    def unlock(self):
        self._lock.unlock()

    def getId(self):
        return self._id

    id = property(getId)

    def save(self):
        raise NotImplementedError()
        
    def getNewMetadata(self):
        return self.serverMetadata
        
    def moveToAlbumAsUnlinked(self, album):
        """Moves the file to a given album as 'unmatched'."""
        self.removeFromAlbum()
        self.log.debug("File #%d moving to album %s as unlinked", self.getId(), album.getId())
        self.album = album
        self.album.addUnmatchedFile(self) 
        
    def removeFromAlbum(self):
        """Removes the file from whatever album it may be on. Does nothing if
        the file is not currently on an album."""
        if self.album is None:
            return
        self.log.debug("File #%d being removed from album %s", self.getId(), self.album.getId())
        self.album.removeFile(self)
        self.album = None     


class FileManager(QtCore.QObject):
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.connect(self, QtCore.SIGNAL("fileAdded(int)"), self.onFileAdded)
        self.mutex = QtCore.QMutex()
        self.files = {}
        
    def getFile(self, fileId):
        locker = QtCore.QMutexLocker(self.mutex)
        return self.files[fileId]
        
    def addFile(self, file):
        self.log.debug("Adding file %s", str(file));
        self.mutex.lock()
        self.files[file.id] = file
        self.mutex.unlock()
        self.emit(QtCore.SIGNAL("fileAdded(int)"), file.id)

    def onFileAdded(self, fileId):
        file = self.getFile(fileId)
        file.moveToAlbumAsUnlinked(self.tagger.albumManager.unmatchedFiles)

    def removeFiles(self, files):
        for file in files:
            self.mutex.lock()
            file.removeFromAlbum()
            del self.files[file.id]
            self.mutex.unlock()


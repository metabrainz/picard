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
from picard.similarity import similarity

class AudioProperties(object):
    
    def __init__(self):
        self.length = 0
        self.bitrate = 0

class File(QtCore.QObject):
    
    _idCounter = 1
    
    def __init__(self, fileName):
        QtCore.QObject.__init__(self)
        assert(isinstance(fileName, unicode))

        self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        
        self._id = File._idCounter
        File._idCounter += 1
        self.fileName = fileName
        self.baseFileName = os.path.basename(fileName)
        
        self.cluster = None
        self.track = None
        
        self.localMetadata = Metadata()
        self.metadata = Metadata()
        self.audioProperties = AudioProperties()

    def lock(self):
        self.mutex.lock()
        
    def unlock(self):
        self.mutex.unlock()

    def getId(self):
        return self._id

    id = property(getId)

    def save(self):
        raise NotImplementedError()

    def getNewMetadata(self):
        return self.metadata

    def removeFromCluster(self):
        locker = QtCore.QMutexLocker(self.mutex)
        if self.cluster is not None:
            self.log.debug("File %r being removed from cluster %r", self, self.cluster)
            self.cluster.removeFile(self)
            self.cluster = None

    def removeFromTrack(self):
        locker = QtCore.QMutexLocker(self.mutex)
        if self.track is not None:
            self.log.debug("File %r being removed from track %r", self, self.track)
            self.track.removeFile(self)
            self.track = None

    def moveToCluster(self, cluster):
        locker = QtCore.QMutexLocker(self.mutex)
        if cluster == self.cluster:
            return
        self.removeFromCluster()
        self.removeFromTrack()
        self.log.debug("File %r being removed from cluster %r", self, cluster)
        self.cluster = cluster
        self.cluster.addFile(self)

    def moveToTrack(self, track):
        locker = QtCore.QMutexLocker(self.mutex)
        if track == self.track:
            return
        self.removeFromCluster()
        self.removeFromTrack()
        self.log.debug("File %r being removed from track %r", self, track)
        self.track = track
        self.track.addFile(self)

    def getSimilarity(self, metadata=None):
        locker = QtCore.QMutexLocker(self.mutex)
        if not metadata:
            metadata = self.metadata 
        return similarity(self.localMetadata.get(u"TITLE", u""),
            metadata.get(u"TITLE", u""))
    
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
        file.moveToCluster(self.tagger.unmatchedFiles)

    def removeFiles(self, files):
        for file in files:
            self.mutex.lock()
            file.removeFromCluster()
            file.removeFromTrack()
            del self.files[file.id]
            self.mutex.unlock()


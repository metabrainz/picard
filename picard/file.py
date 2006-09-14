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
from picard.parsefilename import parseFileName

class AudioProperties(object):
    
    def __init__(self):
        self.length = 0
        self.bitrate = 0

class File(QtCore.QObject):

    _id_counter = 1

    def __init__(self, filename):
        QtCore.QObject.__init__(self)
        self._id = File._id_counter
        File._id_counter += 1
        self.mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.filename = filename
        self.base_filename = os.path.basename(filename)
        self.cluster = None
        self.track = None
        self.orig_metadata = Metadata()
        self.metadata = Metadata()
        self.audioProperties = AudioProperties()

    def __str__(self):
        return ('<File #%d, "%s">' % (self.id, self.base_filename)).encode("UTF-8")

    def lock(self):
        self.mutex.lock()
        
    def unlock(self):
        self.mutex.unlock()

    def getId(self):
        return self._id

    id = property(getId)

    def save(self):
        raise NotImplementedError()

    def remove_from_cluster(self):
        locker = QtCore.QMutexLocker(self.mutex)
        if self.cluster is not None:
            self.log.debug("%s being removed from %s", self, self.cluster)
            self.cluster.remove_file(self)
            self.cluster = None

    def remove_from_track(self):
        locker = QtCore.QMutexLocker(self.mutex)
        if self.track is not None:
            self.log.debug("%s being removed from %s", self, self.track)
            self.track.remove_file(self)
            self.track = None

    def move_to_cluster(self, cluster):
        locker = QtCore.QMutexLocker(self.mutex)
        if cluster != self.cluster:
            self.remove_from_cluster()
            self.remove_from_track()
            self.log.debug("%s being moved to %s", self, cluster)
            self.cluster = cluster
            self.cluster.add_file(self)

    def move_to_track(self, track):
        locker = QtCore.QMutexLocker(self.mutex)
        if track != self.track:
            self.remove_from_cluster()
            self.remove_from_track()
            self.log.debug("%s being moved to %s", self, track)
            self.track = track
            self.track.add_file(self)

    def get_similarity(self, metadata=None):
        locker = QtCore.QMutexLocker(self.mutex)
        if not metadata:
            metadata = self.metadata
        return self.orig_metadata.compare(metadata)


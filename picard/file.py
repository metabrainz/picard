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

import os.path
import sys
from PyQt4 import QtCore
from picard.metadata import Metadata
from picard.parsefilename import parseFileName
from picard.similarity import similarity

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

    def __str__(self):
        return ('<File #%d "%s">' % (self.id, self.base_filename)).encode("UTF-8")

    def lock(self):
        self.mutex.lock()
        
    def unlock(self):
        self.mutex.unlock()

    def getId(self):
        return self._id

    id = property(getId)

    def save(self):
        """Save the file."""
        locker = QtCore.QMutexLocker(self.mutex)
        try:
            self._save()
            if self.config.setting["rename_files"]:
                format = self.config.setting["file_naming_format"]
                filename = self.tagger.evaluate_script(format, self.metadata)
                filename = os.path.basename(filename) + os.path.splitext(self.filename)[1]
                filename = os.path.join(os.path.dirname(self.filename), filename)
                os.rename(self.filename, filename)
                self.filename = filename
        except Exception, e:
            raise
        else:
            self.orig_metadata.copy(self.metadata)
            self.metadata.changed = False

    def _save(self):
        """Save metadata to the file."""
        raise NotImplementedError

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

    def can_save(self):
        """Return if this object can be saved."""
        return True

    def can_remove(self):
        """Return if this object can be removed."""
        return True


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
from picard.metadata import Metadata
from picard.util import formatTime
from picard.dataobj import DataObject

class Track(DataObject):
    
    def __init__(self, id, name, artist=None, album=None):
        DataObject.__init__(self, id, name)
        self.artist = artist
        self.album = album
        self.duration = 0
        self.file = None
        self.metadata = Metadata()

    def __str__(self):
        return u"<Track %s, name %s>" % (self.id, self.name)

    def getDuration(self):
        return self._duration

    def setDuration(self, duration):
        self._duration = duration

    duration = property(getDuration, setDuration)

    def add_file(self, file):
        if self.file:
            self.file.move_to_cluster(self.tagger.unmatched_files)
        self.file = file
        file.metadata.copy(self.metadata)
        self.album.addLinkedFile(self, file)
        
    def remove_file(self, file):
        file = self.file
        self.file = None
        self.album.removeLinkedFile(self, file)
        return file

    def isLinked(self):
        return (self.file is not None)

    def getLinkedFile(self):
        return self.file


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

class Cluster(QtCore.QObject):

    def __init__(self, name):
        QtCore.QObject.__init__(self)
        self.name = name
        self.artist = u""
        self.files = []

    def addFile(self, file):
        self.files.append(file)
        index = self.indexOfFile(file)
        self.emit(QtCore.SIGNAL("fileAdded"), self, file, index)

    def removeFile(self, file):
        index = self.indexOfFile(file)
        self.files.remove(file)
        self.emit(QtCore.SIGNAL("fileRemoved"), self, file, index)

    def getNumFiles(self):
        return len(self.files)

    def indexOfFile(self, file):
        return self.files.index(file)


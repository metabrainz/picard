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

class Cluster(QtCore.QObject):

    def __init__(self, name):
        QtCore.QObject.__init__(self)
        self.name = name
        self.artist = u""
        self.files = []

    def __str__(self):
        return '<Cluster "%s">' % (self.name.decode("UTF-8"))

    def add_file(self, file):
        self.files.append(file)
        index = self.index_of_file(file)
        self.emit(QtCore.SIGNAL("fileAdded"), self, file, index)

    def remove_file(self, file):
        index = self.index_of_file(file)
        self.files.remove(file)
        self.emit(QtCore.SIGNAL("fileRemoved"), self, file, index)

    def get_num_files(self):
        return len(self.files)

    def index_of_file(self, file):
        return self.files.index(file)

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

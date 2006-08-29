# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

class DataObject(QtCore.QObject):
   
    def __init__(self, id, name):
        QtCore.QObject.__init__(self)
        self._id = id
        self._name = name

    def setId(self, id):
        self._id = id

    def getId(self):
        return self._id

    id = property(getId, setId)

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name     
        
    name = property(getName, setName)

        

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
from picard.util import formatTime
from picard.dataobj import DataObject

class Track(DataObject):
    
    def __init__(self, id, name, artist=None, album=None):
        DataObject.__init__(self, id, name)
        self.artist = artist
        self.album = album
        self.duration = 0
        
    def __str__(self):
        return u"<Track %s, name %s>" % (self.id, self.name)
        
    def getDuration(self):
        return self._duration
        
    def setDuration(self, duration):
        self._duration = duration
        self._durationStr = formatTime(duration)
            
    duration = property(getDuration, setDuration)
        

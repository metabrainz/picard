# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
from copy import copy

class Metadata(QtCore.QObject):
    
    """Class to handle tag lists.
    
    @see http://wiki.musicbrainz.org/UnifiedTagging
    """
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.tags = {}
        
    def compare(self, other):
        return 0.0

    def copy(self, other):
        self.tags = copy(other.tags)

    def set(self, name, value):
        self.tags[name.upper()] = value
        
    def get(self, name, default=u""):
        name = name.upper()
        if self.tags.has_key(name):
            return self.tags[name]
        return default

    def __getitem__(self, name):
        return self.get(name)
        
    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, item):
        self.tags.has_key(item)
        
    def getTitle(self):
        return self["TITLE"]
        
    def setTitle(self, value):
        self["TITLE"] = value
        
    title = property(getTitle, setTitle)
    
    def getArtist(self):
        return self["ARTIST"]
        
    def setArtist(self, value):
        self["ARTIST"] = value
        
    artist = property(getArtist, setArtist)
    
    def getAlbum(self):
        return self["ALBUM"]
        
    def setAlbum(self, value):
        self["ALBUM"] = value
        
    album = property(getAlbum, setAlbum)


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
from picard.similarity import similarity

class Metadata(QtCore.QObject):
    
    """Class to handle tag lists.
    
    Special tags:
        * ~#length
        * ~filename
    
    @see http://wiki.musicbrainz.org/UnifiedTagging
    """
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.tags = {}
        
    def compare(self, other):
        parts = []
        
        tags = {
            "musicbrainz_trackid": 10000,
            "musicbrainz_artistid": 10,
            "musicbrainz_albumid": 10,
            "title": 10,
            "artist": 10,
            "album": 9,
            "tracknumber": 8,
        }

        identical = [
            "musicbrainz_trackid",
            "musicbrainz_artistid",
            "musicbrainz_albumid",
            "tracknumber",
            "totaltracks",
            "discnumber",
            "totaldiscs",
        ]
        
        for tag in self.keys():
            if tag not in tags and not tag.startswith("~"):
                tags[tag] = 1
        
        for tag in other.keys():
            if tag not in tags and not tag.startswith("~"):
                tags[tag] = 1
                
        for tag, weight in tags.items():
            if self[tag] and other[tag]:
                if tag in identical:
                    sim = 1.0 - abs(cmp(self[tag], other[tag]))
                else:
                    sim = similarity(self[tag], other[tag])
                parts.append((sim, weight))
            
        total = reduce(lambda x, y: x + y[1], parts, 0.0)
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    def copy(self, other):
        self.tags = copy(other.tags)

    def set(self, name, value):
        self.tags[name.lower()] = value
        
    def get(self, name, default=u""):
        name = name.lower()
        if self.tags.has_key(name):
            return self.tags[name]
        return default

    def keys(self):
        return self.tags.keys()

    def __getitem__(self, name):
        return self.get(name)
        
    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, item):
        self.tags.has_key(item)


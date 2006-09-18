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
from picard.similarity import similarity, raw_similarity

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
        self.changed = False
        
    def compare(self, other):
        parts = []
        
        tags = {
            "~#length": 16,
            "title": 20,
            "artist": 6,
            "album": 12,
            "tracknumber": 5,
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

        #for tag in self.keys():
        #    if tag not in tags and not tag.startswith("~"):
        #        tags[tag] = 1

        #for tag in other.keys():
        #    if tag not in tags and not tag.startswith("~"):
        #        tags[tag] = 1

        for tag, weight in tags.items():
            if self[tag] and other[tag]:
                if tag in identical:
                    sim = 1.0 - abs(cmp(self[tag], other[tag]))
                elif tag == "~#length":
                    sim = 1.0 - min(abs(self[tag] - other[tag]), 30000) / 30000.0
                else:
                    sim = similarity(self[tag], other[tag])
                parts.append((sim, weight))

        total = reduce(lambda x, y: x + y[1], parts, 0.0)
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    def copy(self, other):
        self.tags = copy(other.tags)

    def set(self, name, value):
        self.tags[name.lower()] = value

    def clear(self):
        self.tags.clear()

    def get(self, name, default=u""):
        name = name.lower()
        if self.tags.has_key(name):
            return self.tags[name]
        return default

    def keys(self):
        return self.tags.keys()

    def items(self):
        return self.tags.items()

    def __getitem__(self, name):
        return self.get(name)
        
    def __setitem__(self, name, value):
        self.set(name, value)
        self.changed = True

    def __contains__(self, item):
        return self.tags.has_key(item)

    def set_changed(self, changed=True):
        self.changed = changed

    def generate_filename(self, format):
        filename = format
        for key, value in self.tags.items():
            filename = filename.replace("%%%s%%" % key, value)
        return filename
        #'%albumartist%/%album% $if(%discnumber%, CD%discnumber%d)/%tracknumber% - %title%'

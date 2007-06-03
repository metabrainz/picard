# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006-2007 Lukáš Lalinský
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

import re
import unicodedata
from picard.plugin import ExtensionPoint
from picard.similarity import similarity, similarity2
from picard.util import LockableObject, needs_read_lock, needs_write_lock, format_time


class Metadata(LockableObject):
    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
    ]

    def __init__(self):
        LockableObject.__init__(self)
        self._items = {}
        self.changed = False
        self.images = []
        self.length = 0

    def add_image(self, mime, data):
        self.images.append((mime, data))

    @needs_read_lock
    def __repr__(self):
        return repr(self._items)

    def compare(self, other):
        parts = []
        total = 0
        #print self["title"], " --- ", other["title"]

        if self.length and other.length:
            score = 1.0 - min(abs(self.length - other.length), 30000) / 30000.0
            parts.append((score, 8))
            total += 8

        for name, weight in self.__weights:
            a = self[name]
            b = other[name]
            if a and b:
                if name in ('tracknumber', 'totaltracks'):
                    score = 1.0 - abs(cmp(a, b))
                else:
                    score = similarity2(a, b)
                parts.append((score, weight))
                total += weight
                #print name, score, weight
        #print "******", reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    @needs_write_lock
    def copy(self, other):
        self._items = {}
        for key, values in other.rawitems():
            self._items[key] = values[:]
        self.images = other.images[:]
        self.length = other.length

    @needs_write_lock
    def update(self, other):
        for name, values in other.rawitems():
            self._items[name] = values[:]
        if other.images:
            self.images = other.images[:]
        if other.length:
            self.length = other.length

    @needs_write_lock
    def clear(self):
        self._items = {}
        self.images = []
        self.length = 0

    def __get(self, name, default=None):
        values = self._items.get(name, None)
        if values:
            if len(values) > 1:
                return '; '.join(values)
            else:
                return values[0]
        else:
            return default

    def __set(self, name, values):
        if not isinstance(values, list):
            if isinstance(values, basestring):
                values = list(values.split('; '))
            else:
                values = [values]
        self._items[name] = values

    @needs_read_lock
    def getall(self, name):
        try:
            return self._items[name]
        except KeyError:
            return []

    @needs_read_lock
    def get(self, name, default=None):
        return self.__get(name, default)

    @needs_read_lock
    def __getitem__(self, name):
        return self.__get(name, u'')

    @needs_write_lock
    def set(self, name, value):
        self.__set(name, value)

    @needs_write_lock
    def __setitem__(self, name, value):
        self.__set(name, value)
        self.changed = True

    @needs_write_lock
    def add(self, name, value):
        self._items.setdefault(name, []).append(value)

    @needs_read_lock
    def keys(self):
        return self._items.keys()

    def iteritems(self):
        for name, values in self._items.iteritems():
            for value in values:
                yield name, value

    @needs_read_lock
    def items(self):
        """Returns the metadata items.

        >>> m.items()
        [("key1", "value1"), ("key1", "value2"), ("key2", "value3")]
        """
        return list(self.iteritems())

    @needs_read_lock
    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return self._items.items()

    @needs_read_lock
    def __contains__(self, name):
        for n, v in self._items.iteritems():
            if n == name:
                return True
        return False

    @needs_write_lock
    def __delitem__(self, name):
        del self._items[name]

    @needs_write_lock
    def set_changed(self, changed=True):
        self.changed = changed

    def strip_whitespace(self):
        """Strip leading/trailing whitespace.

        >>> m = Metadata()
        >>> m["foo"] = "  bar  "
        >>> m["foo"]
        "  bar  "
        >>> m.strip_whitespace()
        >>> m["foo"]
        "bar"
        """
        new = Metadata()
        for key, values in self.rawitems():
            if not key.startswith("~"):
                new[key] = [value.strip() for value in values]
        self.update(new)


_album_metadata_processors = ExtensionPoint()
_track_metadata_processors = ExtensionPoint()


def register_album_metadata_processor(function):
    """Registers new album-level metadata processor."""
    _album_metadata_processors.register(function.__module__, function)


def register_track_metadata_processor(function):
    """Registers new track-level metadata processor."""
    _track_metadata_processors.register(function.__module__, function)


def run_album_metadata_processors(tagger, metadata, release):
    for processor in _album_metadata_processors:
        processor(tagger, metadata, release)


def run_track_metadata_processors(tagger, metadata, release, track):
    for processor in _track_metadata_processors:
        processor(tagger, metadata, track, release)

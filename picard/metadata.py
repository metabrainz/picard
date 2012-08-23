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

from picard.plugin import ExtensionPoint
from picard.similarity import similarity2
from picard.util import load_release_type_scores

MULTI_VALUED_JOINER = '; '

class Metadata(dict):
    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
    ]

    def __init__(self):
        super(Metadata, self).__init__()
        self.images = []
        self.length = 0

    def add_image(self, mime, data, filename=None):
        self.images.append((mime, data, filename))

    def remove_image(self, index):
        self.images.pop(index)
    def compare(self, other):
        parts = []
        total = 0

        if self.length and other.length:
            score = 1.0 - min(abs(self.length - other.length), 30000) / 30000.0
            parts.append((score, 8))
            total += 8

        for name, weight in self.__weights:
            a = self[name]
            b = other[name]
            if a and b:
                if name in ('tracknumber', 'totaltracks'):
                    try:
                        ia = int(a)
                        ib = int(b)
                    except ValueError:
                        ia = a
                        ib = b
                    score = 1.0 - abs(cmp(ia, ib))
                else:
                    score = similarity2(a, b)
                parts.append((score, weight))
                total += weight
        return reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)

    def compare_to_release(self, release, weights, config):
        total = 0.0
        parts = []

        if "album" in self:
            b = release.title[0].text
            parts.append((similarity2(self["album"], b), weights["album"]))
            total += weights["album"]

        if "totaltracks" in self:
            a = int(self["totaltracks"])
            if "title" in weights:
                b = int(release.medium_list[0].medium[0].track_list[0].count)
            else:
                b = int(release.medium_list[0].track_count[0].text)
            if a > b:
                score = 0.0
            elif a < b:
                score = 0.3
            else:
                score = 1.0
            parts.append((score, weights["totaltracks"]))
            total += weights["totaltracks"]

        preferred_countries = config.setting["preferred_release_countries"].split("  ")
        preferred_formats = config.setting["preferred_release_formats"].split("  ")

        total_countries = len(preferred_countries)
        if total_countries:
            score = 0.0
            if "country" in release.children:
                try:
                    i = preferred_countries.index(release.country[0].text)
                    score = float(total_countries - i) / float(total_countries)
                except ValueError:
                    pass
            parts.append((score, weights["releasecountry"]))

        total_formats = len(preferred_formats)
        if total_formats:
            score = 0.0
            subtotal = 0
            for medium in release.medium_list[0].medium:
                if "format" in medium.children:
                    try:
                        i = preferred_formats.index(medium.format[0].text)
                        score += float(total_formats - i) / float(total_formats)
                    except ValueError:
                        pass
                    subtotal += 1
            if subtotal > 0: score /= subtotal
            parts.append((score, weights["format"]))

        if "releasetype" in weights:
            type_scores = load_release_type_scores(config.setting["release_type_scores"])
            if 'release_group' in release.children and 'type' in release.release_group[0].attribs:
                release_type = release.release_group[0].type
                score = type_scores.get(release_type, type_scores.get('Other', 0.5))
            else:
                score = 0.0
            parts.append((score, weights["releasetype"]))
            total += weights["releasetype"]

        return (total, parts)

    def copy(self, other):
        self.clear()
        for key, values in other.rawitems():
            self.set(key, values[:])
        self.images = other.images[:]
        self.length = other.length

    def update(self, other):
        for name, values in other.rawitems():
            self.set(name, values[:])
        if other.images:
            self.images = other.images[:]
        if other.length:
            self.length = other.length

    def clear(self):
        dict.clear(self)
        self.images = []
        self.length = 0

    def getall(self, name):
        return dict.get(self, name, [])

    def get(self, name, default=None):
        values = dict.get(self, name, None)
        if values:
            return MULTI_VALUED_JOINER.join(values)
        else:
            return default

    def __getitem__(self, name):
        return self.get(name, u'')

    def set(self, name, values):
        dict.__setitem__(self, name, values)

    def __setitem__(self, name, values):
        if not isinstance(values, list):
            values = [values]
        values = filter(None, map(unicode, values))
        if len(values):
            dict.__setitem__(self, name, values)
        else:
            self.pop(name, None)

    def add(self, name, value):
        if value or value == 0:
            self.setdefault(name, []).append(value)

    def add_unique(self, name, value):
        if value not in self.getall(name):
            self.add(name, value)

    def iteritems(self):
        for name, values in dict.iteritems(self):
            for value in values:
                yield name, value

    def items(self):
        """Returns the metadata items.

        >>> m.items()
        [("key1", "value1"), ("key1", "value2"), ("key2", "value3")]
        """
        return list(self.iteritems())

    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return dict.items(self)

    def apply_func(self, func):
        for key, values in self.rawitems():
            if not key.startswith("~"):
                self[key] = map(func, values)

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
        self.apply_func(lambda s: s.strip())


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

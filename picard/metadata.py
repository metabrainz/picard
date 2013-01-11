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

from PyQt4.QtCore import QObject
from picard.plugin import ExtensionPoint
from picard.similarity import similarity2
from picard.util import load_release_type_scores
from picard.mbxml import artist_credit_from_node

MULTI_VALUED_JOINER = '; '

class MetadataImage(object):
    def __init__(self, mime, data, filename_func=None, filename=None, description="", types=["front"]):
        super(MetadataImage, self).__init__()
        self.mime = mime
        self.data = data
        self.filename_func = filename_func
        self.filename = filename
        self.description = description
        self.types = types
        self.user_main_cover = False # used to override any automatic choice
        self.is_main_cover = False
        self.is_front = 'front' in types
        if self.is_front:
            self.main_type = 'front'
        else:
            self.main_type = self.types[0]
        self.update()

    def update(self):
        if self.filename_func is not None:
            self.filename = self.filename_func(self)
        elif not self.is_main_cover:
            self.filename = self.main_type
        else:
            self.filename = 'cover'


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

    def add_image(self, mime, data, filename_func=None, filename=None, description="", types=["front"]):
        """Adds the image ``data`` to this Metadata object.

        Arguments:
        mime -- The mimetype of the image
        data -- The image data
        filename_func -- A function(MetadataImage) that returns the filename, without an extension
        filename -- The image filename, without an extension
        description -- A description for the image
        types -- The image types - this should be a list of lower-cased names from
                 http://musicbrainz.org/doc/Cover_Art/Types
        """
        img = MetadataImage(mime, data, filename_func, filename, description, types)
        self.images.append(img)
        self.update_main_cover()
        return img

    def add_image_main_cover(self, mime, data, filename_func=None, filename=None, description="", types=["front"]):
        """Add image at start of the list and mark it as main cover
        """
        img = MetadataImage(mime, data, filename_func, filename, description, types)
        img.user_main_cover = True
        self.images.insert(0, img)
        self.update_main_cover()
        return img

    def remove_image(self, index):
        self.images.pop(index)
        self.update_main_cover()

    def update_main_cover(self):
        """Determines which metadata image should be considered as the main cover

        Most often it is the first image with type front, if any
        """
        if not self.images:
            return

        main_cover_image = None

        # check for first image with user_main_cover set
        for image in self.images:
            if image.user_main_cover:
                main_cover_image = image
                break

        if main_cover_image is None:
            # try to use first front image as main cover
            for image in self.images:
                if image.is_front:
                    main_cover_image = image
                    break

        if main_cover_image is None:
            # use first image as main cover
            main_cover_image = self.images[0]

        for image in self.images:
            saved_is_main_cover = image.is_main_cover
            image.is_main_cover = (image == main_cover_image)
            if image.is_main_cover != saved_is_main_cover:
                image.update()

    def get_main_cover(self):
        """Returns current main cover"""
        for image in self.images:
            if image.is_main_cover:
                return image
        return None

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

    def compare_to_release(self, release, weights, return_parts=False):
        """
        Compare metadata to a MusicBrainz release. Produces a probability as a
        linear combination of weights that the metadata matches a certain album.
        """
        config = QObject.config
        total = 0.0
        parts = []

        if "album" in self:
            b = release.title[0].text
            parts.append((similarity2(self["album"], b), weights["album"]))
            total += weights["album"]

        if "albumartist" in self and "albumartist" in weights:
            a = self["albumartist"]
            b = artist_credit_from_node(release.artist_credit[0], config)[0]
            parts.append((similarity2(a, b), weights["albumartist"]))
            total += weights["albumartist"]

        if "totaltracks" in self:
            a = int(self["totaltracks"])
            if "title" in weights:
                b = int(release.medium_list[0].medium[0].track_list[0].count)
            else:
                b = int(release.medium_list[0].track_count[0].text)
            score = 0.0 if a > b else 0.3 if a < b else 1.0
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
            if subtotal > 0:
                score /= subtotal
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

        rg = QObject.tagger.get_release_group_by_id(release.release_group[0].id)
        if release.id in rg.loaded_albums:
            parts.append((1.0, 6))

        return (total, parts) if return_parts else \
               (reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0), release)

    def compare_to_track(self, track, weights):
        config = QObject.config
        total = 0.0
        parts = []

        if 'title' in self:
            a = self['title']
            b = track.title[0].text
            parts.append((similarity2(a, b), weights["title"]))
            total += weights["title"]

        if 'artist' in self:
            a = self['artist']
            b = artist_credit_from_node(track.artist_credit[0], config)[0]
            parts.append((similarity2(a, b), weights["artist"]))
            total += weights["artist"]

        a = self.length
        if a > 0 and 'length' in track.children:
            b = int(track.length[0].text)
            score = 1.0 - min(abs(a - b), 30000) / 30000.0
            parts.append((score, weights["length"]))
            total += weights["length"]

        releases = []
        if "release_list" in track.children and "release" in track.release_list[0].children:
            releases = track.release_list[0].release

        if not releases:
            sim = reduce(lambda x, y: x + y[0] * y[1] / total, parts, 0.0)
            return (sim, None, None, track)

        result = (-1,)
        for release in releases:
            t, p = self.compare_to_release(release, weights, return_parts=True)
            sim = reduce(lambda x, y: x + y[0] * y[1] / (total + t), parts + p, 0.0)
            if sim > result[0]:
                rg = release.release_group[0] if "release_group" in release.children else None
                result = (sim, rg, release, track)

        return result

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

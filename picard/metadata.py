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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
from PyQt5.QtCore import QObject
from picard import config
from picard.plugin import PluginFunctions, PluginPriority
from picard.similarity import similarity2
from picard.util import (
    linear_combination_of_weights,
)
from picard.util.tags import PRESERVED_TAGS
from picard.mbjson import artist_credit_from_node
from picard.util.imagelist import ImageList

MULTI_VALUED_JOINER = '; '

# lengths difference over this number of milliseconds will give a score of 0.0
# equal lengths will give a score of 1.0
# example
# a     b     score
# 20000 0     0.333333333333
# 20000 10000 0.666666666667
# 20000 20000 1.0
# 20000 30000 0.666666666667
# 20000 40000 0.333333333333
# 20000 50000 0.0
LENGTH_SCORE_THRES_MS = 30000


class Metadata(dict):

    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
    ]

    multi_valued_joiner = MULTI_VALUED_JOINER

    def __init__(self):
        super().__init__()
        self.images = ImageList()
        self.deleted_tags = set()
        self.length = 0

    def __bool__(self):
        return bool(len(self) or len(self.images))

    def append_image(self, coverartimage):
        self.images.append(coverartimage)

    def set_front_image(self, coverartimage):
        # First remove all front images
        self.images[:] = [img for img in self.images if not img.is_front_image()]
        self.images.append(coverartimage)

    @property
    def images_to_be_saved_to_tags(self):
        if not config.setting["save_images_to_tags"]:
            return ()
        images = [img for img in self.images if img.can_be_saved_to_tags]
        if config.setting["embed_only_one_front_image"]:
            front_image = self.get_single_front_image(images)
            if front_image:
                return front_image
        return images

    def get_single_front_image(self, images=None):
        if not images:
            images = self.images
        for img in images:
            if img.is_front_image():
                return [img]
        return []

    def remove_image(self, index):
        self.images.pop(index)

    @staticmethod
    def length_score(a, b):
        return (1.0 - min(abs(a - b), LENGTH_SCORE_THRES_MS) /
                float(LENGTH_SCORE_THRES_MS))

    def compare(self, other):
        parts = []

        if self.length and other.length:
            score = self.length_score(self.length, other.length)
            parts.append((score, 8))

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
                    score = 1.0 - (int(ia != ib))
                else:
                    score = similarity2(a, b)
                parts.append((score, weight))

        return linear_combination_of_weights(parts)

    def compare_to_release(self, release, weights):
        """
        Compare metadata to a MusicBrainz release. Produces a probability as a
        linear combination of weights that the metadata matches a certain album.
        """
        parts = self.compare_to_release_parts(release, weights)
        return (linear_combination_of_weights(parts), release)

    def compare_to_release_parts(self, release, weights):
        parts = []
        if "album" in self:
            b = release['title']
            parts.append((similarity2(self["album"], b), weights["album"]))

        if "albumartist" in self and "albumartist" in weights:
            a = self["albumartist"]
            b = artist_credit_from_node(release['artist-credit'])[0]
            parts.append((similarity2(a, b), weights["albumartist"]))

        try:
            a = int(self["totaltracks"])
        except (ValueError, KeyError):
            pass
        else:
            if "title" in weights:
                b = release['media'][0]['track-count']
            else:
                b = release['track-count']
            score = 0.0 if a > b else 0.3 if a < b else 1.0
            parts.append((score, weights["totaltracks"]))

        preferred_countries = config.setting["preferred_release_countries"]
        preferred_formats = config.setting["preferred_release_formats"]

        total_countries = len(preferred_countries)
        if total_countries:
            score = 0.0
            if "country" in release:
                try:
                    i = preferred_countries.index(release['country'])
                    score = float(total_countries - i) / float(total_countries)
                except ValueError:
                    pass
            parts.append((score, weights["releasecountry"]))

        total_formats = len(preferred_formats)
        if total_formats:
            score = 0.0
            subtotal = 0
            for medium in release['media']:
                if "format" in medium:
                    try:
                        i = preferred_formats.index(medium['format'])
                        score += float(total_formats - i) / float(total_formats)
                    except ValueError:
                        pass
                    subtotal += 1
            if subtotal > 0:
                score /= subtotal
            parts.append((score, weights["format"]))

        if "releasetype" in weights:
            type_scores = dict(config.setting["release_type_scores"])
            if 'release-group' in release and 'primary-type' in release['release-group']:
                release_type = release['release-group']['primary-type']
                score = type_scores.get(release_type, type_scores.get('Other', 0.5))
            else:
                score = 0.0
            parts.append((score, weights["releasetype"]))

        rg = QObject.tagger.get_release_group_by_id(release['release-group']['id'])
        if release['id'] in rg.loaded_albums:
            parts.append((1.0, 6))

        return parts

    def compare_to_track(self, track, weights):
        parts = []

        if 'title' in self:
            a = self['title']
            b = track['title']
            parts.append((similarity2(a, b), weights["title"]))

        if 'artist' in self:
            a = self['artist']
            b = artist_credit_from_node(track['artist-credit'])[0]
            parts.append((similarity2(a, b), weights["artist"]))

        a = self.length
        if a > 0 and 'length' in track:
            b = track['length']
            score = self.length_score(a, b)
            parts.append((score, weights["length"]))

        releases = []
        if "releases" in track:
            releases = track['releases']

        if not releases:
            sim = linear_combination_of_weights(parts)
            return (sim, None, None, track)

        result = (-1,)

        for release in releases:
            release_parts = self.compare_to_release_parts(release, weights)
            sim = linear_combination_of_weights(parts + release_parts)
            if sim > result[0]:
                rg = release['release-group'] if "release-group" in release else None
                result = (sim, rg, release, track)
        return result

    def copy(self, other):
        self.clear()
        self.update(other)

    def update(self, other):
        for key in other.keys():
            self.set(key, other.getall(key)[:])
        if other.images:
            self.images = other.images[:]
        if other.length:
            self.length = other.length

        self.deleted_tags.update(other.deleted_tags)
        # Remove deleted tags from UI on save
        for tag in other.deleted_tags:
            self.pop(tag, None)

    def clear(self):
        super().clear()
        self.images = ImageList()
        self.length = 0
        self.deleted_tags = set()

    def getall(self, name):
        return super().get(name, [])

    def get(self, name, default=None):
        values = super().get(name, None)
        if values:
            return self.multi_valued_joiner.join(values)
        else:
            return default

    def __getitem__(self, name):
        return self.get(name, '')

    def set(self, name, values):
        super().__setitem__(name, values)
        if name in self.deleted_tags:
            self.deleted_tags.remove(name)

    def __setitem__(self, name, values):
        if not isinstance(values, list):
            values = [values]
        values = [string_(value) for value in values if value]
        if len(values):
            self.set(name, values)
        else:
            self.delete(name)

    def add(self, name, value):
        if value or value == 0:
            self.setdefault(name, []).append(value)
            if name in self.deleted_tags:
                self.deleted_tags.remove(name)

    def add_unique(self, name, value):
        if value not in self.getall(name):
            self.add(name, value)

    def delete(self, name):
        if name in self:
            self.pop(name, None)
        self.deleted_tags.add(name)

    def items(self):
        for name, values in super().items():
            for value in values:
                yield name, value

    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return dict.items(self)

    def apply_func(self, func):
        for key, values in self.rawitems():
            if key not in PRESERVED_TAGS:
                self[key] = [func(value) for value in values]

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


_album_metadata_processors = PluginFunctions()
_track_metadata_processors = PluginFunctions()


def register_album_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new album-level metadata processor."""
    _album_metadata_processors.register(function.__module__, function, priority)


def register_track_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new track-level metadata processor."""
    _track_metadata_processors.register(function.__module__, function, priority)


def run_album_metadata_processors(album_object, metadata, release):
    _album_metadata_processors.run(album_object, metadata, release)


def run_track_metadata_processors(track_object, metadata, release, track):
    _track_metadata_processors.run(track_object, metadata, track, release)

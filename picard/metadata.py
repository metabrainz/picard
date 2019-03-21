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
from collections.abc import (
    Iterable,
    MutableMapping,
)

from PyQt5.QtCore import QObject

from picard import config
from picard.mbjson import artist_credit_from_node
from picard.plugin import (
    PluginFunctions,
    PluginPriority,
)
from picard.similarity import similarity2
from picard.util import linear_combination_of_weights
from picard.util.imagelist import ImageList
from picard.util.tags import PRESERVED_TAGS

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


class Metadata(MutableMapping):

    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
    ]

    multi_valued_joiner = MULTI_VALUED_JOINER

    def __init__(self, *args, deleted_tags=None, images=None, length=None, **kwargs):
        self._store = dict()
        self.deleted_tags = set()
        self.length = 0
        self.images = ImageList()
        self.has_common_images = True

        d = dict(*args, **kwargs)
        for k, v in d.items():
            self[k] = v
        if images is not None:
            for image in images:
                self.images.append(image)
        if deleted_tags is not None:
            for tag in deleted_tags:
                del self[tag]
        if length is not None:
            self.length = int(length)

    def __bool__(self):
        return bool(len(self))

    def __len__(self):
        return len(self._store) + len(self.images)

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
            elif (a and name in other.deleted_tags
                  or b and name in self.deleted_tags):
                parts.append((0, weight))
        return linear_combination_of_weights(parts)

    def compare_to_release(self, release, weights):
        """
        Compare metadata to a MusicBrainz release. Produces a probability as a
        linear combination of weights that the metadata matches a certain album.
        """
        parts = self.compare_to_release_parts(release, weights)
        sim = linear_combination_of_weights(parts)
        if 'score' in release:
            sim *= release['score'] / 100
        return (sim, release)

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
            try:
                if "title" in weights:
                    b = release['media'][0]['track-count']
                else:
                    b = release['track-count']
            except KeyError:
                b = 0
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
        if total_formats and 'media' in release:
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
            # This section generates a score that determines how likely this release will be selected in a lookup.
            # The score goes from 0 to 1 with 1 being the most likely to be chosen and 0 the least likely
            # This score is based on the preferences of release-types found in this release
            # This algorithm works by taking the scores of the primary type (and secondary if found) and averages them
            # If no types are found, it is set to the score of the 'Other' type or 0.5 if 'Other' doesnt exist

            type_scores = dict(config.setting["release_type_scores"])
            score = 0.0
            other_score = type_scores.get('Other', 0.5)
            if 'release-group' in release and 'primary-type' in release['release-group']:
                types_found = [release['release-group']['primary-type']]
                if 'secondary-types' in release['release-group']:
                    types_found += release['release-group']['secondary-types']
                for release_type in types_found:
                    score += type_scores.get(release_type, other_score)
                score /= len(types_found)
            parts.append((score, weights["releasetype"]))

        rg = QObject.tagger.get_release_group_by_id(release['release-group']['id'])
        if release['id'] in rg.loaded_albums:
            parts.append((1.0, 6))

        return parts

    def compare_to_track(self, track, weights):
        parts = []

        if 'title' in self:
            a = self['title']
            b = track.get('title', '')
            parts.append((similarity2(a, b), weights["title"]))

        if 'artist' in self:
            a = self['artist']
            artist_credits = track.get('artist-credit', [])
            b = artist_credit_from_node(artist_credits)[0]
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
            if 'score' in track:
                sim *= track['score'] / 100
            if sim > result[0]:
                rg = release['release-group'] if "release-group" in release else None
                result = (sim, rg, release, track)
        return result

    def copy(self, other):
        self.clear()
        self.update(other)

    def update(self, *args, **kwargs):
        one_arg = len(args) == 1
        if one_arg and isinstance(args[0], self.__class__):
            # update from Metadata object
            other = args[0]

            for k, v in other.rawitems():
                self.set(k, v[:])

            for tag in other.deleted_tags:
                del self[tag]

            if other.images:
                self.images = other.images[:]
            if other.length:
                self.length = other.length

        elif one_arg and isinstance(args[0], MutableMapping):
            # update from MutableMapping (ie. dict)
            for k, v in args[0].items():
                self[k] = v
        elif args or kwargs:
            # update from a dict-like constructor parameters
            for k, v in dict(*args, **kwargs).items():
                self[k] = v
        else:
            # no argument, raise TypeError to mimic dict.update()
            raise TypeError("descriptor 'update' of '%s' object needs an argument" % self.__class__.__name__)

    def clear(self):
        self._store.clear()
        self.images = ImageList()
        self.length = 0
        self.clear_deleted()

    def clear_deleted(self):
        self.deleted_tags = set()

    def getall(self, name):
        return self._store.get(name, [])

    def getraw(self, name):
        return self._store[name]

    def get(self, name, default=None):
        values = self._store.get(name, None)
        if values:
            return self.multi_valued_joiner.join(values)
        else:
            return default

    def __contains__(self, name):
        return self._store.__contains__(name)

    def __getitem__(self, name):
        return self.get(name, '')

    def set(self, name, values):
        self._store[name] = values
        self.deleted_tags.discard(name)

    def __setitem__(self, name, values):
        if isinstance(values, str) or not isinstance(values, Iterable):
            values = [values]
        values = [str(value) for value in values if value or value == 0]
        if values:
            self.set(name, values)
        elif name in self._store:
            del self[name]

    def __delitem__(self, name):
        try:
            del self._store[name]
        except KeyError:
            pass
        finally:
            self.deleted_tags.add(name)

    def add(self, name, value):
        if value or value == 0:
            self._store.setdefault(name, []).append(value)
            self.deleted_tags.discard(name)

    def add_unique(self, name, value):
        if value not in self.getall(name):
            self.add(name, value)

    def delete(self, name):
        del self[name]

    def __iter__(self):
        return iter(self._store)

    def items(self):
        for name, values in self._store.items():
            for value in values:
                yield name, value

    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return self._store.items()

    def apply_func(self, func):
        for name, values in self.rawitems():
            if name not in PRESERVED_TAGS:
                self[name] = [func(value) for value in values]

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

    def __repr__(self):
        return "%s(%r, deleted_tags=%r, length=%r, images=%r)" % (self.__class__.__name__, self._store, self.deleted_tags, self.length, self.images)

    def __str__(self):
        return ("store: %r\ndeleted: %r\nimages: %r\nlength: %r" % (self._store, self.deleted_tags, [str(img) for img in self.images], self.length))


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

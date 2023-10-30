# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012-2014, 2018, 2020 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2022 Laurent Monin
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 Xincognito10
# Copyright (C) 2020 Gabriel Ferreira
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2022 Bob Swift
# Copyright (C) 2022 skelly37
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


from collections import namedtuple
from collections.abc import (
    Iterable,
    MutableMapping,
)
from functools import partial

from PyQt6.QtCore import QObject

from picard.config import get_config
from picard.mbjson import (
    artist_credit_from_node,
    get_score,
)
from picard.plugin import (
    PluginFunctions,
    PluginPriority,
)
from picard.similarity import similarity2
from picard.util import (
    ReadWriteLockContext,
    extract_year_from_date,
    linear_combination_of_weights,
)
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

SimMatchTrack = namedtuple('SimMatchTrack', 'similarity releasegroup release track')
SimMatchRelease = namedtuple('SimMatchRelease', 'similarity release')


def weights_from_release_type_scores(parts, release, release_type_scores,
                                     weight_release_type=1):
    # This function generates a score that determines how likely this release will be selected in a lookup.
    # The score goes from 0 to 1 with 1 being the most likely to be chosen and 0 the least likely
    # This score is based on the preferences of release-types found in this release
    # This algorithm works by taking the scores of the primary type (and secondary if found) and averages them
    # If no types are found, it is set to the score of the 'Other' type or 0.5 if 'Other' doesnt exist
    # It appends (score, weight_release_type) to passed parts list

    # if our preference is zero for the release_type, force to never return this recording
    # by using a large zero weight. This means it only gets picked if there are no others at all.
    skip_release = False

    type_scores = dict(release_type_scores)
    score = 0.0
    other_score = type_scores.get('Other', 0.5)
    if 'release-group' in release and 'primary-type' in release['release-group']:
        types_found = [release['release-group']['primary-type']]
        if 'secondary-types' in release['release-group']:
            types_found += release['release-group']['secondary-types']
        for release_type in types_found:
            type_score = type_scores.get(release_type, other_score)
            if type_score == 0:
                skip_release = True
            score += type_score
        score /= len(types_found)
    else:
        score = other_score

    if skip_release:
        parts.append((0, 9999))
    else:
        parts.append((score, weight_release_type))


def weights_from_preferred_countries(parts, release,
                                     preferred_countries,
                                     weight):
    total_countries = len(preferred_countries)
    if total_countries:
        score = 0.0
        if "country" in release:
            try:
                i = preferred_countries.index(release['country'])
                score = float(total_countries - i) / float(total_countries)
            except ValueError:
                pass
        parts.append((score, weight))


def weights_from_preferred_formats(parts, release, preferred_formats, weight):
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
        parts.append((score, weight))


def trackcount_score(actual, expected):
    return 0.0 if actual > expected else 0.3 if actual < expected else 1.0


class Metadata(MutableMapping):

    """List of metadata items with dict-like access."""

    __weights = [
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
        ('discnumber', 5),
        ('totaldiscs', 4),
    ]

    __date_match_factors = {
        'exact': 1.00,
        'year': 0.95,
        'close_year': 0.85,
        'exists_vs_null': 0.65,
        'no_release_date': 0.25,
        'differed': 0.0
    }

    multi_valued_joiner = MULTI_VALUED_JOINER

    def __init__(self, *args, deleted_tags=None, images=None, length=None, **kwargs):
        self._lock = ReadWriteLockContext()
        self._store = dict()
        self.deleted_tags = set()
        self.length = 0
        self.images = ImageList()
        self.has_common_images = True

        if args or kwargs:
            self.update(*args, **kwargs)
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

    @staticmethod
    def length_score(a, b):
        return (1.0 - min(abs(a - b),
                LENGTH_SCORE_THRES_MS) / float(LENGTH_SCORE_THRES_MS))

    def compare(self, other, ignored=None):
        parts = []
        if ignored is None:
            ignored = []

        with self._lock.lock_for_read():
            if self.length and other.length and '~length' not in ignored:
                score = self.length_score(self.length, other.length)
                parts.append((score, 8))

            for name, weight in self.__weights:
                if name in ignored:
                    continue
                a = self[name]
                b = other[name]
                if a and b:
                    if name in {'tracknumber', 'totaltracks', 'discnumber', 'totaldiscs'}:
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
        sim = linear_combination_of_weights(parts) * get_score(release)
        return SimMatchRelease(similarity=sim, release=release)

    def compare_to_release_parts(self, release, weights):
        parts = []

        with self._lock.lock_for_read():
            if 'album' in self and 'album' in weights:
                b = release['title']
                parts.append((similarity2(self['album'], b), weights['album']))

            if 'albumartist' in self and 'albumartist' in weights:
                a = self['albumartist']
                b = artist_credit_from_node(release['artist-credit'])[0]
                parts.append((similarity2(a, b), weights['albumartist']))

            if 'totaltracks' in weights:
                try:
                    a = int(self['totaltracks'])
                    if 'media' in release:
                        score = 0.0
                        for media in release['media']:
                            b = media.get('track-count', 0)
                            score = max(score, trackcount_score(a, b))
                            if score == 1.0:
                                break
                    else:
                        b = release['track-count']
                        score = trackcount_score(a, b)
                    parts.append((score, weights['totaltracks']))
                except (ValueError, KeyError):
                    pass

            if 'totalalbumtracks' in weights:
                try:
                    a = int(self['~totalalbumtracks'] or self['totaltracks'])
                    b = release['track-count']
                    score = trackcount_score(a, b)
                    parts.append((score, weights['totalalbumtracks']))
                except (ValueError, KeyError):
                    pass

            # Date Logic
            date_match_factor = 0.0
            if 'date' in weights:
                if 'date' in release and release['date'] != '':
                    release_date = release['date']
                    if 'date' in self:
                        metadata_date = self['date']
                        if release_date == metadata_date:
                            # release has a date and it matches what our metadata had exactly.
                            date_match_factor = self.__date_match_factors['exact']
                        else:
                            release_year = extract_year_from_date(release_date)
                            if release_year is not None:
                                metadata_year = extract_year_from_date(metadata_date)
                                if metadata_year is not None:
                                    if release_year == metadata_year:
                                        # release has a date and it matches what our metadata had for year exactly.
                                        date_match_factor = self.__date_match_factors['year']
                                    elif abs(release_year - metadata_year) <= 2:
                                        # release has a date and it matches what our metadata had closely (year +/- 2).
                                        date_match_factor = self.__date_match_factors['close_year']
                                    else:
                                        # release has a date but it does not match ours (all else equal,
                                        # its better to have an unknown date than a wrong date, since
                                        # the unknown could actually be correct)
                                        date_match_factor = self.__date_match_factors['differed']
                    else:
                        # release has a date but we don't have one (all else equal, we prefer
                        # tracks that have non-blank date values)
                        date_match_factor = self.__date_match_factors['exists_vs_null']
                else:
                    # release has a no date (all else equal, we don't prefer this
                    # release since its date is missing)
                    date_match_factor = self.__date_match_factors['no_release_date']

                parts.append((date_match_factor, weights['date']))

        config = get_config()
        if 'releasecountry' in weights:
            weights_from_preferred_countries(parts, release,
                                             config.setting['preferred_release_countries'],
                                             weights['releasecountry'])

        if 'format' in weights:
            weights_from_preferred_formats(parts, release,
                                           config.setting['preferred_release_formats'],
                                           weights['format'])

        if 'releasetype' in weights:
            weights_from_release_type_scores(parts, release,
                                             config.setting['release_type_scores'],
                                             weights['releasetype'])

        rg = QObject.tagger.get_release_group_by_id(release['release-group']['id'])
        if release['id'] in rg.loaded_albums:
            parts.append((1.0, 6))

        return parts

    def compare_to_track(self, track, weights):
        parts = []
        releases = []

        with self._lock.lock_for_read():
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

            if 'isvideo' in weights:
                metadata_is_video = self['~video'] == '1'
                track_is_video = bool(track.get('video'))
                score = 1 if metadata_is_video == track_is_video else 0
                parts.append((score, weights['isvideo']))

            if "releases" in track:
                releases = track['releases']

            search_score = get_score(track)
            if not releases:
                sim = linear_combination_of_weights(parts) * search_score
                return SimMatchTrack(similarity=sim, releasegroup=None, release=None, track=track)

        result = SimMatchTrack(similarity=-1, releasegroup=None, release=None, track=None)
        for release in releases:
            release_parts = self.compare_to_release_parts(release, weights)
            sim = linear_combination_of_weights(parts + release_parts) * search_score
            if sim > result.similarity:
                rg = release['release-group'] if "release-group" in release else None
                result = SimMatchTrack(similarity=sim, releasegroup=rg, release=release, track=track)
        return result

    def copy(self, other, copy_images=True):
        self.clear()
        with self._lock.lock_for_write():
            self._update_from_metadata(other, copy_images)

    def update(self, *args, **kwargs):
        with self._lock.lock_for_write():
            one_arg = len(args) == 1
            if one_arg and (isinstance(args[0], self.__class__) or isinstance(args[0], MultiMetadataProxy)):
                self._update_from_metadata(args[0])
            elif one_arg and isinstance(args[0], MutableMapping):
                # update from MutableMapping (ie. dict)
                for k, v in args[0].items():
                    self._set(k, v)
            elif args or kwargs:
                # update from a dict-like constructor parameters
                for k, v in dict(*args, **kwargs).items():
                    self._set(k, v)
            else:
                # no argument, raise TypeError to mimic dict.update()
                raise TypeError("descriptor 'update' of '%s' object needs an argument" % self.__class__.__name__)

    def diff(self, other):
        """Returns a new Metadata object with only the tags that changed in self compared to other"""
        with self._lock.lock_for_read():
            m = Metadata()
            for tag, values in self.rawitems():
                other_values = other.getall(tag)
                if other_values != values:
                    m[tag] = values
            m.deleted_tags = self.deleted_tags - other.deleted_tags
            return m

    def _update_from_metadata(self, other, copy_images=True):
        for k, v in other.rawitems():
            self._set(k, v[:])

        for tag in other.deleted_tags:
            self._del(tag)

        if copy_images and other.images:
            self.images = other.images.copy()
        if other.length:
            self.length = other.length

    def clear(self):
        with self._lock.lock_for_write():
            self._store.clear()
            self.images = ImageList()
            self.length = 0
            self.clear_deleted()

    def clear_deleted(self):
        self.deleted_tags = set()

    @staticmethod
    def normalize_tag(name):
        return name.rstrip(':')

    def getall(self, name):
        with self._lock.lock_for_read():
            return self._store.get(self.normalize_tag(name), [])

    def getraw(self, name):
        with self._lock.lock_for_read():
            return self._store[self.normalize_tag(name)]

    def get(self, key, default=None):
        with self._lock.lock_for_read():
            values = self._store.get(self.normalize_tag(key), None)
            if values:
                return self.multi_valued_joiner.join(values)
            else:
                return default

    def __getitem__(self, name):
        return self.get(name, '')

    def _set(self, name, values):
        name = self.normalize_tag(name)
        if isinstance(values, str) or not isinstance(values, Iterable):
            values = [values]
        values = [str(value) for value in values if value or value == 0 or value == '']
        # Remove if there is only a single empty or blank element.
        if values and (len(values) > 1 or values[0]):
            self._store[name] = values
            self.deleted_tags.discard(name)
        elif name in self._store:
            self._del(name)

    def set(self, name, values):
        with self._lock.lock_for_write():
            self._set(name, values)

    def __setitem__(self, name, values):
        self.set(name, values)

    def __contains__(self, name):
        with self._lock.lock_for_read():
            return self._store.__contains__(self.normalize_tag(name))

    def _del(self, name):
        name = self.normalize_tag(name)
        try:
            del self._store[name]
        except KeyError:
            pass
        finally:
            self.deleted_tags.add(name)

    def __delitem__(self, name):
        with self._lock.lock_for_write():
            self._del(name)

    def delete(self, name):
        del self[self.normalize_tag(name)]

    def add(self, name, value):
        if value or value == 0:
            with self._lock.lock_for_write():
                name = self.normalize_tag(name)
                self._store.setdefault(name, []).append(str(value))
                self.deleted_tags.discard(name)

    def add_unique(self, name, value):
        name = self.normalize_tag(name)
        if value not in self.getall(name):
            self.add(name, value)

    def unset(self, name):
        """Removes a tag from the metadata, but does not mark it for deletion.

        Args:
            name: name of the tag to unset
        """
        with self._lock.lock_for_write():
            name = self.normalize_tag(name)
            try:
                del self._store[name]
            except KeyError:
                pass

    def __iter__(self):
        with self._lock.lock_for_read():
            return iter(self._store)

    def items(self):
        with self._lock.lock_for_read():
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
        with self._lock.lock_for_write():
            for name, values in list(self.rawitems()):
                if name not in PRESERVED_TAGS:
                    self._set(name, (func(value) for value in values))

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
        self.apply_func(str.strip)

    def __repr__(self):
        return "%s(%r, deleted_tags=%r, length=%r, images=%r)" % (self.__class__.__name__, self._store, self.deleted_tags, self.length, self.images)

    def __str__(self):
        return ("store: %r\ndeleted: %r\nimages: %r\nlength: %r" % (self._store, self.deleted_tags, [str(img) for img in self.images], self.length))


class MultiMetadataProxy:
    """
    Wraps a writable Metadata object together with another
    readonly Metadata object.

    Changes are written to the writable object, while values are
    read from both the writable and the readonly object (with the writable
    object taking precedence). The use case is to provide access to Metadata
    values without making them part of the actual Metadata. E.g. allow track
    metadata to use file specific metadata, without making it actually part
    of the track.
    """
    WRITE_METHODS = [
        'add_unique',
        'add',
        'apply_func',
        'clear_deleted',
        'clear',
        'copy',
        'delete',
        'pop',
        'set',
        'strip_whitespace',
        'unset',
        'update',
    ]

    def __init__(self, metadata, *readonly_metadata):
        self.metadata = metadata
        self.combined_metadata = Metadata()
        for m in reversed(readonly_metadata):
            self.combined_metadata.update(m)
        self.combined_metadata.update(metadata)

    def __getattr__(self, name):
        if name in self.WRITE_METHODS:
            return partial(self.__write, name)
        else:
            attribute = self.combined_metadata.__getattribute__(name)
            if callable(attribute):
                return partial(self.__read, name)
            else:
                return attribute

    def __setattr__(self, name, value):
        if name in {'metadata', 'combined_metadata'}:
            super().__setattr__(name, value)
        else:
            self.metadata.__setattr__(name, value)
            self.combined_metadata.__setattr__(name, value)

    def __write(self, name, *args, **kwargs):
        func1 = self.metadata.__getattribute__(name)
        func2 = self.combined_metadata.__getattribute__(name)
        func1(*args, **kwargs)
        return func2(*args, **kwargs)

    def __read(self, name, *args, **kwargs):
        func = self.combined_metadata.__getattribute__(name)
        return func(*args, **kwargs)

    def __getitem__(self, name):
        return self.__read('__getitem__', name)

    def __setitem__(self, name, values):
        return self.__write('__setitem__', name, values)

    def __delitem__(self, name):
        return self.__write('__delitem__', name)

    def __iter__(self):
        return self.__read('__iter__')

    def __len__(self):
        return self.__read('__len__')

    def __contains__(self, name):
        return self.__read('__contains__', name)

    def __repr__(self):
        return self.__read('__repr__')


_album_metadata_processors = PluginFunctions(label='album_metadata_processors')
_track_metadata_processors = PluginFunctions(label='track_metadata_processors')


def register_album_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new album-level metadata processor."""
    _album_metadata_processors.register(function.__module__, function, priority)


def register_track_metadata_processor(function, priority=PluginPriority.NORMAL):
    """Registers new track-level metadata processor."""
    _track_metadata_processors.register(function.__module__, function, priority)


def run_album_metadata_processors(album_object, metadata, release):
    _album_metadata_processors.run(album_object, metadata, release)


def run_track_metadata_processors(album_object, metadata, track, release=None):
    _track_metadata_processors.run(album_object, metadata, track, release)

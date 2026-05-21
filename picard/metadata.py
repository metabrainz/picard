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
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
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
# Copyright (C) 2024 x11x
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


from collections.abc import (
    Callable,
    Iterable,
    MutableMapping,
)
from functools import partial
from typing import TYPE_CHECKING

from PyQt6 import QtCore

from picard.config import get_config
from picard.matching import (
    LENGTH_SCORE_THRESHOLD_MS,
    ReleaseMatchParts,
    SimMatchRelease,
    SimMatchTrack,
    TieredWeights,
    _catno_label_score,
    _date_score,
    _get_weighted_release_parts,
    _isrcs_score,
    _trackcount_score,
    weights_from_preferred_countries,
    weights_from_preferred_formats,
    weights_from_release_type_scores,
)
from picard.mbjson import (
    artist_credit_from_node,
    get_score,
)
from picard.plugin import PluginFunctions
from picard.similarity import similarity2
from picard.tags import preserved_tag_names
from picard.util import (
    ReadWriteLockContext,
    compare_barcodes,
    linear_combination_of_weights,
)
from picard.util.imagelist import ImageList


if TYPE_CHECKING:
    from picard.coverart.image import CoverArtImage

MULTI_VALUED_JOINER = '; '


class Metadata(MutableMapping[str, str | list[str] | None]):
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

    multi_valued_joiner = MULTI_VALUED_JOINER

    def __init__(
        self,
        *args,
        deleted_tags: Iterable[str] | None = None,
        images: Iterable['CoverArtImage'] | None = None,
        length: int | None = None,
        **kwargs,
    ):
        self._lock = ReadWriteLockContext()
        self._store: dict[str, list[str]] = dict()
        self.deleted_tags: set[str] = set()
        self.images: ImageList = ImageList()
        self.has_common_images = True

        if length is not None:
            self.length = length
        else:
            self.length = 0
        if args or kwargs:
            self.update(*args, **kwargs)
        if images is not None:
            for image in images:
                self.images.append(image)
        if deleted_tags is not None:
            for tag in deleted_tags:
                del self[tag]

    def __bool__(self):
        return bool(len(self))

    def __len__(self):
        return len(self._store) + len(self.images)

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value: int):
        length = int(value)
        if length < 0:
            raise ValueError("negative value: %d" % length)
        self._length = length

    @staticmethod
    def length_score(a: int, b: int):
        if a is None or b is None:
            return 0.0
        return 1.0 - min(abs(a - b), LENGTH_SCORE_THRESHOLD_MS) / float(LENGTH_SCORE_THRESHOLD_MS)

    def compare(self, other: 'Metadata', ignored: Iterable[str] | None = None):
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
                elif a and name in other.deleted_tags or b and name in self.deleted_tags:
                    parts.append((0, weight))

        return linear_combination_of_weights(parts)

    def compare_to_release(self, release: dict, weights: TieredWeights):
        """
        Compare metadata to a MusicBrainz release. Produces a probability as a
        linear combination of weights that the metadata matches a certain album.
        """
        config = get_config()
        parts = self.compare_to_release_parts(release, weights, config)
        sim = parts.combine_tiers() * get_score(release)
        return SimMatchRelease(similarity=sim, release=release)

    def compare_to_release_parts(self, release: dict, weights: TieredWeights, config=None):
        result = ReleaseMatchParts()
        id_w = weights.get('identifiers', {})
        sim_w = weights.get('similarity', {})
        pref_w = weights.get('preferences', {})

        # Tier 1: Identifiers — exact matches, cheap to compute
        if 'barcode' in id_w:
            file_barcode = self.get('barcode', '')
            if file_barcode and 'barcode' in release:
                release_barcode = release['barcode']
                if compare_barcodes(file_barcode, release_barcode):
                    result.identifiers.append((1.0, id_w['barcode']))
                else:
                    result.identifiers.append((0.0, id_w['barcode']))

        if 'catno' in id_w:
            file_catno = self.get('catalognumber', '')
            if file_catno and 'label-info' in release:
                release_label_info = release['label-info']
                if release_label_info:
                    file_label = self.get('label', '')
                    score = _catno_label_score(file_catno, file_label, release_label_info)
                    result.identifiers.append((score, id_w['catno']))

        if 'release-group' in release:
            tagger = QtCore.QCoreApplication.instance()
            if tagger is not None:
                rg = tagger.get_release_group_by_id(release['release-group']['id'])  # type: ignore[attr-defined]
                if release['id'] in rg.loaded_albums:
                    result.identifiers.append((1.0, 6))

        # Tier 2: Similarity — fuzzy matching core
        with self._lock.lock_for_read():
            if 'album' in self and 'album' in sim_w:
                b = release['title']
                result.similarity.append((similarity2(self['album'], b), sim_w['album']))

            if 'albumartist' in self and 'albumartist' in sim_w:
                a = self['albumartist']
                b = artist_credit_from_node(release['artist-credit']).name
                result.similarity.append((similarity2(a, b), sim_w['albumartist']))

            if 'totaltracks' in sim_w:
                try:
                    a = int(self['totaltracks'])
                    if 'media' in release:
                        score = 0.0
                        for media in release['media']:
                            b = media.get('track-count', 0)
                            score = max(score, _trackcount_score(a, b))
                            if score == 1.0:
                                break
                    else:
                        b = release['track-count']
                        score = _trackcount_score(a, b)
                    result.similarity.append((score, sim_w['totaltracks']))
                except (ValueError, KeyError):
                    pass

            if 'totalalbumtracks' in sim_w:
                try:
                    a = int(self['~totalalbumtracks'] or self['totaltracks'])
                    if 'track-count' in release:
                        b = release['track-count']
                    else:
                        b = sum(m.get('track-count', 0) for m in release.get('media', []))
                    score = _trackcount_score(a, b)
                    result.similarity.append((score, sim_w['totalalbumtracks']))
                except (ValueError, KeyError):
                    pass

            # Date matching
            if 'date' in sim_w:
                result.similarity.append((_date_score(release, self), sim_w['date']))

        # Tier 3: Preferences — tie-breaking discriminators
        if config is None:
            config = get_config()
        if 'releasecountry' in pref_w:
            weights_from_preferred_countries(
                result.preferences,
                release,
                config.setting['preferred_release_countries'],
                pref_w['releasecountry'],
            )

        if 'format' in pref_w:
            weights_from_preferred_formats(
                result.preferences,
                release,
                config.setting['preferred_release_formats'],
                pref_w['format'],
            )

        if 'releasetype' in pref_w:
            weights_from_release_type_scores(
                result.preferences,
                release,
                config.setting['release_type_scores'],
                pref_w['releasetype'],
            )

        return result

    def compare_to_track(self, track: dict, weights: TieredWeights):
        track_parts = ReleaseMatchParts()
        releases = []
        id_w = weights.get('identifiers', {})
        sim_w = weights.get('similarity', {})
        pref_w = weights.get('preferences', {})

        with self._lock.lock_for_read():
            # Tier 1: ISRC — recording-level identifier
            if 'isrc' in id_w:
                file_isrcs = self.getall('isrc')
                if file_isrcs:
                    recording = track.get('recording', track)
                    track_isrcs = recording.get('isrcs', [])
                    score = _isrcs_score(file_isrcs, track_isrcs)
                    track_parts.identifiers.append((score, id_w['isrc']))

            # Track-level similarity signals
            if 'title' in self and 'title' in sim_w:
                a = self['title']
                b = track.get('title', '')
                track_parts.similarity.append((similarity2(a, b), sim_w["title"]))

            if 'artist' in self and 'artist' in sim_w:
                a = self['artist']
                artist_credits = track.get('artist-credit', [])
                b = artist_credit_from_node(artist_credits).name
                track_parts.similarity.append((similarity2(a, b), sim_w["artist"]))

            a = self.length
            if a > 0 and 'length' in track and 'length' in sim_w:
                b = track['length']
                score = self.length_score(a, b)
                track_parts.similarity.append((score, sim_w["length"]))

            if 'isvideo' in pref_w:
                metadata_is_video = self['~video'] == '1'
                track_is_video = bool(track.get('video'))
                score = 1 if metadata_is_video == track_is_video else 0
                track_parts.preferences.append((score, pref_w['isvideo']))

            if "releases" in track:
                releases = track['releases']

            search_score = get_score(track)
            if not releases:
                config = get_config()
                score = dict(config.setting['release_type_scores']).get('Other', 0.5)
                release_parts = _get_weighted_release_parts(weights, score)
                track_parts = track_parts.merged_with(release_parts)
                sim = track_parts.combine_tiers() * search_score
                return SimMatchTrack(similarity=sim, releasegroup=None, release=None, track=track)

        result = SimMatchTrack(similarity=-1, releasegroup=None, release=None, track=None)
        config = get_config()
        for release in releases:
            release_parts = self.compare_to_release_parts(release, weights, config)
            combined = track_parts.merged_with(release_parts)
            sim = combined.combine_tiers() * search_score
            if sim > result.similarity:
                rg = release['release-group'] if "release-group" in release else None
                result = SimMatchTrack(similarity=sim, releasegroup=rg, release=release, track=track)
        return result

    def copy(self, other: 'Metadata', copy_images=True):
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

    def diff(self, other: 'Metadata'):
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
    def normalize_tag(name: str):
        return name.rstrip(':')

    def getall(self, name: str) -> list[str]:
        with self._lock.lock_for_read():
            return self._store.get(self.normalize_tag(name), [])

    def getraw(self, name: str):
        with self._lock.lock_for_read():
            return self._store[self.normalize_tag(name)]

    def get(self, name: str, default=None) -> str | None:
        with self._lock.lock_for_read():
            values = self._store.get(self.normalize_tag(name), None)
            if values:
                return self.multi_valued_joiner.join(values)
            else:
                return default

    def __getitem__(self, name: str) -> str:
        return self.get(name) or ''

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

    def set(self, name: str, values: str | list[str]):
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

    def __delitem__(self, name: str):
        with self._lock.lock_for_write():
            self._del(name)

    def delete(self, name: str):
        del self[self.normalize_tag(name)]

    def add(self, name: str, value: str):
        if value or value == 0:
            with self._lock.lock_for_write():
                name = self.normalize_tag(name)
                self._store.setdefault(name, []).append(str(value))
                self.deleted_tags.discard(name)

    def add_unique(self, name: str, value: str):
        name = self.normalize_tag(name)
        if value not in self.getall(name):
            self.add(name, value)

    def unset(self, name: str):
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
            yield from self._store

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

    def apply_func(self, func: Callable[[str], str]):
        with self._lock.lock_for_write():
            default_preserved_tags = set(preserved_tag_names())
            for name, values in list(self.rawitems()):
                if name not in default_preserved_tags:
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
        return "%s(%r, deleted_tags=%r, length=%r, images=%r)" % (
            self.__class__.__name__,
            self._store,
            self.deleted_tags,
            self.length,
            self.images,
        )

    def __str__(self):
        return "store: %r\ndeleted: %r\nimages: %r\nlength: %r" % (
            self._store,
            self.deleted_tags,
            [str(img) for img in self.images],
            self.length,
        )

    def add_images(self, added_images):
        if not added_images:
            return False

        current_images = set(self.images)
        if added_images.isdisjoint(current_images):
            self.images = ImageList(current_images.union(added_images))
            self.has_common_images = False
            return True

        return False

    def remove_images(self, sources, removed_images):
        """Removes `removed_images` from `images`, but only if they are not included in `sources`.

        Args:
            sources: List of source `Metadata` objects
            removed_images: Set of `CoverArt` to removed

        Returns:
            True if self.images was modified, False else
        """
        if not self.images or not removed_images:
            return False

        if not sources:
            self.images = ImageList()
            self.has_common_images = True
            return True

        current_images = set(self.images)

        if self.has_common_images and current_images == removed_images:
            return False

        common_images = True  # True, if all children share the same images
        previous_images = None

        # Iterate over all sources and check whether the images proposed to be
        # removed are used in any sources. Images used in existing sources
        # must not be removed.
        for source_metadata in sources:
            source_images = set(source_metadata.images)
            if previous_images and common_images and previous_images != source_images:
                common_images = False
            previous_images = set(source_metadata.images)  # Remember for next iteration
            removed_images = removed_images.difference(source_images)
            if not removed_images and not common_images:
                return False  # No images left to remove, abort immediately

        new_images = current_images.difference(removed_images)
        self.images = ImageList(new_images)
        self.has_common_images = common_images
        return True


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


album_metadata_processors = PluginFunctions(label='album_metadata_processors')
track_metadata_processors = PluginFunctions(label='track_metadata_processors')


def run_album_metadata_processors(album_object, metadata, release_node):
    album_metadata_processors.run(album_object, metadata, release_node)


def run_track_metadata_processors(track_object, metadata, track_node, release_node=None):
    track_metadata_processors.run(track_object, metadata, track_node, release_node)

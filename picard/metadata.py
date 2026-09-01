# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009, 2015, 2018-2023, 2025-2026 Philipp Wolfer
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012 Johannes Weißl
# Copyright (C) 2012-2014, 2018, 2020 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2026 Laurent Monin
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2018 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 Xincognito10
# Copyright (C) 2020 Gabriel Ferreira
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2022 skelly37
# Copyright (C) 2022, 2025 Bob Swift
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from collections.abc import (
    Callable,
    Iterable,
    MutableMapping,
)
from functools import partial
from typing import TYPE_CHECKING

from picard.matching import length_score
from picard.plugin import PluginFunctions
from picard.similarity import similarity2
from picard.tags import preserved_tag_names
from picard.util import (
    ReadWriteLockContext,
    linear_combination_of_weights,
)
from picard.util.imagelist import ImageList


if TYPE_CHECKING:
    from picard.album import Album
    from picard.coverart.image import CoverArtImage
    from picard.track import Track

MULTI_VALUED_JOINER = '; '


class Metadata(MutableMapping[str, str | list[str] | None]):
    """List of metadata items with dict-like access."""

    __weights = (
        ('title', 22),
        ('artist', 6),
        ('album', 12),
        ('tracknumber', 6),
        ('totaltracks', 5),
        ('discnumber', 5),
        ('totaldiscs', 4),
    )

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
        # Values are stored either as a bare ``str`` (single value) or a
        # ``list[str]`` (multiple values) to save memory on the common
        # single-valued case. Use the accessors (getall/getraw/rawitems), which
        # always present values as lists.
        self._store: dict[str, str | list[str]] = dict()
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

    def compare(self, other: 'Metadata', ignored: Iterable[str] | None = None):
        parts = []
        if ignored is None:
            ignored = []

        with self._lock.lock_for_read():
            if self.length and other.length and '~length' not in ignored:
                score = length_score(self.length, other.length)
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
        other_store = getattr(other, '_store', None)
        if other_store is not None and type(other) is type(self):
            # Fast path for Metadata->Metadata: copy the internal store
            # directly. Bare str values are immutable so can be shared; only
            # multi-value lists need a shallow copy. This avoids the
            # list-normalization allocations of rawitems()/_set().
            store = self._store
            for k, v in other_store.items():
                store[k] = v[:] if type(v) is list else v
            # The tags we just copied are now set, so drop them from the list
            # of deleted tags (mirrors the deleted_tags.discard() that _set()
            # does on the slow path below).
            self.deleted_tags.difference_update(other_store.keys())
        else:
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

    @staticmethod
    def _as_list(stored) -> list[str]:
        """Present a stored entry (bare str or list) as a list of strings.

        For the bare-str case a new 1-element list is returned. For the
        multi-value case the stored list is returned as-is (not copied),
        matching the prior behavior of getall()/getraw(); no caller mutates
        the returned list in place.
        """
        if type(stored) is str:
            return [stored]
        return stored

    def getall(self, name: str) -> list[str]:
        """Return all values for a tag as a list.

        Values are presented as a list regardless of the internal storage
        (a single value is stored as a bare str, multiple as a list).
        Use this method when you need the individual values (e.g., multiple
        artists or labels). Returns an empty list if the tag is not set.
        """
        with self._lock.lock_for_read():
            stored = self._store.get(self.normalize_tag(name))
            return [] if stored is None else self._as_list(stored)

    def getraw(self, name: str):
        """Return the raw stored list for a tag, raising KeyError if missing."""
        with self._lock.lock_for_read():
            return self._as_list(self._store[self.normalize_tag(name)])

    def get(self, name: str, default=None) -> str | None:
        """Return all values joined into a single string.

        Multiple values are joined with `multi_valued_joiner` (default: "; ").
        Use `getall()` instead when you need the individual values as a list.
        Returns `default` if the tag is not set.
        """
        with self._lock.lock_for_read():
            stored = self._store.get(self.normalize_tag(name), None)
            if stored is None:
                return default
            if type(stored) is str:
                # Single value stored bare; return as-is (do not char-join).
                return stored or default
            if stored:
                return self.multi_valued_joiner.join(stored)
            return default

    def __getitem__(self, name: str) -> str:
        """Return all values joined as a string, or empty string if unset.

        Equivalent to `self.get(name) or ''`. Use `getall()` when you need
        individual values as a list.
        """
        return self.get(name) or ''

    def _set(self, name, values):
        """Store values for a tag.

        A single value is stored internally as a bare ``str`` and multiple
        values as a ``list[str]``. This avoids a one-element list wrapper for
        the common single-valued case, which is a significant per-object memory
        saving across large collections. All public accessors
        (:meth:`getall`, :meth:`getraw`, :meth:`rawitems`, :meth:`items`) still
        present values as lists, so the external contract is unchanged.
        """
        name = self.normalize_tag(name)
        if isinstance(values, str) or not isinstance(values, Iterable):
            values = [values]
        values = [str(value) for value in values if value or value == 0 or value == '']
        # Remove if there is only a single empty or blank element.
        count = len(values)
        if count and (count > 1 or values[0]):
            # Store a bare str for the single-value case to save memory.
            self._store[name] = values if count > 1 else values[0]
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

    def get_new(self, name, default=''):
        """Get a value only from the new metadata.

        On a plain Metadata object this is the same as get().
        On a MultiMetadataProxy this ignores the readonly fallback.
        Provides a consistent interface for script functions.
        """
        return self.get(name, default)

    def get_original(self, name, default=''):
        """Get a value from the original (file) metadata.

        On a plain Metadata object this is the same as get() (there is no
        separate original source).
        On a MultiMetadataProxy this reads only from the readonly fallback.
        Provides a consistent interface for script functions.
        """
        return self.get(name, default)

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
                stored = self._store.get(name)
                if stored is None:
                    # First value: store bare str.
                    self._store[name] = str(value)
                elif isinstance(stored, str):
                    # Promote single bare str to a list on second value.
                    self._store[name] = [stored, str(value)]
                else:
                    stored.append(str(value))
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
            for name, stored in self._store.items():
                if isinstance(stored, str):
                    yield name, stored
                else:
                    for value in stored:
                        yield name, value

    def rawitems(self):
        """Returns the metadata items.

        >>> m.rawitems()
        [("key1", ["value1", "value2"]), ("key2", ["value3"])]
        """
        return [(name, self._as_list(stored)) for name, stored in self._store.items()]

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

    WRITE_METHODS = (
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
    )

    def __init__(self, metadata, *readonly_metadata):
        self.metadata = metadata
        self._original_metadata = Metadata()
        for m in reversed(readonly_metadata):
            self._original_metadata.update(m)
        self.combined_metadata = Metadata()
        self.combined_metadata.update(self._original_metadata)
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
        if name in {'metadata', 'combined_metadata', '_original_metadata'}:
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

    def get_new(self, name, default=''):
        """Get a value only from the new (writable) metadata, ignoring fallback.

        This allows distinguishing values that were set by MusicBrainz/scripts
        from values that only exist in the readonly fallback (file metadata).

        Returns:
            The value from the new metadata, or default if not present.
        """
        return self.metadata.get(name, default)

    def get_original(self, name, default=''):
        """Get a value only from the readonly (file) metadata, ignoring new metadata.

        This allows accessing the file's original tag values regardless of
        what MusicBrainz or scripts have set.

        Returns:
            The value from the readonly file metadata, or default if not present.
        """
        return self._original_metadata.get(name, default)

    def __repr__(self):
        return self.__read('__repr__')


album_metadata_processors = PluginFunctions[['Album', Metadata, dict], None](label='album_metadata_processors')
track_metadata_processors = PluginFunctions[['Track', Metadata, dict, dict | None], None](
    label='track_metadata_processors'
)


def run_album_metadata_processors(album_object: 'Album', metadata: Metadata, release_node: dict):
    album_metadata_processors.run(album_object, metadata, release_node)


def run_track_metadata_processors(
    track_object: 'Track', metadata: Metadata, track_node: dict, release_node: dict | None = None
):
    track_metadata_processors.run(track_object, metadata, track_node, release_node)

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010, 2018, 2020-2022, 2024-2025 Philipp Wolfer
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Rakim Middya
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


from collections import (
    Counter,
    UserList,
)
from collections.abc import Iterable

from PyQt6 import QtCore

from picard import log
from picard.config import get_config
from picard.i18n import ngettext
from picard.metadata import Metadata
from picard.util import IgnoreUpdatesContext
from picard.util.imagelist import ImageList


class Item:
    def __init__(self):
        self.ui_item = None

    @property
    def can_save(self) -> bool:
        """Return if this object can be saved."""
        return False

    @property
    def can_remove(self) -> bool:
        """Return if this object can be removed."""
        return False

    @property
    def can_edit_tags(self) -> bool:
        """Return if this object supports tag editing."""
        return False

    @property
    def can_analyze(self) -> bool:
        """Return if this object can be fingerprinted."""
        return False

    @property
    def can_autotag(self) -> bool:
        """Return if this object can be autotagged."""
        return False

    @property
    def can_refresh(self) -> bool:
        """Return if this object can be refreshed."""
        return False

    @property
    def can_view_info(self) -> bool:
        return False

    @property
    def can_submit(self) -> bool:
        """Return True if this object can be submitted to MusicBrainz.org."""
        return False

    @property
    def can_show_coverart(self) -> bool:
        """Return if this object supports cover art."""
        return self.can_edit_tags

    @property
    def can_browser_lookup(self) -> bool:
        return True

    @property
    def is_album_like(self) -> bool:
        return False

    @property
    def can_link_fingerprint(self) -> bool:
        """Return True if this item can provide a recording ID for linking to AcoustID."""
        return False

    @property
    def is_permanently_hidden(self) -> bool:
        """Indicates, that this item should be considered hidden.

        By default items are visible, but can be overridden by subclasses.
        """
        return False

    def load(self, priority=False, refresh=False):
        pass

    @property
    def tracknumber(self):
        """The track number as an int."""
        return self._track_or_disc_number('tracknumber')

    @property
    def discnumber(self):
        """The disc number as an int."""
        return self._track_or_disc_number('discnumber')

    def _track_or_disc_number(self, field):
        """Extract tracknumber or discnumber as int, defaults to 0."""
        try:
            return int(self.metadata.get(field, '0').split('/')[0])
        except ValueError:
            return 0

    @property
    def errors(self) -> list[str]:
        if not hasattr(self, '_errors'):
            self._errors = []
        return self._errors

    def error_append(self, msg: str):
        log.error("%r: %s", self, msg)
        self.errors.append(msg)

    def clear_errors(self):
        self._errors = []

    @property
    def _images(self):
        return self.metadata.images

    def cover_art_description(self):
        """Return the number of cover art images for display in the UI

        Returns:
            A string with the cover art image count, or empty string if not applicable
        """
        if not self.can_show_coverart:
            return ''

        return str(len(self._images))

    def cover_art_description_detailed(self):
        """Return  a detailed text about the images and whether they are the same across
           all tracks for images in `images` for display in the UI

        Returns:
            A string explaining the cover art image count.
        """
        if not self.can_show_coverart:
            return ''

        number_of_images = len(self._images)
        if getattr(self, 'has_common_images', True):
            return ngettext("%i image", "%i images", number_of_images) % number_of_images
        else:
            return (
                ngettext("%i image not in all tracks", "%i different images among tracks", number_of_images)
                % number_of_images
            )

    def cover_art_dimensions(self) -> str:
        front_image = self.metadata.images.get_front_image()
        if front_image:
            return front_image.dimensions_as_string()
        return ''


class ImageListState:
    def __init__(self):
        self.images = {}
        self.has_common_images = True
        self.first_obj = True

    def process_images(self, src_obj_metadata):
        src_dict = src_obj_metadata.images.hash_dict()
        prev_len = len(self.images)
        self.images.update(src_dict)
        if len(self.images) != prev_len:
            if not self.first_obj:
                self.has_common_images = False
        if self.first_obj:
            self.first_obj = False


class MetadataItem(QtCore.QObject, Item):
    metadata_images_changed = QtCore.pyqtSignal()

    def __init__(self, obj_id=None):
        super().__init__()
        self.id = obj_id
        self.metadata: Metadata = Metadata()
        self.orig_metadata: Metadata = Metadata()
        self.update_children_metadata_attrs = {}
        self._iter_children_items_metadata_ignore_attrs = {}
        self.suspend_metadata_images_update = IgnoreUpdatesContext()
        self._genres = Counter()
        self._folksonomy_tags = Counter()

    @property
    def tagger(self):
        return QtCore.QCoreApplication.instance()

    @tagger.setter
    def tagger(self, value):
        # We used to set tagger property in subclasses, but that's not needed anymore
        assert value == QtCore.QCoreApplication.instance()
        import inspect

        stack = inspect.stack()
        f = stack[1]
        log.warning("MetadataItem.tagger property set at %s:%d in %s", f.filename, f.lineno, f.function)

    def update_metadata_images(self):
        if not self.suspend_metadata_images_update and self.can_show_coverart:
            if self.update_metadata_images_from_children():
                self.metadata_images_changed.emit()

    def keep_original_images(self):
        with self.suspend_metadata_images_update:
            for file in list(self.files):
                if file.can_show_coverart:
                    file.keep_original_images()
        self.update_metadata_images()

    def children_metadata_items(self) -> Iterable['MetadataItem']:
        """Yield MetadataItems that are children of the current object"""
        return []

    def iter_children_items_metadata(self, metadata_attr):
        for s in self.children_metadata_items():
            if metadata_attr in s._iter_children_items_metadata_ignore_attrs:
                continue
            yield getattr(s, metadata_attr)

    @staticmethod
    def get_sources_metadata_images(sources_metadata):
        images = set()
        for s in sources_metadata:
            images = images.union(s.images)
        return images

    def remove_metadata_images_from_children(self, removed_sources):
        """Remove the images in the metadata of `removed_sources` from the metadata.

        Args:
            removed_sources: List of child objects (`Track` or `File`) which's metadata images should be removed from
        """
        changed = False

        for metadata_attr in self.update_children_metadata_attrs:
            removed_images = self.get_sources_metadata_images(getattr(s, metadata_attr) for s in removed_sources)
            sources_metadata = list(self.iter_children_items_metadata(metadata_attr))
            metadata = getattr(self, metadata_attr)
            changed |= metadata.remove_images(sources_metadata, removed_images)

        return changed

    def add_metadata_images_from_children(self, added_sources):
        """Add the images in the metadata of `added_sources` to the metadata.

        Args:
            added_sources: List of child objects (`Track` or `File`) which's metadata images should be added to current object
        """
        changed = False

        for metadata_attr in self.update_children_metadata_attrs:
            added_images = self.get_sources_metadata_images(getattr(s, metadata_attr) for s in added_sources)
            metadata = getattr(self, metadata_attr)
            changed |= metadata.add_images(added_images)

        return changed

    def update_metadata_images_from_children(self):
        """Update the metadata images of the current object based on its children.

        Based on the type of the current object, this will update `self.metadata.images` to
        represent the metadata images of all children (`Track` or `File` objects).

        This method will iterate over all children and completely rebuild
        `self.metadata.images`. Whenever possible the more specific functions
        `add_metadata_images_from_children` or `remove_metadata_images_from_children` should be used.

        Returns:
            bool: True, if images where changed, False otherwise
        """
        changed = False

        for metadata_attr in self.update_children_metadata_attrs:
            state = ImageListState()
            for src_obj_metadata in self.iter_children_items_metadata(metadata_attr):
                state.process_images(src_obj_metadata)

            updated_images = ImageList(state.images.values())
            metadata = getattr(self, metadata_attr)
            changed |= set(updated_images.hash_dict()) != set(metadata.images.hash_dict())
            metadata.images = updated_images
            metadata.has_common_images = state.has_common_images

        return changed

    @property
    def genres(self) -> Counter[str]:
        return self._genres

    def add_genre(self, name: str, count: int):
        if name:
            self._genres[name] += count

    @property
    def folksonomy_tags(self) -> Counter[str]:
        return self._folksonomy_tags

    def add_folksonomy_tag(self, name: str, count: int):
        if name:
            self._folksonomy_tags[name] += count

    @staticmethod
    def set_genre_inc_params(inc, config=None):
        require_authentication = False
        config = config or get_config()
        if config.setting['use_genres']:
            if config.setting['only_my_genres']:
                require_authentication = True
                inc |= {'user-tags', 'user-genres'}
            else:
                inc |= {'tags', 'genres'}
        return require_authentication


class ListOfMetadataItems(UserList):
    """
    UserList with length attribute equals to the sum of items metadata lengths.
    """

    def __init__(self, initlist=None):
        self._dirty = True
        super().__init__(initlist)

    def __setitem__(self, i, item):
        self._dirty = True
        super().__setitem__(i, item)

    def __delitem__(self, i):
        self._dirty = True
        super().__delitem__(i)

    def __copy__(self):
        self._dirty = True
        return super().__copy__()

    def append(self, item):
        self._dirty = True
        super().append(item)

    def insert(self, i, item):
        self._dirty = True
        super().insert(i, item)

    def pop(self, i=-1):
        self._dirty = True
        return super().pop(i)

    def remove(self, item):
        self._dirty = True
        super().remove(item)

    def clear(self):
        self._dirty = True
        super().clear()

    def extend(self, other):
        self._dirty = True
        super().extend(other)

    def __iadd__(self, other):  # For += operator
        self._dirty = True
        super().__iadd__(other)
        return self  # In-place operations should return self

    def __imul__(self, other):  # For *= operator
        self._dirty = True
        super().__imul__(other)
        return self  # In-place operations should return self

    @property
    def length(self):
        if self._dirty:
            self._length = sum(item.metadata.length for item in self.data)
            self._dirty = False
        return self._length


class FileListItem(MetadataItem):
    def __init__(self, obj_id=None, files=None):
        super().__init__(obj_id)
        self.files = ListOfMetadataItems(files or [])
        self.update_children_metadata_attrs = {'metadata', 'orig_metadata'}

    def iterfiles(self, save=False):
        yield from self.files

    def children_metadata_items(self):
        yield from self.files

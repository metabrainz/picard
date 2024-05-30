# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010, 2018, 2020-2022 Philipp Wolfer
# Copyright (C) 2011-2012 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2013, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
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

from PyQt6 import QtCore

from picard import log
from picard.i18n import ngettext
from picard.metadata import Metadata
from picard.util import IgnoreUpdatesContext


class Item:

    @property
    def can_save(self):
        """Return if this object can be saved."""
        return False

    @property
    def can_remove(self):
        """Return if this object can be removed."""
        return False

    @property
    def can_edit_tags(self):
        """Return if this object supports tag editing."""
        return False

    @property
    def can_analyze(self):
        """Return if this object can be fingerprinted."""
        return False

    @property
    def can_autotag(self):
        """Return if this object can be autotagged."""
        return False

    @property
    def can_refresh(self):
        """Return if this object can be refreshed."""
        return False

    @property
    def can_view_info(self):
        return False

    @property
    def can_submit(self):
        """Return True if this object can be submitted to MusicBrainz.org."""
        return False

    @property
    def can_show_coverart(self):
        """Return if this object supports cover art."""
        return self.can_edit_tags

    @property
    def can_browser_lookup(self):
        return True

    @property
    def is_album_like(self):
        return False

    @property
    def can_link_fingerprint(self):
        """Return True if this item can provide a recording ID for linking to AcoustID."""
        return False

    def load(self, priority=False, refresh=False):
        pass

    @property
    def tracknumber(self):
        """The track number as an int."""
        try:
            return int(self.metadata['tracknumber'])
        except BaseException:
            return 0

    @property
    def discnumber(self):
        """The disc number as an int."""
        try:
            return int(self.metadata['discnumber'])
        except BaseException:
            return 0

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            self._errors = []
        return self._errors

    def error_append(self, msg):
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
            return ngettext("%i image", "%i images",
                            number_of_images) % number_of_images
        else:
            return ngettext("%i image not in all tracks", "%i different images among tracks",
                            number_of_images) % number_of_images


class MetadataItem(Item):
    metadata_images_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.metadata = Metadata()
        self.orig_metadata = Metadata()
        self.update_children_metadata_attrs = {}
        self.iter_children_items_metadata_ignore_attrs = {}
        self.suspend_metadata_images_update = IgnoreUpdatesContext()

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

    def children_metadata_items(self):
        """Yield MetadataItems that are children of the current object"""

    def iter_children_items_metadata(self, metadata_attr):
        for s in self.children_metadata_items():
            if metadata_attr in s.iter_children_items_metadata_ignore_attrs:
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
        from picard.util.imagelist import ImageList

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


class FileListItem(MetadataItem):

    def __init__(self, files=None):
        super().__init__()
        self.files = files or []
        self.update_children_metadata_attrs = {'metadata', 'orig_metadata'}

    def iterfiles(self, save=False):
        yield from self.files

    def children_metadata_items(self):
        yield from self.files

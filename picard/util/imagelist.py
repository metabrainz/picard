# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2022 Philipp Wolfer
# Copyright (C) 2019-2021, 2023-2024 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
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


from collections.abc import MutableSequence

from picard.config import get_config


class ImageList(MutableSequence):
    def __init__(self, iterable=()):
        self._images = list(iterable)
        self._hash_dict = {}
        self._changed = True

    def __len__(self):
        return len(self._images)

    def __getitem__(self, index):
        return self._images[index]

    def __setitem__(self, index, value):
        self._images[index] = value
        self._changed = True

    def __delitem__(self, index):
        del self._images[index]
        self._changed = True

    def insert(self, index, value):
        self._changed = True
        return self._images.insert(index, value)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._images)

    def _sorted(self):
        return sorted(self, key=lambda image: image.normalized_types())

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return self._sorted() == other._sorted()

    def copy(self):
        return self.__class__(self._images)

    def get_front_image(self):
        for img in self:
            if img.is_front_image():
                return img
        return None

    def to_be_saved_to_tags(self, settings=None):
        """Generator returning images to be saved to tags according to
           passed settings or config.setting
        """
        if settings is None:
            config = get_config()
            settings = config.setting
        if settings['save_images_to_tags']:
            only_one_front = settings['embed_only_one_front_image']
            for image in self:
                if not image.can_be_saved_to_tags:
                    continue
                if only_one_front:
                    if image.is_front_image():
                        yield image
                        break
                else:
                    yield image

    def strip_front_images(self):
        self._images = [image for image in self._images if not image.is_front_image()]
        self._changed = True

    def hash_dict(self):
        if self._changed:
            self._hash_dict = {img.datahash.hash(): img for img in self._images}
            self._changed = False
        return self._hash_dict


def get_sources_metadata_images(sources_metadata):
    images = set()
    for s in sources_metadata:
        images = images.union(s.images)
    return images


class ImageListState:
    def __init__(self, update_new_metadata=False, update_orig_metadata=False):
        self.new_images = {}
        self.orig_images = {}
        self.has_common_new_images = True
        self.has_common_orig_images = True
        self.first_new_obj = True
        self.first_orig_obj = True
        # The next variables specify what will be updated
        self.update_new_metadata = update_new_metadata
        self.update_orig_metadata = update_orig_metadata

    def process_images(self, src_obj, Track):
        # Check new images
        if self.update_new_metadata:
            src_dict = src_obj.metadata.images.hash_dict()
            prev_len = len(self.new_images)
            self.new_images.update(src_dict)
            if len(self.new_images) != prev_len:
                if not self.first_new_obj:
                    self.has_common_new_images = False
            if self.first_new_obj:
                self.first_new_obj = False

        if self.update_orig_metadata and not isinstance(src_obj, Track):
            # Check orig images, but not for Tracks (which don't have a useful orig_metadata)
            src_dict = src_obj.orig_metadata.images.hash_dict()
            prev_len = len(self.orig_images)
            self.orig_images.update(src_dict)
            if len(self.orig_images) != prev_len:
                if not self.first_orig_obj:
                    self.has_common_orig_images = False
            if self.first_orig_obj:
                self.first_orig_obj = False

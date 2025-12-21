# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2022 Philipp Wolfer
# Copyright (C) 2019-2021, 2023-2024 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2024 Giorgio Fontanive
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
    Iterable,
    MutableSequence,
)
from typing import TYPE_CHECKING

from picard.config import get_config


if TYPE_CHECKING:
    from picard.coverart import CoverArtImage


class ImageList(MutableSequence['CoverArtImage']):
    def __init__(self, iterable: Iterable['CoverArtImage'] | None = None):
        self._images: list['CoverArtImage'] = list(iterable or ())
        self._hash_dict = {}
        self._dirty = True

    def __len__(self):
        return len(self._images)

    def __getitem__(self, index):
        return self._images[index]

    def __setitem__(self, index, value):
        if self._images[index] != value:
            self._images[index] = value
            self._dirty = True

    def __delitem__(self, index):
        del self._images[index]
        self._dirty = True

    def insert(self, index, value: 'CoverArtImage'):
        self._images.insert(index, value)
        self._dirty = True

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._images)

    def _sorted(self):
        return sorted(self, key=lambda image: image.normalized_types())

    def __eq__(self, other) -> bool:
        if len(self) != len(other):
            return False
        return self._sorted() == other._sorted()

    def copy(self):
        return self.__class__(self._images)

    def get_front_image(self) -> 'CoverArtImage | None':
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
        self._dirty = True

    def hash_dict(self):
        if self._dirty:
            self._hash_dict = {img.datahash.hash(): img for img in self._images}
            self._dirty = False
        return self._hash_dict

    def get_types_dict(self):
        types_dict = dict()
        for image in self._images:
            image_types = image.normalized_types()
            if image_types in types_dict:
                previous_image = types_dict[image_types]
                if image.width > previous_image.width or image.height > previous_image.height:
                    continue
            types_dict[image_types] = image
        return types_dict

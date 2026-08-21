# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2022, 2025-2026 Philipp Wolfer
# Copyright (C) 2019-2021, 2023-2026 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2026 Bryan Roessler
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
    Iterable,
    Iterator,
    MutableSequence,
)
from typing import TYPE_CHECKING

from picard.config import (
    SettingConfigSection,
    get_config,
)


if TYPE_CHECKING:
    from picard.coverart import CoverArtImage


class ImageList(MutableSequence['CoverArtImage']):
    def __init__(self, iterable: Iterable['CoverArtImage'] | None = None):
        self._images: list[CoverArtImage] = list(iterable or ())
        self._hash_dict: dict[str, CoverArtImage] = {}
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

    def insert(self, index: int, value: 'CoverArtImage'):
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

    def copy(self) -> 'ImageList':
        return self.__class__(self._images)

    def get_front_image(self) -> 'CoverArtImage | None':
        for img in self:
            if img.is_front_image():
                return img
        return None

    def to_be_saved_to_tags(
        self,
        settings: SettingConfigSection | None = None,
        previous_images: 'ImageList | None' = None,
    ) -> Iterator['CoverArtImage']:
        """Generator returning images to be saved to tags according to
        passed settings or config.setting.

        If `previous_images` (the images currently embedded in a specific file)
        is given, the per-file "never replace" filters are applied against it,
        so a new image can still be kept for external file saving even when it
        is rejected for tags on this particular file.
        """
        if settings is None:
            config = get_config()
            settings = config.setting
        if settings['save_images_to_tags']:
            # Imported here to avoid a circular import between imagelist and coverart.
            from picard.coverart.processing.filters import filter_image_for_file

            only_one_front = settings['embed_only_one_front_image']
            for image in self:
                if not image.can_be_saved_to_tags:
                    continue
                if previous_images is not None and not filter_image_for_file(image, previous_images):
                    continue
                if only_one_front:
                    if image.is_front_image():
                        yield image
                        break
                else:
                    yield image

    def to_be_saved_to_files(
        self,
        settings: SettingConfigSection | None = None,
        previous_images: 'ImageList | None' = None,
    ) -> Iterator['CoverArtImage']:
        """Generator returning images to be saved as external files according to
        passed settings or config.setting.

        When save_only_one_front_image is enabled, yields only the first front
        image. Falls back to yielding all images if no front image is found.

        If `previous_images` (the images currently embedded in tags) is given
        and tags are about to be cleared (`remove_images_from_tags`), any
        original image bigger than its replacement here (or with no
        replacement at all) is used instead, so higher quality tagged art is
        saved to disk instead of being lost when it is removed from tags.
        """
        if settings is None:
            config = get_config()
            settings = config.setting
        if not settings['save_images_to_files']:
            return

        only_one_front = settings['save_only_one_front_image']
        if only_one_front:
            front = self.get_front_image()
            exported = [front] if front else list(self)
        else:
            exported = list(self)

        if previous_images and settings['remove_images_from_tags']:
            index_by_type = {image.normalized_types(): i for i, image in enumerate(exported)}
            for prev_image in previous_images:
                # Filter on is_front_image() first so normalized_types() is only
                # computed for images that can actually be candidates.
                if only_one_front and not prev_image.is_front_image():
                    continue
                types = prev_image.normalized_types()
                index = index_by_type.get(types)
                if index is None:
                    index_by_type[types] = len(exported)
                    exported.append(prev_image)
                elif prev_image.width > exported[index].width or prev_image.height > exported[index].height:
                    # Keep the higher quality tagged image instead of the smaller replacement.
                    exported[index] = prev_image

        yield from exported

    def should_remove_images_from_tags(
        self,
        settings: SettingConfigSection | None = None,
        previous_images: 'ImageList | None' = None,
    ) -> bool:
        """Whether images embedded in tags should be removed.

        Only true when explicitly requested and this list actually has at
        least one image that will be saved to an external file, so cover art
        is never deleted without being kept somewhere else.
        """
        if settings is None:
            config = get_config()
            settings = config.setting
        if not settings['remove_images_from_tags']:
            return False
        return any(self.to_be_saved_to_files(settings, previous_images))

    def strip_front_images(self) -> None:
        self._images = [image for image in self._images if not image.is_front_image()]
        self._dirty = True

    def hash_dict(self) -> dict[str, 'CoverArtImage']:
        if self._dirty:
            self._hash_dict = {img.datahash.hash: img for img in self._images if img.datahash}
            self._dirty = False
        return self._hash_dict

    def get_types_dict(self) -> dict[tuple[str, ...], 'CoverArtImage']:
        types_dict = {}
        for image in self._images:
            image_types = image.normalized_types()
            if image_types in types_dict:
                previous_image = types_dict[image_types]
                if image.width > previous_image.width or image.height > previous_image.height:
                    continue
            types_dict[image_types] = image
        return types_dict

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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


from picard import log
from picard.config import get_config
from picard.debug_opts import DebugOpt
from picard.extension_points.cover_art_filters import (
    register_cover_art_filter,
    register_cover_art_metadata_filter,
)


def _check_threshold_size(width, height):
    config = get_config()
    if not config.setting['filter_cover_by_size']:
        return True
    # If the given width or height is -1, that dimension is not considered
    min_width = config.setting['cover_minimum_width'] if width != -1 else -1
    min_height = config.setting['cover_minimum_height'] if height != -1 else -1
    log.debug_if(
        DebugOpt.COVERART,
        "Size filter: image %d x %d, minimum %d x %d",
        width,
        height,
        min_width,
        min_height,
    )
    if width < min_width or height < min_height:
        log.debug(
            "Discarding cover art due to size. Image size: %d x %d. Minimum: %d x %d",
            width,
            height,
            min_width,
            min_height,
        )
        return False
    return True


def size_filter(data, image_info, album, coverartimage):
    return _check_threshold_size(image_info.width, image_info.height)


def size_metadata_filter(metadata):
    if 'width' not in metadata or 'height' not in metadata:
        return True
    return _check_threshold_size(metadata['width'], metadata['height'])


def bigger_previous_image_filter(coverartimage, previous_images):
    """Return False if previous_images contains a bigger image of the same type.

    Used to prevent replacing embedded images with smaller downloaded ones.
    """
    config = get_config()
    if not config.setting['dont_replace_with_smaller_cover']:
        return True
    downloaded_types = coverartimage.normalized_types()
    previous_images_dict = previous_images.get_types_dict()
    if downloaded_types in previous_images_dict:
        previous_image = previous_images_dict[downloaded_types]
        log.debug_if(
            DebugOpt.COVERART,
            "Bigger image filter: new %d x %d vs existing %d x %d",
            coverartimage.width,
            coverartimage.height,
            previous_image.width,
            previous_image.height,
        )
        if coverartimage.width < previous_image.width or coverartimage.height < previous_image.height:
            log.debug("Discarding cover art. A bigger image with the same types is already embedded.")
            return False
    return True


def image_types_filter(coverartimage, previous_images):
    """Return False if previous_images contains an image of a "never replace" type.

    Used to prevent replacing embedded images of specific types (e.g. front, back).
    """
    config = get_config()
    if not config.setting['dont_replace_cover_of_types']:
        return True
    downloaded_types = set(coverartimage.normalized_types())
    never_replace_types = config.setting['dont_replace_included_types']
    log.debug_if(
        DebugOpt.COVERART,
        "Image types filter: downloaded types %r, never replace types %r",
        downloaded_types,
        never_replace_types,
    )
    previous_image_types = previous_images.get_types_dict()
    for previous_image_type in previous_image_types:
        type_already_embedded = downloaded_types.intersection(previous_image_type)
        should_not_replace = downloaded_types.intersection(never_replace_types)
        if type_already_embedded and should_not_replace:
            log.debug("Discarding cover art. An image with the same type is already embedded.")
            return False
    return True


def filter_image_for_file(coverartimage, previous_images):
    """Run per-file "never replace" filters on a single image.

    Returns True if the image should be assigned to the file,
    False if it should be skipped.
    """
    if not bigger_previous_image_filter(coverartimage, previous_images):
        return False
    if not image_types_filter(coverartimage, previous_images):
        return False
    return True


register_cover_art_filter(size_filter)
register_cover_art_metadata_filter(size_metadata_filter)

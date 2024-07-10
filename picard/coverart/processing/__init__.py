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

import time

from picard import log
from picard.config import get_config
from picard.coverart.processing import (  # noqa: F401 # pylint: disable=unused-import
    filters,
    processors,
)
from picard.extension_points.cover_art_filters import (
    ext_point_cover_art_filters,
    ext_point_cover_art_metadata_filters,
)
from picard.extension_points.cover_art_processors import (
    CoverArtProcessingError,
    ProcessingImage,
    ProcessingTarget,
    get_cover_art_processors,
)
from picard.util.imageinfo import IdentificationError


def run_image_filters(data, image_info, album, coverartimage):
    for f in ext_point_cover_art_filters:
        if not f(data, image_info, album, coverartimage):
            return False
    return True


def run_image_metadata_filters(metadata):
    for f in ext_point_cover_art_metadata_filters:
        if not f(metadata):
            return False
    return True


def run_image_processors(coverartimage, data, image_info):
    config = get_config()
    tags_data = data
    file_data = data
    try:
        start_time = time.time()
        image = ProcessingImage(data, image_info)
        both_queue, tags_queue, file_queue = get_cover_art_processors()
        for processor in both_queue:
            processor.run(image, ProcessingTarget.BOTH)
        if config.setting['save_images_to_tags']:
            tags_image = image.copy()
            for processor in tags_queue:
                processor.run(tags_image, ProcessingTarget.TAGS)
            tags_data = tags_image.get_result()
        coverartimage.set_tags_data(tags_data)
        if config.setting['save_images_to_files']:
            file_image = image.copy()
            for processor in file_queue:
                processor.run(file_image, ProcessingTarget.FILE)
            file_data = file_image.get_result()
            coverartimage.set_external_file_data(file_data)
        log.debug(
            "Image processing for %s finished in %d ms",
            coverartimage,
            1000 * (time.time() - start_time)
        )
    except IdentificationError as e:
        raise CoverArtProcessingError(e)
    except CoverArtProcessingError as e:
        coverartimage.set_tags_data(tags_data)
        if config.setting['save_images_to_files']:
            coverartimage.set_external_file_data(file_data)
        raise e

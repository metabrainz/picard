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

from functools import partial
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
from picard.util import thread
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


def _run_processors_queue(image, target, queue, coverartimage, start_time):
    for processor in queue:
        processor.run(image, target)
    data = image.get_result()
    if target == ProcessingTarget.TAGS:
        coverartimage.set_tags_data(data)
        image_target = "embedded"
    else:
        coverartimage.set_external_file_data(data)
        image_target = "external"
    log.debug(
        "Image processing for %s cover art image %s finished in %d ms",
        image_target,
        coverartimage,
        1000 * (time.time() - start_time)
    )


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
        if config.setting['save_images_to_files']:
            run_queue = partial(
                _run_processors_queue,
                image.copy(),
                ProcessingTarget.FILE,
                file_queue,
                coverartimage,
                start_time
            )
            thread.run_task(run_queue)
        if config.setting['save_images_to_tags']:
            run_queue = partial(
                _run_processors_queue,
                image.copy(),
                ProcessingTarget.TAGS,
                tags_queue,
                coverartimage,
                start_time
            )
            thread.run_task(run_queue)
        else:
            coverartimage.set_tags_data(tags_data)
    except IdentificationError as e:
        raise CoverArtProcessingError(e)
    except CoverArtProcessingError as e:
        coverartimage.set_tags_data(tags_data)
        if config.setting['save_images_to_files']:
            coverartimage.set_external_file_data(file_data)
        raise e

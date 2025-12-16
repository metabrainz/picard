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
from queue import Queue
import time

from picard import log
from picard.album import Album
from picard.config import get_config
from picard.const.cover_processing import COVER_PROCESSING_SLEEP
from picard.coverart.image import (
    CoverArtImageError,
    CoverArtImageIOError,
)
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
    ImageProcessor,
    ProcessingImage,
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


def handle_processing_exceptions(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except (CoverArtImageError, CoverArtProcessingError) as e:
            self.errors.put(e)

    return wrapper


class CoverArtImageProcessing:
    def __init__(self, album: Album):
        self.album = album
        self.queues = get_cover_art_processors()
        self.task_counter = thread.TaskCounter()
        self.errors = Queue()

    @handle_processing_exceptions
    def _run_processors_queue(self, coverartimage, initial_data, start_time, image, target):
        data = initial_data
        try:
            queue = self.queues[target]
            for processor in queue:
                processor.run(image, target)
                time.sleep(COVER_PROCESSING_SLEEP)
            data = image.get_result()
        except CoverArtProcessingError as e:
            raise e
        finally:
            if target == ImageProcessor.Target.TAGS:
                coverartimage.set_tags_data(data)
            else:
                coverartimage.set_external_file_data(data)
            log.debug(
                "Image processing for %s cover art image %s finished in %d ms",
                target.name,
                coverartimage,
                1000 * (time.time() - start_time),
            )

    @handle_processing_exceptions
    def _run_image_processors(self, coverartimage, initial_data, image_info):
        config = get_config()
        try:
            start_time = time.time()
            image = ProcessingImage(initial_data, image_info)
            for processor in self.queues[ImageProcessor.Target.BOTH]:
                processor.run(image, ImageProcessor.Target.BOTH)
                time.sleep(COVER_PROCESSING_SLEEP)
            run_queue_common = partial(self._run_processors_queue, coverartimage, initial_data, start_time)
            if config.setting['save_images_to_files']:
                run_queue = partial(run_queue_common, image.copy(), ImageProcessor.Target.FILE)
                thread.run_task(run_queue, task_counter=self.task_counter)
            if config.setting['save_images_to_tags']:
                run_queue = partial(run_queue_common, image.copy(), ImageProcessor.Target.TAGS)
                thread.run_task(run_queue, task_counter=self.task_counter)
            else:
                coverartimage.set_tags_data(initial_data)
        except IdentificationError as e:
            raise CoverArtProcessingError(e) from e
        except CoverArtProcessingError:
            coverartimage.set_tags_data(initial_data)
            if config.setting['save_images_to_files']:
                coverartimage.set_external_file_data(initial_data)
            raise

    def run_image_processors(self, coverartimage, initial_data, image_info):
        if coverartimage.can_be_processed:
            run_processors = partial(self._run_image_processors, coverartimage, initial_data, image_info)
            thread.run_task(run_processors, task_counter=self.task_counter)
        else:
            set_data = partial(handle_processing_exceptions, coverartimage.set_tags_data, initial_data)
            thread.run_task(set_data, task_counter=self.task_counter)

    def wait_for_processing(self):
        self.task_counter.wait_for_tasks()
        has_io_error = False
        while not self.errors.empty():
            error = self.errors.get()
            self.album.error_append(error)
            if isinstance(error, CoverArtImageIOError):
                has_io_error = True
        return has_io_error

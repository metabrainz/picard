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

from collections.abc import Callable
from functools import partial
from queue import Queue
import time

from picard import log
from picard.album import Album
from picard.config import get_config
from picard.const.cover_processing import COVER_PROCESSING_SLEEP
from picard.coverart.image import (
    CoverArtImage,
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
from picard.util.imageinfo import (
    IdentificationError,
    ImageInfo,
)


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
        self.task_counter: thread.TaskCounter = thread.TaskCounter()
        self.errors = Queue()

    @handle_processing_exceptions
    def _run_processors_queue(
        self,
        coverartimage: CoverArtImage,
        initial_data: bytes,
        start_time: int | float,
        save_images_to_tags: bool,
        save_images_to_files: bool,
        image: ProcessingImage,
        target: ImageProcessor.Target,
    ):
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
            if target in ImageProcessor.Target.SAME | ImageProcessor.Target.TAGS:
                coverartimage.set_data(data if save_images_to_tags else initial_data)
            if save_images_to_files and target in ImageProcessor.Target.SAME | ImageProcessor.Target.FILE:
                coverartimage.set_external_file_data(data)
            log.debug(
                "Image processing for %s cover art image %s finished in %d ms",
                target.name,
                coverartimage,
                1000 * (time.time() - start_time),
            )

    @handle_processing_exceptions
    def _run_image_processors(
        self,
        coverartimage: CoverArtImage,
        initial_data: bytes,
        image_info: ImageInfo,
    ):
        config = get_config()
        try:
            start_time = time.time()
            image = ProcessingImage(initial_data, image_info)
            save_images_to_tags = config.setting['save_images_to_tags']
            save_images_to_files = config.setting['save_images_to_files']

            run_queue_common = partial(
                self._run_processors_queue,
                coverartimage,
                initial_data,
                start_time,
                save_images_to_tags,
                save_images_to_files,
            )

            # Run processors for both tags and external files in this thread, as this is the basis
            # for the specialized processors.
            if save_images_to_files or save_images_to_tags:
                run_queue_common(image, ImageProcessor.Target.SAME)
            else:
                coverartimage.set_data(initial_data)

            # Start separate threads to run tag and file only processors in parallel
            sub_task_counter = thread.TaskCounter()
            if save_images_to_files:
                run_queue_files = partial(run_queue_common, image.copy(), ImageProcessor.Target.FILE)
                thread.run_task(run_queue_files, task_counter=sub_task_counter)
            if save_images_to_tags:
                run_queue_tags = partial(run_queue_common, image.copy(), ImageProcessor.Target.TAGS)
                thread.run_task(run_queue_tags, task_counter=sub_task_counter)
            sub_task_counter.wait_for_tasks()
        except IdentificationError as e:
            raise CoverArtProcessingError(e) from e
        except CoverArtProcessingError:
            coverartimage.set_data(initial_data)
            if config.setting['save_images_to_files']:
                coverartimage.set_external_file_data(initial_data)
            raise

    def run_image_processors(
        self,
        coverartimage: CoverArtImage,
        initial_data: bytes,
        image_info: ImageInfo,
        callback: Callable[[CoverArtImage, Exception | None], None],
    ):
        if coverartimage.can_be_processed:
            run_processors = partial(self._run_image_processors, coverartimage, initial_data, image_info)

            def next_func(result, error=None):
                callback(coverartimage, error)

            thread.run_task(run_processors, next_func=next_func, task_counter=self.task_counter)
        else:
            coverartimage.set_data(initial_data)
            callback(coverartimage, None)

    def wait_for_processing(self):
        self.task_counter.wait_for_tasks()
        has_io_error = False
        while not self.errors.empty():
            error = self.errors.get()
            self.album.error_append(error)
            if isinstance(error, CoverArtImageIOError):
                has_io_error = True
        return has_io_error

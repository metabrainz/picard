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

from PyQt6.QtCore import Qt

from picard import log
from picard.config import get_config
from picard.const.cover_processing import ResizeModes
from picard.extension_points.cover_art_processors import (
    ImageProcessor,
    ProcessingTarget,
    register_cover_art_processor,
)


class ResizeImage(ImageProcessor):

    def save_to_file(self):
        config = get_config()
        return config.setting['cover_file_resize']

    def save_to_tags(self):
        config = get_config()
        return config.setting['cover_tags_resize']

    def same_processing(self):
        setting = get_config().setting
        both_resize = setting['cover_tags_resize'] and setting['cover_file_resize']
        same_enlarge = setting['cover_tags_enlarge'] == setting['cover_file_enlarge']
        same_width = setting['cover_tags_resize_target_width'] == setting['cover_file_resize_target_width']
        same_height = setting['cover_tags_resize_target_height'] == setting['cover_file_resize_target_height']
        same_resize_mode = setting['cover_tags_resize_mode'] == setting['cover_file_resize_mode']
        return both_resize and same_enlarge and same_width and same_height and same_resize_mode

    def run(self, image, target):
        start_time = time.time()
        config = get_config()
        if target == ProcessingTarget.TAGS:
            scale_up = config.setting['cover_tags_enlarge']
            target_width = config.setting['cover_tags_resize_target_width']
            target_height = config.setting['cover_tags_resize_target_height']
            resize_mode = config.setting['cover_tags_resize_mode']
        else:
            scale_up = config.setting['cover_file_enlarge']
            target_width = config.setting['cover_file_resize_target_width']
            target_height = config.setting['cover_file_resize_target_height']
            resize_mode = config.setting['cover_file_resize_mode']

        width_scale_factor = target_width / image.info.width
        height_scale_factor = target_height / image.info.height
        if resize_mode == ResizeModes.MAINTAIN_ASPECT_RATIO:
            scale_factor = min(width_scale_factor, height_scale_factor)
        elif resize_mode == ResizeModes.SCALE_TO_WIDTH:
            scale_factor = width_scale_factor
        elif resize_mode == ResizeModes.SCALE_TO_HEIGHT:
            scale_factor = height_scale_factor
        else:  # crop or stretch
            scale_factor = max(width_scale_factor, height_scale_factor)
        if scale_factor == 1 or scale_factor > 1 and not scale_up:
            # no resizing needed
            return

        qimage = image.get_qimage()
        new_width = image.info.width * scale_factor
        new_height = image.info.height * scale_factor
        if resize_mode == ResizeModes.STRETCH_TO_FIT:
            new_width = image.info.width * width_scale_factor
            new_height = image.info.height * height_scale_factor
        scaled_image = qimage.scaled(int(new_width), int(new_height), Qt.AspectRatioMode.IgnoreAspectRatio)
        if resize_mode == ResizeModes.CROP_TO_FIT:
            cutoff_width = (scaled_image.width() - target_width) // 2
            cutoff_height = (scaled_image.height() - target_height) // 2
            scaled_image = scaled_image.copy(cutoff_width, cutoff_height, target_width, target_height)

        log.debug(
            "Resized cover art from %d x %d to %d x %d in %.2f ms",
            image.info.width,
            image.info.height,
            scaled_image.width(),
            scaled_image.height(),
            1000 * (time.time() - start_time)
        )
        image.info.width = scaled_image.width()
        image.info.height = scaled_image.height()
        image.info.datalen = scaled_image.sizeInBytes()
        image.set_result(scaled_image)


class ConvertImage(ImageProcessor):

    _format_aliases = {
        "jpeg": {"jpg", "jpeg"},
        "png": {"png"},
        "webp": {"webp"},
        "tiff": {"tif", "tiff"},
    }

    def save_to_tags(self):
        config = get_config()
        return config.setting['cover_tags_convert_images']

    def save_to_file(self):
        config = get_config()
        return config.setting['cover_file_convert_images']

    def same_processing(self):
        config = get_config()
        same_format = config.setting['cover_tags_convert_to_format'] == config.setting['cover_file_convert_to_format']
        return self.save_to_file() and self.save_to_tags() and same_format

    def run(self, image, target):
        config = get_config()
        if target == ProcessingTarget.TAGS:
            new_format = config.setting['cover_tags_convert_to_format'].lower()
        else:
            new_format = config.setting['cover_file_convert_to_format'].lower()
        previous_format = image.info.format
        if previous_format in self._format_aliases[new_format]:
            return
        image.info.extension = f".{new_format}"
        image.info.mime = f"image/{new_format}"
        log.debug("Changed cover art format from %s to %s", previous_format, new_format)


register_cover_art_processor(ResizeImage)
register_cover_art_processor(ConvertImage)

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
        same_enlarge = setting['cover_tags_dont_enlarge'] == setting['cover_file_dont_enlarge']
        tags_size = (
            setting['cover_tags_resize_target_width'] if setting['cover_tags_resize_use_width'] else 0,
            setting['cover_tags_resize_target_height'] if setting['cover_tags_resize_use_height'] else 0
        )
        file_size = (
            setting['cover_file_resize_target_width'] if setting['cover_file_resize_use_width'] else 0,
            setting['cover_file_resize_target_height'] if setting['cover_file_resize_use_height'] else 0
        )
        same_size = tags_size == file_size
        same_resize_mode = setting['cover_tags_resize_mode'] == setting['cover_file_resize_mode']
        return both_resize and same_enlarge and same_size and same_resize_mode

    def run(self, image, target):
        start_time = time.time()
        config = get_config()
        if target == ProcessingTarget.TAGS:
            scale_up = not config.setting['cover_tags_dont_enlarge']
            use_width = config.setting['cover_tags_resize_use_width']
            target_width = config.setting['cover_tags_resize_target_width']
            use_height = config.setting['cover_tags_resize_use_height']
            target_height = config.setting['cover_tags_resize_target_height']
            crop = config.setting['cover_tags_resize_mode'] == 1
            stretch = config.setting['cover_tags_resize_mode'] == 2
        else:
            scale_up = not config.setting['cover_file_dont_enlarge']
            use_width = config.setting['cover_file_resize_use_width']
            target_width = config.setting['cover_file_resize_target_width']
            use_height = config.setting['cover_file_resize_use_height']
            target_height = config.setting['cover_file_resize_target_height']
            crop = config.setting['cover_file_resize_mode'] == 1
            stretch = config.setting['cover_file_resize_mode'] == 2

        width_resize = target_width if use_width else image.info.width
        height_resize = target_height if use_height else image.info.height
        width_scale_factor = width_resize / image.info.width
        height_scale_factor = height_resize / image.info.height
        use_both_dimensions = use_height and use_width
        if use_both_dimensions and not stretch:
            if crop:
                scale_factor = max(width_scale_factor, height_scale_factor)
            else:
                scale_factor = min(width_scale_factor, height_scale_factor)
            width_scale_factor = scale_factor
            height_scale_factor = scale_factor
        if (width_scale_factor == 1 and height_scale_factor == 1
                or ((width_scale_factor > 1 or height_scale_factor > 1) and not scale_up)):
            # no resizing needed
            return

        qimage = image.get_qimage()
        if stretch:
            scaled_image = qimage.scaled(width_resize, height_resize, Qt.AspectRatioMode.IgnoreAspectRatio)
        elif crop:
            scaled_image = qimage.scaled(width_resize, height_resize, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            cutoff_width = (scaled_image.width() - width_resize) // 2
            cutoff_height = (scaled_image.height() - height_resize) // 2
            scaled_image = scaled_image.copy(cutoff_width, cutoff_height, width_resize, height_resize)
        else:  # keep aspect ratio
            if use_both_dimensions:
                scaled_image = qimage.scaled(width_resize, height_resize, Qt.AspectRatioMode.KeepAspectRatio)
            elif use_width:
                scaled_image = qimage.scaledToWidth(width_resize)
            else:
                scaled_image = qimage.scaledToHeight(height_resize)

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

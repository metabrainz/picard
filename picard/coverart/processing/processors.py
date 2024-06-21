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
        return config.setting['cover_file_scale_down'] or config.setting['cover_file_scale_up']

    def save_to_tags(self):
        config = get_config()
        return config.setting['cover_tags_scale_down'] or config.setting['cover_tags_scale_up']

    def same_processing(self):
        setting = get_config().setting
        tags_size = (
            setting['cover_tags_resize_target_width'] if setting['cover_tags_resize_use_width'] else 0,
            setting['cover_tags_resize_target_height'] if setting['cover_tags_resize_use_height'] else 0
        )
        file_size = (
            setting['cover_file_resize_target_width'] if setting['cover_file_resize_use_width'] else 0,
            setting['cover_file_resize_target_height'] if setting['cover_file_resize_use_height'] else 0
        )
        same_size = tags_size == file_size
        tags_direction = (setting['cover_tags_scale_up'], setting['cover_tags_scale_down'])
        file_direction = (setting['cover_file_scale_up'], setting['cover_file_scale_down'])
        same_direction = tags_direction == file_direction and any(tags_direction)
        tags_resize_mode = (setting['cover_tags_stretch'], setting['cover_tags_crop'])
        file_resize_mode = (setting['cover_file_stretch'], setting['cover_file_crop'])
        same_resize_mode = tags_resize_mode == file_resize_mode
        return same_size and same_direction and same_resize_mode

    def run(self, image, target):
        start_time = time.time()
        config = get_config()
        if target == ProcessingTarget.TAGS:
            scale_up = config.setting['cover_tags_scale_up']
            scale_down = config.setting['cover_tags_scale_down']
            use_width = config.setting['cover_tags_resize_use_width']
            target_width = config.setting['cover_tags_resize_target_width']
            use_height = config.setting['cover_tags_resize_use_height']
            target_height = config.setting['cover_tags_resize_target_height']
            stretch = config.setting["cover_tags_stretch"]
            crop = config.setting["cover_tags_crop"]
        else:
            scale_up = config.setting['cover_file_scale_up']
            scale_down = config.setting['cover_file_scale_down']
            use_width = config.setting['cover_file_resize_use_width']
            target_width = config.setting['cover_file_resize_target_width']
            use_height = config.setting['cover_file_resize_use_height']
            target_height = config.setting['cover_file_resize_target_height']
            stretch = config.setting["cover_file_stretch"]
            crop = config.setting["cover_file_crop"]

        width_scale_factor = 1
        width_resize = image.info.width
        if use_width:
            width_scale_factor = target_width / image.info.width
            width_resize = target_width
        height_scale_factor = 1
        height_resize = image.info.height
        if use_height:
            height_scale_factor = target_height / image.info.height
            height_resize = target_height
        if (width_scale_factor == 1 and height_scale_factor == 1
                or ((width_scale_factor > 1 and height_scale_factor > 1) and not scale_up)
                or ((width_scale_factor < 1 or height_scale_factor < 1) and not scale_down)):
            # no resizing needed
            return

        qimage = image.get_result()
        if stretch:
            scaled_image = qimage.scaled(width_resize, height_resize, Qt.AspectRatioMode.IgnoreAspectRatio)
        elif crop:
            scaled_image = qimage.scaled(width_resize, height_resize, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            cutoff_width = (scaled_image.width() - width_resize) // 2
            cutoff_height = (scaled_image.height() - height_resize) // 2
            scaled_image = scaled_image.copy(cutoff_width, cutoff_height, width_resize, height_resize)
        else:  # keep aspect ratio
            if use_width and use_height:
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


register_cover_art_processor(ResizeImage)

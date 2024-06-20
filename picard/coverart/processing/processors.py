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
        return same_size and same_direction

    def run(self, image, target):
        start_time = time.time()
        config = get_config()
        target_width = image.info.width
        target_height = image.info.height
        if target == ProcessingTarget.TAGS:
            scale_up = config.setting['cover_tags_scale_up']
            scale_down = config.setting['cover_tags_scale_down']
            use_width = config.setting['cover_tags_resize_use_width']
            if use_width:
                target_width = config.setting['cover_tags_resize_target_width']
            use_height = config.setting['cover_tags_resize_use_height']
            if use_height:
                target_height = config.setting['cover_tags_resize_target_height']
        else:
            scale_up = config.setting['cover_file_scale_up']
            scale_down = config.setting['cover_file_scale_down']
            use_width = config.setting['cover_file_resize_use_width']
            if use_width:
                target_width = config.setting['cover_file_resize_target_width']
            use_height = config.setting['cover_file_resize_use_height']
            if use_height:
                target_height = config.setting['cover_file_resize_target_height']

        if scale_down and (image.info.width > target_width or image.info.height > target_height):
            aspect_ratio = Qt.AspectRatioMode.KeepAspectRatio
        elif scale_up and (image.info.width < target_width or image.info.height < target_height):
            aspect_ratio = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        else:
            # no resizing needed
            return
        qimage = image.get_result()
        if use_width and use_height:
            scaled_image = qimage.scaled(target_width, target_height, aspect_ratio)
        elif use_width:
            scaled_image = qimage.scaledToWidth(target_width)
        else:
            scaled_image = qimage.scaledToHeight(target_height)

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

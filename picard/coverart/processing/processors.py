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
        same_up = setting['cover_file_scale_up'] == setting['cover_tags_scale_up']
        same_down = setting['cover_file_scale_down'] == setting['cover_tags_scale_down']
        same_width = setting['cover_file_resize_use_width'] == setting['cover_tags_resize_use_width']
        if setting['cover_file_resize_use_width'] and setting['cover_tags_resize_use_width']:
            same_width = setting['cover_file_resize_target_width'] == setting['cover_tags_resize_target_width']
        same_height = setting['cover_file_resize_use_height'] == setting['cover_tags_resize_use_height']
        if setting['cover_file_resize_use_height'] and setting['cover_tags_resize_use_height']:
            same_height = setting['cover_file_resize_target_height'] == setting['cover_tags_resize_target_height']
        return same_up and same_down and same_width and same_height and self.save_to_file() and self.save_to_tags()

    def _find_target_size(self, image, target):
        config = get_config()
        target_width = image.info.width
        target_height = image.info.height
        if target == ProcessingTarget.TAGS:
            if config.setting['cover_tags_resize_use_width']:
                target_width = config.setting['cover_tags_resize_target_width']
            if config.setting['cover_tags_resize_use_height']:
                target_height = config.setting['cover_tags_resize_target_height']
            scaling_up = config.setting['cover_tags_scale_up']
            scaling_down = config.setting['cover_tags_scale_down']
        else:
            if config.setting['cover_file_resize_use_width']:
                target_width = config.setting['cover_file_resize_target_width']
            if config.setting['cover_file_resize_use_height']:
                target_height = config.setting['cover_file_resize_target_height']
            scaling_up = config.setting['cover_file_scale_up']
            scaling_down = config.setting['cover_file_scale_down']
        return target_width, target_height, scaling_up, scaling_down

    def _resize_image(self, image, target_width, target_height, aspect_ratio):
        start_time = time.time()
        qimage = image.get_result()
        scaled_image = qimage.scaled(target_width, target_height, aspect_ratio)
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

    def run(self, image, target):
        target_width, target_height, scaling_up, scaling_down = self._find_target_size(image, target)
        if scaling_down and (image.info.width > target_width or image.info.height > target_height):
            aspect_ratio = Qt.AspectRatioMode.KeepAspectRatio
        elif scaling_up and (image.info.width < target_width or image.info.height < target_height):
            aspect_ratio = Qt.AspectRatioMode.KeepAspectRatioByExpanding
        else:
            # no resizing is needed
            return
        self._resize_image(image, target_width, target_height, aspect_ratio)


register_cover_art_processor(ResizeImage)

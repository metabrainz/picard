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
        return config.setting['resize_images_saved_to_file']

    def save_to_tags(self):
        config = get_config()
        return config.setting['resize_images_saved_to_tags']

    def same_processing(self):
        config = get_config()
        same_width = config.setting['cover_tags_maximum_width'] == config.setting['cover_file_maximum_width']
        same_height = config.setting['cover_tags_maximum_height'] == config.setting['cover_file_maximum_height']
        return self.save_to_tags and self.save_to_file and same_width and same_height

    def run(self, image, target):
        start_time = time.time()
        config = get_config()
        if target == ProcessingTarget.TAGS:
            max_width = config.setting['cover_tags_maximum_width']
            max_height = config.setting['cover_tags_maximum_height']
        else:
            max_width = config.setting['cover_file_maximum_width']
            max_height = config.setting['cover_file_maximum_height']
        if image.info.width <= max_width and image.info.height <= max_height:
            return
        qimage = image.get_result()
        scaled_image = qimage.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio)
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

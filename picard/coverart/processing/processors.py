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

from PyQt6.QtCore import (
    QBuffer,
    Qt,
)
from PyQt6.QtGui import QImage

from picard import log
from picard.config import get_config
from picard.extension_points.cover_art_processors import (
    ImageProcessor,
    ProcessingTarget,
    register_cover_art_processor,
)


def _get_image_data(image, image_format):
    buffer = QBuffer()
    image.save(buffer, image_format, quality=90)
    buffer.close()
    return buffer.data()


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

    def run(self, data, info, target):
        config = get_config()
        if target == ProcessingTarget.TAGS:
            max_width = config.setting['cover_tags_maximum_width']
            max_height = config.setting['cover_tags_maximum_height']
        else:
            max_width = config.setting['cover_file_maximum_width']
            max_height = config.setting['cover_file_maximum_height']
        if info.width <= max_width and info.height <= max_height:
            return data
        image = QImage.fromData(data)
        scaled_image = image.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio)
        log.debug(
            "Resizing cover art from %d x %d to %d x %d",
            info.width,
            info.height,
            scaled_image.width(),
            scaled_image.height()
        )
        return _get_image_data(scaled_image, "bmp")


class ConvertImage(ImageProcessor):

    def save_to_file(self):
        return True

    def save_to_tags(self):
        return True

    def same_processing(self):
        return False

    def run(self, data, info, target):
        image = QImage.fromData(data)
        extension = info.extension[1:]
        return _get_image_data(image, extension)


register_cover_art_processor(ResizeImage)
register_cover_art_processor(ConvertImage)

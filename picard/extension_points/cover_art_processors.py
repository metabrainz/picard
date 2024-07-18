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

from copy import copy
from enum import IntEnum

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage

from picard.plugin import ExtensionPoint
from picard.util import imageinfo


ext_point_cover_art_processors = ExtensionPoint(label='cover_art_processors')


class CoverArtProcessingError(Exception):
    pass


class CoverArtEncodingError(CoverArtProcessingError):
    pass


class ProcessingTarget(IntEnum):
    TAGS = 0
    FILE = 1
    BOTH = 2


class ProcessingImage:

    def __init__(self, image, info=None):
        self.set_result(image)
        if info is None and not isinstance(image, QImage):
            self.info = imageinfo.identify(image)
        else:
            self.info = info

    def copy(self):
        return ProcessingImage(self._qimage.copy(), copy(self.info))

    def set_result(self, image):
        if isinstance(image, QImage):
            self._qimage = image
        else:
            self._qimage = QImage.fromData(image)

    def get_qimage(self):
        return self._qimage

    def get_result(self, image_format=None, quality=90):
        if image_format is None:
            image_format = self.info.format
        buffer = QBuffer()
        if not self._qimage.save(buffer, image_format, quality=quality):
            raise CoverArtEncodingError(f"Failed to encode into {image_format}")
        qbytearray = buffer.data()
        return qbytearray.data()


class ImageProcessor:

    def save_to_tags(self):
        return False

    def save_to_file(self):
        return False

    def same_processing(self):
        return False

    def run(self, image, target):
        pass


def get_cover_art_processors():
    queues = dict.fromkeys(list(ProcessingTarget), [])
    for processor in ext_point_cover_art_processors:
        if processor.same_processing():
            queues[ProcessingTarget.BOTH].append(processor)
        else:
            if processor.save_to_tags():
                queues[ProcessingTarget.TAGS].append(processor)
            if processor.save_to_file():
                queues[ProcessingTarget.FILE].append(processor)
    return queues


def register_cover_art_processor(cover_art_processor):
    instance = cover_art_processor()
    ext_point_cover_art_processors.register(cover_art_processor.__module__, instance)

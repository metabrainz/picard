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
from typing import Optional

from PyQt6.QtCore import (
    QBuffer,
    QIODevice,
)
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
    def __init__(self, image, info: imageinfo.ImageInfo | None = None):
        self.set_result(image)
        if info is None and not isinstance(image, QImage):
            self.info = imageinfo.identify(image)
        else:
            self.info = info

    def copy(self):
        return ProcessingImage(self._qimage.copy(), copy(self.info))

    def set_result(self, image: QImage | bytes):
        if isinstance(image, QImage):
            self._qimage = image
        else:
            self._qimage = QImage.fromData(image)

    def get_qimage(self):
        return self._qimage

    def get_result(self, image_format: Optional[str] = None, quality: int = 90) -> bytes:
        """
        Encode the internal QImage to the specified format and quality and
        return the raw bytes.

        If image_format is None, the format from self.info.format is used.

        Raises:
            CoverArtEncodingError: If required attributes are missing, the
                buffer could not be opened, or saving the image failed.
        """
        if image_format is None:
            image_format = getattr(self.info, "format", None)
            if not image_format:
                raise CoverArtEncodingError("No image format specified and info.format is missing.")

        qimage = getattr(self, "_qimage", None)
        if qimage is None:
            raise CoverArtEncodingError("No QImage available to encode.")

        buffer = QBuffer()
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise CoverArtEncodingError("Failed to open QBuffer for writing.")

        try:
            if not qimage.save(buffer, image_format, quality=quality):
                raise CoverArtEncodingError(f"Failed to encode image into format '{image_format}'")
            return bytes(buffer.data())
        finally:
            buffer.close()


class ImageProcessor:
    def save_to_tags(self) -> bool:
        return False

    def save_to_file(self) -> bool:
        return False

    def same_processing(self) -> bool:
        return False

    def run(self, image: ProcessingImage, target: ProcessingTarget):
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

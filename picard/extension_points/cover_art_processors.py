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

from collections import defaultdict
from copy import copy
from enum import IntEnum
from typing import Optional

from PyQt6.QtCore import (
    QBuffer,
    QIODevice,
)
from PyQt6.QtGui import QImage

from picard.plugin import ExtensionPoint
from picard.util.imageinfo import (
    ImageInfo,
    identify,
)


ext_point_cover_art_processors = ExtensionPoint(label='cover_art_processors')


class CoverArtProcessingError(Exception):
    pass


class CoverArtEncodingError(CoverArtProcessingError):
    pass


class ProcessingImage:
    def __init__(self, image: QImage | bytes, info: ImageInfo | None = None):
        self.set_result(image)
        if info is not None:
            self.info = info
        elif isinstance(image, QImage):
            self._set_imageinfo_from_qimage(image)
        elif info is None:
            self.info = identify(image)

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

        if self._qimage is None:
            raise CoverArtEncodingError("No QImage available to encode.")

        buffer = QBuffer()
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise CoverArtEncodingError("Failed to open QBuffer for writing.")

        try:
            if not self._qimage.save(buffer, image_format, quality=quality):
                raise CoverArtEncodingError(f"Failed to encode image into format '{image_format}'")
            return buffer.data().data()
        finally:
            buffer.close()

    def _set_imageinfo_from_qimage(self, image: QImage):
        self.info = ImageInfo(
            width=image.width(),
            height=image.height(),
            mime="",
            extension="",
            datalen=0,
        )


class ImageProcessor:
    class Target(IntEnum):
        TAGS = 0
        FILE = 1
        BOTH = 2

    def save_to_tags(self) -> bool:
        return False

    def save_to_file(self) -> bool:
        return False

    def same_processing(self) -> bool:
        return False

    def run(self, image: ProcessingImage, target: Target):
        pass


def get_cover_art_processors():
    queues = defaultdict(list)
    for processor in ext_point_cover_art_processors:
        if processor.same_processing():
            queues[ImageProcessor.Target.BOTH].append(processor)
        else:
            if processor.save_to_tags():
                queues[ImageProcessor.Target.TAGS].append(processor)
            if processor.save_to_file():
                queues[ImageProcessor.Target.FILE].append(processor)
    return queues


def register_cover_art_processor(cover_art_processor):
    instance = cover_art_processor()
    ext_point_cover_art_processors.register(cover_art_processor.__module__, instance)

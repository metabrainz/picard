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
from enum import (
    Flag,
    auto,
)

from PyQt6.QtCore import (
    QBuffer,
    QIODevice,
)
from PyQt6.QtGui import QImage

from picard.config import get_config
from picard.const.cover_processing import ImageFormat
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

    def get_result(self, image_format: ImageFormat | None = None, quality: int | None = None) -> bytes:
        """
        Encode the internal QImage to the specified format and quality and
        return the raw bytes.

        If image_format is None, the format from self.info.format_info is used.

        Raises:
            CoverArtEncodingError: If required attributes are missing, the
                buffer could not be opened, or saving the image failed.
        """
        if image_format is None:
            image_format = self.info.format_info
            if not image_format:
                raise CoverArtEncodingError("No image format specified and info.format_info is missing.")

        if self._qimage is None:
            raise CoverArtEncodingError("No QImage available to encode.")

        buffer = QBuffer()
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            raise CoverArtEncodingError("Failed to open QBuffer for writing.")

        if quality is None:
            if image_format.use_quality:
                config = get_config()
                quality = config.setting['cover_image_quality']
            else:
                quality = -1

        try:
            if not self._qimage.save(buffer, image_format.value, quality=quality):
                raise CoverArtEncodingError(f"Failed to encode image into format '{image_format.value}'")
            return buffer.data().data()
        finally:
            buffer.close()

    def _set_imageinfo_from_qimage(self, image: QImage):
        self.info = ImageInfo(
            width=image.width(),
            height=image.height(),
            datalen=0,
            format_info=None,
        )


class ImageProcessor:
    class Target(Flag):
        # processing should not be performed (image processor is disabled)
        NONE = auto()
        # processing for cover art saved to tags
        TAGS = auto()
        # processing for external cover art files
        FILE = auto()
        # processing is identical for tags and files
        SAME = auto()

    def target(self) -> Target:
        """Return the processing target for this image processor.

        Subclasses need to override this if the processing should be applied to only
        tags or files. The processor should return:

        Target.SAME: the processor will be called once for an image, and processing
                     applies to both cover art in metadata and external files.
        Target.TAGS: the processor will be called only once for cover art in metadata.
        Target.FILE: the processor will be called only once for cover art in external files.
        Target.TAGS | Target.FILE: the processor will be called separately for cover art
                     in metadata and external files.
        Target.NONE: the processor will not be called at all (e.g. when disabled in settings).
        """
        return ImageProcessor.Target.SAME

    def run(self, image: ProcessingImage, target: Target):
        """Run the image processing.
        This needs to be implemented by the subclass. The image data is provided
        as a ProcessingImage, which holds the image data.
        """
        pass


def get_cover_art_processors():
    queues = defaultdict(list)
    for processor in ext_point_cover_art_processors:
        target = processor.target()
        if target == ImageProcessor.Target.SAME:
            queues[target].append(processor)
        else:
            if ImageProcessor.Target.TAGS in target:
                queues[ImageProcessor.Target.TAGS].append(processor)
            if ImageProcessor.Target.FILE in target:
                queues[ImageProcessor.Target.FILE].append(processor)
    return queues


def register_cover_art_processor(cover_art_processor):
    instance = cover_art_processor()
    ext_point_cover_art_processors.register(cover_art_processor.__module__, instance)

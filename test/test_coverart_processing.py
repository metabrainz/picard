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

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage

from test.picardtestcase import PicardTestCase

from picard.coverart.processing.filters import (
    size_filter,
    size_metadata_filter,
)


def create_fake_image(width, height, image_format):
    buffer = QBuffer()
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.save(buffer, image_format)
    buffer.close()
    return buffer.data()


class ImageFiltersTest(PicardTestCase):
    def test_filter_by_size(self):
        settings = {
            'filter_cover_by_size': True,
            'cover_minimum_width': 500,
            'cover_minimum_height': 500
        }
        self.set_config_values(settings)
        image1 = create_fake_image(400, 600, "png")
        image2 = create_fake_image(500, 500, "jpeg")
        image3 = create_fake_image(600, 600, "bmp")
        self.assertFalse(size_filter(image1))
        self.assertTrue(size_filter(image2))
        self.assertTrue(size_filter(image3))

    def test_filter_by_size_metadata(self):
        settings = {
            'filter_cover_by_size': True,
            'cover_minimum_width': 500,
            'cover_minimum_height': 500
        }
        self.set_config_values(settings)
        image_metadata1 = {'width': 400, 'height': 600}
        image_metadata2 = {'width': 500, 'height': 500}
        image_metadata3 = {'width': 600, 'height': 600}
        self.assertFalse(size_metadata_filter(image_metadata1))
        self.assertTrue(size_metadata_filter(image_metadata2))
        self.assertTrue(size_metadata_filter(image_metadata3))


# class ImageProcessorsTest(PicardTestCase):
#     pass

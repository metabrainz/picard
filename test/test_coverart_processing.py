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
import itertools

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage

from test.picardtestcase import PicardTestCase

from picard.coverart.image import CoverArtImage
from picard.coverart.processing import run_image_processors
from picard.coverart.processing.filters import (
    size_filter,
    size_metadata_filter,
)
from picard.coverart.processing.processors import ResizeImage
from picard.extension_points.cover_art_processors import (
    CoverArtProcessingError,
    ProcessingImage,
    ProcessingTarget,
)


def create_fake_image(width, height, image_format):
    buffer = QBuffer()
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.save(buffer, image_format)
    buffer.close()
    return buffer.data()


class ImageFiltersTest(PicardTestCase):
    def setUp(self):
        settings = {
            'filter_cover_by_size': True,
            'cover_minimum_width': 500,
            'cover_minimum_height': 500
        }
        self.set_config_values(settings)

    def test_filter_by_size(self):
        image1 = create_fake_image(400, 600, "png")
        image2 = create_fake_image(500, 500, "jpeg")
        image3 = create_fake_image(600, 600, "bmp")
        self.assertFalse(size_filter(image1))
        self.assertTrue(size_filter(image2))
        self.assertTrue(size_filter(image3))

    def test_filter_by_size_metadata(self):
        image_metadata1 = {'width': 400, 'height': 600}
        image_metadata2 = {'width': 500, 'height': 500}
        image_metadata3 = {'width': 600, 'height': 600}
        self.assertFalse(size_metadata_filter(image_metadata1))
        self.assertTrue(size_metadata_filter(image_metadata2))
        self.assertTrue(size_metadata_filter(image_metadata3))


class ImageProcessorsTest(PicardTestCase):
    def setUp(self):
        self.settings = {
            'enabled_plugins': [],
            'resize_images_saved_to_tags': True,
            'cover_tags_maximum_width': 500,
            'cover_tags_maximum_height': 500,
            'resize_images_saved_to_file': True,
            'cover_file_maximum_width': 750,
            'cover_file_maximum_height': 750,
            'save_images_to_tags': True,
            'save_images_to_files': True,
        }
        self.set_config_values(self.settings)

    def test_resize(self):
        sizes = [
            (500, 500),
            (1000, 500),
            (600, 1000),
            (1000, 1000),
            (400, 400)
        ]
        expected_sizes = [
            (500, 500),
            (500, 250),
            (300, 500),
            (500, 500),
            (400, 400)
        ]
        processor = ResizeImage()
        for size, expected_size in zip(sizes, expected_sizes):
            image = ProcessingImage(create_fake_image(size[0], size[1], "jpg"))
            processor.run(image, ProcessingTarget.TAGS)
            data = image.get_result("jpg")
            new_image = QImage.fromData(data)
            new_size = (new_image.width(), new_image.height())
            self.assertEqual(new_size, expected_size)
            self.assertEqual(new_size, (image.info.width, image.info.height))

    def test_image_processors(self):
        sizes = [
            (1000, 1000),
            (1000, 500),
            (600, 600),
        ]
        expected_sizes = [
            ((500, 500), (750, 750)),
            ((500, 250), (750, 375)),
            ((500, 500), (600, 600)),
        ]
        settings = copy(self.settings)
        self.target_combinations = itertools.product([True, False], repeat=2)
        for save_to_tags, save_to_file in self.target_combinations:
            settings['save_images_to_tags'] = save_to_tags
            settings['save_images_to_files'] = save_to_file
            self.set_config_values(settings)
            for size, expected_size in zip(sizes, expected_sizes):
                coverartimage = CoverArtImage()
                image = create_fake_image(size[0], size[1], "jpg")
                run_image_processors(image, coverartimage)
                tags_size = (coverartimage.width, coverartimage.height)
                expected_size_tags = expected_size[0] if save_to_tags else size
                self.assertEqual(tags_size, expected_size_tags)
                if save_to_file:
                    external_cover = coverartimage.external_file_coverart
                    file_size = (external_cover.width, external_cover.height)
                    self.assertEqual(file_size, expected_size[1])
                else:
                    self.assertIsNone(coverartimage.external_file_coverart)
                extension = coverartimage.extension[1:]
                self.assertEqual(extension, "jpg")
        self.set_config_values(self.settings)

    def test_identification_error(self):
        image = create_fake_image(0, 0, "jpg")
        coverartimage = CoverArtImage()
        with self.assertRaises(CoverArtProcessingError):
            run_image_processors(image, coverartimage)

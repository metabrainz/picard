# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Philipp Wolfer
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

from PyQt6.QtCore import QBuffer
from PyQt6.QtGui import QImage

from test.picardtestcase import PicardTestCase

from picard import config
from picard.album import Album
from picard.const.cover_processing import ResizeModes
from picard.coverart.image import CoverArtImage
from picard.coverart.processing import CoverArtImageProcessing
from picard.coverart.processing.filters import (
    bigger_previous_image_filter,
    image_types_filter,
    size_filter,
    size_metadata_filter,
)
from picard.coverart.processing.processors import (
    ConvertImage,
    ResizeImage,
)
from picard.extension_points.cover_art_processors import (
    CoverArtProcessingError,
    ProcessingImage,
    ProcessingTarget,
)
from picard.util import imageinfo
from picard.util.imagelist import ImageList


def create_fake_image(width, height, image_format):
    buffer = QBuffer()
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.save(buffer, image_format)
    buffer.close()
    data = buffer.data()
    try:
        info = imageinfo.identify(data)
    except imageinfo.IdentificationError:
        info = None
    return data, info


class ImageFiltersTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        settings = {
            'filter_cover_by_size': True,
            'cover_minimum_width': 500,
            'cover_minimum_height': 500,
            'dont_replace_with_smaller_cover': True,
            'dont_replace_cover_of_types': True,
            'dont_replace_included_types': ['front', 'booklet'],
            'dont_replace_excluded_types': ['back'],
            'save_images_to_tags': True,
        }
        self.set_config_values(settings)

    def test_filter_by_size(self):
        image1, info1 = create_fake_image(400, 600, 'png')
        image2, info2 = create_fake_image(500, 500, 'jpeg')
        image3, info3 = create_fake_image(600, 600, 'tiff')
        self.assertFalse(size_filter(image1, info1, None, None))
        self.assertTrue(size_filter(image2, info2, None, None))
        self.assertTrue(size_filter(image3, info3, None, None))

    def test_filter_by_size_metadata(self):
        image_metadata1 = {'width': 400, 'height': 600}
        image_metadata2 = {'width': 500, 'height': 500}
        image_metadata3 = {'width': 600, 'height': 600}
        self.assertFalse(size_metadata_filter(image_metadata1))
        self.assertTrue(size_metadata_filter(image_metadata2))
        self.assertTrue(size_metadata_filter(image_metadata3))

    def _create_fake_album(self):
        previous_coverartimage = CoverArtImage(types=['front'], support_types=True)
        previous_coverartimage.width = 1000
        previous_coverartimage.height = 1000
        album = Album(None)
        album.orig_metadata.images = ImageList([previous_coverartimage])
        return album

    def test_filter_by_previous_image_size(self):
        album = self._create_fake_album()
        image1, info1 = create_fake_image(500, 500, 'jpg')
        image2, info2 = create_fake_image(2000, 2000, 'jpg')
        coverartimage = CoverArtImage(types=['front'], support_types=True)
        self.assertFalse(bigger_previous_image_filter(image1, info1, album, coverartimage))
        self.assertTrue(bigger_previous_image_filter(image2, info2, album, coverartimage))
        coverartimage = CoverArtImage(types=['back'], support_types=True)
        self.assertTrue(bigger_previous_image_filter(image1, info1, album, coverartimage))

    def test_filter_by_image_type(self):
        album = self._create_fake_album()
        image, info = create_fake_image(1000, 1000, 'jpg')
        coverartimage1 = CoverArtImage(types=['front'], support_types=True)
        coverartimage2 = CoverArtImage(types=['back'], support_types=True)
        coverartimage3 = CoverArtImage(types=['front', 'back'], support_types=True)
        coverartimage4 = CoverArtImage(types=['spine'], support_types=True)
        coverartimage5 = CoverArtImage(types=['booklet', 'spine'], support_types=True)
        self.assertFalse(image_types_filter(image, info, album, coverartimage1))
        self.assertTrue(image_types_filter(image, info, album, coverartimage2))
        self.assertTrue(image_types_filter(image, info, album, coverartimage3))
        self.assertTrue(image_types_filter(image, info, album, coverartimage4))
        self.assertTrue(image_types_filter(image, info, album, coverartimage5))


class ImageProcessorsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.settings = {
            'enabled_plugins': [],
            'cover_tags_resize': True,
            'cover_tags_enlarge': True,
            'cover_tags_resize_target_width': 500,
            'cover_tags_resize_target_height': 500,
            'cover_tags_resize_mode': ResizeModes.MAINTAIN_ASPECT_RATIO,
            'cover_tags_convert_images': False,
            'cover_tags_convert_to_format': 'jpeg',
            'cover_file_resize': True,
            'cover_file_enlarge': True,
            'cover_file_resize_target_width': 750,
            'cover_file_resize_target_height': 750,
            'cover_file_resize_mode': ResizeModes.MAINTAIN_ASPECT_RATIO,
            'save_images_to_tags': True,
            'save_images_to_files': True,
            'cover_file_convert_images': False,
            'cover_file_convert_to_format': 'jpeg',
        }

    def _check_image_processors(self, size, expected_tags_size, expected_file_size=None):
        coverartimage = CoverArtImage()
        image, info = create_fake_image(size[0], size[1], 'jpg')
        album = Album(None)
        image_processing = CoverArtImageProcessing(album)
        image_processing.run_image_processors(coverartimage, image, info)
        image_processing.wait_for_processing()
        tags_size = (coverartimage.width, coverartimage.height)
        if config.setting['save_images_to_tags']:
            self.assertEqual(tags_size, expected_tags_size)
        else:
            self.assertEqual(tags_size, size)
        if config.setting['save_images_to_files']:
            external_cover = coverartimage.external_file_coverart
            file_size = (external_cover.width, external_cover.height)
            self.assertEqual(file_size, expected_file_size)
        else:
            self.assertIsNone(coverartimage.external_file_coverart)
        extension = coverartimage.extension[1:]
        self.assertEqual(extension, 'jpg')

    def test_image_processors_save_to_both(self):
        self.set_config_values(self.settings)
        self._check_image_processors((1000, 1000), (500, 500), (750, 750))
        self._check_image_processors((600, 600), (500, 500), (750, 750))
        self._check_image_processors((400, 400), (500, 500), (750, 750))

    def test_image_processors_save_to_tags(self):
        settings = copy(self.settings)
        settings['save_images_to_files'] = False
        self.set_config_values(settings)
        self._check_image_processors((1000, 1000), (500, 500))
        self._check_image_processors((600, 600), (500, 500))
        self._check_image_processors((400, 400), (500, 500))
        self.set_config_values(self.settings)

    def test_image_processors_save_to_file(self):
        settings = copy(self.settings)
        settings['save_images_to_tags'] = False
        self.set_config_values(settings)
        self._check_image_processors((1000, 1000), (1000, 1000), (750, 750))
        self._check_image_processors((600, 600), (600, 600), (750, 750))
        self._check_image_processors((400, 400), (400, 400), (750, 750))
        self.set_config_values(self.settings)

    def test_image_processors_save_to_none(self):
        settings = copy(self.settings)
        settings['save_images_to_tags'] = False
        settings['save_images_to_files'] = False
        self.set_config_values(settings)
        self._check_image_processors((1000, 1000), (1000, 1000), (1000, 1000))
        self.set_config_values(self.settings)

    def _check_resize_image(self, size, expected_size):
        image = ProcessingImage(*create_fake_image(size[0], size[1], 'jpg'))
        processor = ResizeImage()
        processor.run(image, ProcessingTarget.TAGS)
        new_size = (image.get_qimage().width(), image.get_qimage().height())
        new_info_size = (image.info.width, image.info.height)
        self.assertEqual(new_size, expected_size)
        self.assertEqual(new_info_size, expected_size)

    def test_scale_down_both_dimensions(self):
        self.set_config_values(self.settings)
        self._check_resize_image((1000, 1000), (500, 500))
        self._check_resize_image((1000, 500), (500, 250))
        self._check_resize_image((600, 1200), (250, 500))

    def test_scale_down_only_width(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.SCALE_TO_WIDTH
        self.set_config_values(settings)
        self._check_resize_image((1000, 1000), (500, 500))
        self._check_resize_image((1000, 500), (500, 250))
        self._check_resize_image((600, 1200), (500, 1000))
        self.set_config_values(self.settings)

    def test_scale_down_only_height(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.SCALE_TO_HEIGHT
        self.set_config_values(settings)
        self._check_resize_image((1000, 1000), (500, 500))
        self._check_resize_image((1000, 500), (1000, 500))
        self._check_resize_image((600, 1200), (250, 500))
        self.set_config_values(self.settings)

    def test_scale_up_both_dimensions(self):
        self.set_config_values(self.settings)
        self._check_resize_image((250, 250), (500, 500))
        self._check_resize_image((400, 500), (400, 500))
        self._check_resize_image((250, 150), (500, 300))

    def test_scale_up_only_width(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.SCALE_TO_WIDTH
        self.set_config_values(settings)
        self._check_resize_image((250, 250), (500, 500))
        self._check_resize_image((400, 500), (500, 625))
        self._check_resize_image((500, 250), (500, 250))
        self.set_config_values(self.settings)

    def test_scale_up_only_height(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.SCALE_TO_HEIGHT
        self.set_config_values(settings)
        self._check_resize_image((250, 250), (500, 500))
        self._check_resize_image((400, 500), (400, 500))
        self._check_resize_image((500, 250), (1000, 500))
        self.set_config_values(self.settings)

    def test_scale_priority(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_target_width'] = 500
        settings['cover_tags_resize_target_height'] = 1000
        self.set_config_values(settings)
        self._check_resize_image((750, 750), (500, 500))
        self.set_config_values(self.settings)

    def test_stretch_both_dimensions(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.STRETCH_TO_FIT
        self.set_config_values(settings)
        self._check_resize_image((1000, 100), (500, 500))
        self._check_resize_image((200, 500), (500, 500))
        self._check_resize_image((200, 2000), (500, 500))
        self.set_config_values(self.settings)

    def test_crop_both_dimensions(self):
        settings = copy(self.settings)
        settings['cover_tags_resize_mode'] = ResizeModes.CROP_TO_FIT
        self.set_config_values(settings)
        self._check_resize_image((1000, 100), (500, 500))
        self._check_resize_image((750, 1000), (500, 500))
        self._check_resize_image((250, 1000), (500, 500))
        self.set_config_values(self.settings)

    def _check_convert_image(self, format, expected_format):
        image = ProcessingImage(*create_fake_image(100, 100, format))
        processor = ConvertImage()
        processor.run(image, ProcessingTarget.TAGS)
        new_image = image.get_result()
        new_info = imageinfo.identify(new_image)
        self.assertIn(new_info.format, ConvertImage._format_aliases[expected_format])

    def test_format_conversion(self):
        settings = copy(self.settings)
        settings['cover_tags_convert_images'] = True
        formats = ['jpeg', 'png', 'webp', 'tiff']
        for format in formats:
            settings['cover_tags_convert_to_format'] = format
            self.set_config_values(settings)
            self._check_convert_image('jpeg', format)
        self.set_config_values(self.settings)

    def _check_processing_error(self, image, info):
        self.set_config_values(self.settings)
        coverartimage = CoverArtImage()
        album = Album(None)
        image_processing = CoverArtImageProcessing(album)
        image_processing.run_image_processors(coverartimage, image, info)
        image_processing.wait_for_processing()
        self.assertNotEqual(album.errors, [])
        for error in album.errors:
            self.assertIsInstance(error, CoverArtProcessingError)

    def test_identification_error(self):
        image, info = create_fake_image(0, 0, "jpg")
        self._check_processing_error(image, info)

    def test_encoding_error(self):
        image, info = create_fake_image(500, 500, "jpg")
        info.extension = ".test"
        self._check_processing_error(image, info)

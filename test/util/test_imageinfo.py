# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2020, 2025 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2025-2026 Bob Swift
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
    subtest_cases,
)

from picard.const.cover_processing import ImageFormat
from picard.util import imageinfo


class IdentifyTest(PicardTestCase):
    @subtest_cases(
        "filename,expected",
        [
            ('mb.gif', imageinfo.ImageInfo(width=140, height=96, datalen=5806, format_info=ImageFormat.GIF)),
            ('mb.png', imageinfo.ImageInfo(width=140, height=96, datalen=11137, format_info=ImageFormat.PNG)),
            ('mb.jpg', imageinfo.ImageInfo(width=140, height=96, datalen=8550, format_info=ImageFormat.JPEG)),
            ('mb-vp8.webp', imageinfo.ImageInfo(width=140, height=96, datalen=6178, format_info=ImageFormat.WEBP)),
            ('mb-vp8l.webp', imageinfo.ImageInfo(width=140, height=96, datalen=9432, format_info=ImageFormat.WEBP)),
            ('mb-vp8x.webp', imageinfo.ImageInfo(width=140, height=96, datalen=6858, format_info=ImageFormat.WEBP)),
            ('mb.tiff', imageinfo.ImageInfo(width=140, height=96, datalen=12509, format_info=ImageFormat.TIFF)),
            ('mb.pdf', imageinfo.ImageInfo(width=0, height=0, datalen=10362, format_info=ImageFormat.PDF)),
        ],
    )
    def test_identify_supported_formats(self, filename, expected):
        with open(get_test_data_path(filename), 'rb') as f:
            self.assertEqual(imageinfo.identify(f.read()), expected)

    def test_webp_insufficient_data(self):
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, b'RIFF\x00\x00\x00\x00WEBPVP8L')
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, b'RIFF\x00\x00\x00\x00WEBPVP8X')

    def test_not_enough_data(self):
        self.assertRaises(imageinfo.IdentificationError, imageinfo.identify, "x")
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, "x")

    def test_invalid_data(self):
        self.assertRaises(imageinfo.IdentificationError, imageinfo.identify, "x" * 20)
        self.assertRaises(imageinfo.UnrecognizedFormat, imageinfo.identify, "x" * 20)

    def test_invalid_png_data(self):
        data = '\x89PNG\x0d\x0a\x1a\x0a' + "x" * 20
        self.assertRaises(imageinfo.IdentificationError, imageinfo.identify, data)
        self.assertRaises(imageinfo.UnrecognizedFormat, imageinfo.identify, data)


class SupportsMimeTypeTest(PicardTestCase):
    def test_supported_mime_types(self):
        self.assertTrue(imageinfo.supports_mime_type('application/pdf'))
        self.assertTrue(imageinfo.supports_mime_type('image/gif'))
        self.assertTrue(imageinfo.supports_mime_type('image/jpeg'))
        self.assertTrue(imageinfo.supports_mime_type('image/png'))
        self.assertTrue(imageinfo.supports_mime_type('image/tiff'))
        self.assertTrue(imageinfo.supports_mime_type('image/webp'))

    def test_unsupported_mime_types(self):
        self.assertFalse(imageinfo.supports_mime_type('application/octet-stream'))
        self.assertFalse(imageinfo.supports_mime_type('text/html'))


class GetSupportedExtensionsTest(PicardTestCase):
    def test_supported_extensions(self):
        extensions = list(imageinfo.get_supported_extensions())
        self.assertIn('.jpeg', extensions)
        self.assertIn('.jpg', extensions)
        self.assertIn('.pdf', extensions)
        self.assertIn('.png', extensions)
        self.assertIn('.tif', extensions)
        self.assertIn('.tiff', extensions)
        self.assertIn('.webp', extensions)

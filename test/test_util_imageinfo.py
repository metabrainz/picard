# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2020 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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


from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.util import imageinfo


class IdentifyTest(PicardTestCase):

    def test_gif(self):
        file = get_test_data_path('mb.gif')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/gif',
                    extension='.gif',
                    datalen=5806
                )
            )

    def test_png(self):
        file = get_test_data_path('mb.png')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/png',
                    extension='.png',
                    datalen=11137
                )
            )

    def test_jpeg(self):
        file = get_test_data_path('mb.jpg')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/jpeg',
                    extension='.jpg',
                    datalen=8550
                )
            )

    def test_webp_vp8(self):
        file = get_test_data_path('mb-vp8.webp')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/webp',
                    extension='.webp',
                    datalen=6178
                )
            )

    def test_webp_vp8l(self):
        file = get_test_data_path('mb-vp8l.webp')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/webp',
                    extension='.webp',
                    datalen=9432
                )
            )

    def test_webp_vp8x(self):
        file = get_test_data_path('mb-vp8x.webp')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/webp',
                    extension='.webp',
                    datalen=6858
                )
            )

    def test_webp_insufficient_data(self):
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, b'RIFF\x00\x00\x00\x00WEBPVP8L')
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, b'RIFF\x00\x00\x00\x00WEBPVP8X')

    def test_tiff(self):
        file = get_test_data_path('mb.tiff')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=140,
                    height=96,
                    mime='image/tiff',
                    extension='.tiff',
                    datalen=12509
                )
            )

    def test_pdf(self):
        file = get_test_data_path('mb.pdf')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                imageinfo.ImageInfo(
                    width=0,
                    height=0,
                    mime='application/pdf',
                    extension='.pdf',
                    datalen=10362
                )
            )

    def test_not_enough_data(self):
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, "x")
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, "x")

    def test_invalid_data(self):
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, "x" * 20)
        self.assertRaises(imageinfo.UnrecognizedFormat,
                          imageinfo.identify, "x" * 20)

    def test_invalid_png_data(self):
        data = '\x89PNG\x0D\x0A\x1A\x0A' + "x" * 20
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, data)
        self.assertRaises(imageinfo.UnrecognizedFormat,
                          imageinfo.identify, data)


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

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Philipp Wolfer
# Copyright (C) 2019-2020 Laurent Monin
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


import os.path
import unittest

from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.const.sys import IS_WIN
from picard.coverart.image import (
    CoverArtImage,
    LocalFileCoverArtImage,
)
from picard.coverart.utils import Id3ImageType


def create_image(extra_data, types=None, support_types=False,
                 support_multi_types=False, comment=None, id3_type=None):
    return CoverArtImage(
        data=create_fake_png(extra_data),
        types=types,
        comment=comment,
        support_types=support_types,
        support_multi_types=support_multi_types,
        id3_type=id3_type,
    )


class CoverArtImageTest(PicardTestCase):
    def test_is_front_image_no_types(self):
        image = create_image(b'a')
        self.assertTrue(image.is_front_image())
        self.assertEqual(Id3ImageType.COVER_FRONT, image.id3_type)
        image.can_be_saved_to_metadata = False
        self.assertFalse(image.is_front_image())

    def test_is_front_image_types_supported(self):
        image = create_image(b'a', types=["booklet", "front"], support_types=True)
        self.assertTrue(image.is_front_image())
        image.is_front = False
        self.assertFalse(image.is_front_image())
        image = create_image(b'a', support_types=True)
        self.assertFalse(image.is_front_image())

    def test_is_front_image_no_types_supported(self):
        image = create_image(b'a', types=["back"], support_types=False)
        self.assertTrue(image.is_front_image())
        self.assertEqual(Id3ImageType.COVER_FRONT, image.id3_type)

    def test_maintype(self):
        self.assertEqual("front", create_image(b'a').maintype)
        self.assertEqual("front", create_image(b'a', support_types=True).maintype)
        self.assertEqual("front", create_image(b'a', types=["back", "front"], support_types=True).maintype)
        self.assertEqual("back", create_image(b'a', types=["back", "medium"], support_types=True).maintype)
        self.assertEqual("front", create_image(b'a', types=["back", "medium"], support_types=False).maintype)

    def test_id3_type_derived(self):
        self.assertEqual(Id3ImageType.COVER_FRONT, create_image(b'a').id3_type)
        self.assertEqual(Id3ImageType.COVER_FRONT, create_image(b'a', support_types=True).id3_type)
        self.assertEqual(Id3ImageType.COVER_FRONT, create_image(b'a', types=["back", "front"], support_types=True).id3_type)
        self.assertEqual(Id3ImageType.COVER_BACK, create_image(b'a', types=["back", "medium"], support_types=True).id3_type)
        self.assertEqual(Id3ImageType.COVER_FRONT, create_image(b'a', types=["back", "medium"], support_types=False).id3_type)
        self.assertEqual(Id3ImageType.MEDIA, create_image(b'a', types=["medium"], support_types=True).id3_type)
        self.assertEqual(Id3ImageType.LEAFLET_PAGE, create_image(b'a', types=["booklet"], support_types=True).id3_type)
        self.assertEqual(Id3ImageType.OTHER, create_image(b'a', types=["spine"], support_types=True).id3_type)
        self.assertEqual(Id3ImageType.OTHER, create_image(b'a', types=["sticker"], support_types=True).id3_type)

    def test_id3_type_explicit(self):
        image = create_image(b'a', types=["back"], support_types=True)
        for id3_type in Id3ImageType:
            image.id3_type = id3_type
            self.assertEqual(id3_type, image.id3_type)
        image.id3_type = None
        self.assertEqual(Id3ImageType.COVER_BACK, image.id3_type)

    def test_id3_type_value_error(self):
        image = create_image(b'a')
        for invalid_value in ('foo', 200, -1):
            with self.assertRaises(ValueError):
                image.id3_type = invalid_value

    def test_compare_without_type(self):
        image1 = create_image(b'a', types=["front"])
        image2 = create_image(b'a', types=["back"])
        image3 = create_image(b'a', types=["back"], support_types=True)
        image4 = create_image(b'b', types=["front"])

        self.assertEqual(image1, image2)
        self.assertEqual(image1, image3)
        self.assertNotEqual(image1, image4)

    def test_compare_with_primary_type(self):
        image1 = create_image(b'a', types=["front"], support_types=True)
        image2 = create_image(b'a', types=["front", "booklet"], support_types=True, support_multi_types=True)
        image3 = create_image(b'a', types=["back"], support_types=True)
        image4 = create_image(b'b', types=["front"], support_types=True)
        image5 = create_image(b'a', types=[], support_types=True)
        image6 = create_image(b'a', types=[], support_types=True)

        self.assertEqual(image1, image2)
        self.assertNotEqual(image1, image3)
        self.assertNotEqual(image1, image4)
        self.assertNotEqual(image3, image5)
        self.assertEqual(image5, image6)

    def test_compare_with_multiple_types(self):
        image1 = create_image(b'a', types=["front"], support_types=True, support_multi_types=True)
        image2 = create_image(b'a', types=["front", "booklet"], support_types=True, support_multi_types=True)
        image3 = create_image(b'a', types=["front", "booklet"], support_types=True, support_multi_types=True)
        image4 = create_image(b'b', types=["front", "booklet"], support_types=True, support_multi_types=True)

        self.assertNotEqual(image1, image2)
        self.assertEqual(image2, image3)
        self.assertNotEqual(image2, image4)

    def test_set_data(self):
        imgdata = create_fake_png(b'a')
        imgdata2 = create_fake_png(b'xxx')
        # set data once
        coverartimage = CoverArtImage(data=imgdata2)
        tmp_file = coverartimage.tempfile_filename
        filesize = os.path.getsize(tmp_file)
        # ensure file was written, and check its length
        self.assertEqual(filesize, len(imgdata2))
        self.assertEqual(coverartimage.data, imgdata2)

        # set data again, with another payload
        coverartimage.set_data(imgdata)

        tmp_file = coverartimage.tempfile_filename
        filesize = os.path.getsize(tmp_file)
        # check file length again
        self.assertEqual(filesize, len(imgdata))
        self.assertEqual(coverartimage.data, imgdata)


class LocalFileCoverArtImageTest(PicardTestCase):
    def test_set_file_url(self):
        path = '/some/path/image.jpeg'
        image = LocalFileCoverArtImage(path)
        self.assertEqual(image.url.toString(), 'file://' + path)

    def test_support_types(self):
        path = '/some/path/image.jpeg'
        image = LocalFileCoverArtImage(path)
        self.assertFalse(image.support_types)
        self.assertFalse(image.support_multi_types)
        image = LocalFileCoverArtImage(path, support_types=True)
        self.assertTrue(image.support_types)
        self.assertFalse(image.support_multi_types)
        image = LocalFileCoverArtImage(path, support_multi_types=True)
        self.assertFalse(image.support_types)
        self.assertTrue(image.support_multi_types)

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_windows_path(self):
        path = 'C:\\Music\\somefile.mp3'
        image = LocalFileCoverArtImage(path)
        self.assertEqual(image.url.toLocalFile(), 'C:/Music/somefile.mp3')

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2021-2022 Philipp Wolfer
# Copyright (C) 2019-2021 Laurent Monin
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


from collections import Counter
import os.path
from tempfile import TemporaryDirectory
import unittest

from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.const import DEFAULT_COVER_IMAGE_FILENAME
from picard.const.sys import IS_WIN
from picard.coverart.image import (
    CoverArtImage,
    LocalFileCoverArtImage,
)
from picard.coverart.utils import Id3ImageType
from picard.metadata import Metadata
from picard.util import encode_filename
from picard.util.filenaming import WinPathTooLong


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

    def test_save(self):
        self.set_config_values({
            'image_type_as_filename': True,
            'windows_compatibility': True,
            'win_compat_replacements': {},
            'windows_long_paths': False,
            'replace_spaces_with_underscores': False,
            'replace_dir_separator': '_',
            'enabled_plugins': [],
            'ascii_filenames': False,
            'save_images_overwrite': False,
        })
        metadata = Metadata()
        counters = Counter()
        with TemporaryDirectory() as d:
            image1 = create_image(b'a', types=['back'], support_types=True)
            expected_filename = os.path.join(d, 'back.png')
            counter_filename = encode_filename(os.path.join(d, 'back'))
            image1.save(d, metadata, counters)
            self.assertTrue(os.path.exists(expected_filename))
            self.assertEqual(len(image1.data), os.path.getsize(expected_filename))
            self.assertEqual(1, counters[counter_filename])
            image2 = create_image(b'bb', types=['back'], support_types=True)
            image2.save(d, metadata, counters)
            expected_filename_2 = os.path.join(d, 'back (1).png')
            self.assertTrue(os.path.exists(expected_filename_2))
            self.assertEqual(len(image2.data), os.path.getsize(expected_filename_2))
            self.assertEqual(2, counters[counter_filename])


class CoverArtImageMakeFilenameTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.image = create_image(b'a', types=['back'], support_types=True)
        self.metadata = Metadata()
        self.set_config_values({
            'windows_compatibility': False,
            'win_compat_replacements': {},
            'enabled_plugins': [],
            'ascii_filenames': False,
            'replace_spaces_with_underscores': False,
            'replace_dir_separator': '_',
        })

    def compare_paths(self, path1, path2):
        self.assertEqual(
            encode_filename(os.path.normpath(path1)),
            encode_filename(os.path.normpath(path2)),
        )

    def test_make_image_filename(self):
        filename = self.image._make_image_filename('AlbumArt', '/music/albumart',
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths('/music/albumart/AlbumArt', filename)

    def test_make_image_filename_default(self):
        filename = self.image._make_image_filename('$noop()', '/music/albumart',
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths(
            os.path.join('/music/albumart/', DEFAULT_COVER_IMAGE_FILENAME), filename)

    def test_make_image_filename_relative_path(self):
        self.metadata['album'] = 'TheAlbum'
        filename = self.image._make_image_filename("../covers/%album%", "/music/album",
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths('/music/covers/TheAlbum', filename)

    def test_make_image_filename_absolute_path(self):
        filename = self.image._make_image_filename('/foo/bar/AlbumArt', '/music/albumart',
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths('/foo/bar/AlbumArt', filename)

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_make_image_filename_absolute_path_no_common_base(self):
        filename = self.image._make_image_filename('D:/foo/AlbumArt', 'C:/music',
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths('D:\\foo\\AlbumArt', filename)

    def test_make_image_filename_script(self):
        cover_script = '%album%-$if($eq(%coverart_maintype%,front),cover,%coverart_maintype%)'
        self.metadata['album'] = 'TheAlbum'
        filename = self.image._make_image_filename(cover_script, "/music/",
            self.metadata, win_compat=False, win_shorten_path=False)
        self.compare_paths('/music/TheAlbum-back', filename)

    def test_make_image_filename_save_path(self):
        self.set_config_values({
            'windows_compatibility': True,
        })
        filename = self.image._make_image_filename(".co:ver", "/music/albumart",
            self.metadata, win_compat=True, win_shorten_path=False)
        self.compare_paths('/music/albumart/_co_ver', filename)

    def test_make_image_filename_win_shorten_path(self):
        requested_path = "/" + 300 * "a" + "/cover"
        expected_path = "/" + 226 * "a" + "/cover"
        filename = self.image._make_image_filename(requested_path, "/music/albumart",
            self.metadata, win_compat=False, win_shorten_path=True)
        self.compare_paths(expected_path, filename)

    def test_make_image_filename_win_shorten_path_too_long_base_path(self):
        base_path = '/' + 244*'a'
        with self.assertRaises(WinPathTooLong):
            self.image._make_image_filename("cover", base_path,
                self.metadata, win_compat=False, win_shorten_path=True)


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

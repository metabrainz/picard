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

from picard import config
from picard.const.sys import IS_WIN
from picard.coverart.image import (
    CoverArtImage,
    CoverArtImageIOError,
    LocalFileCoverArtImage,
)
from picard.metadata import Metadata


IGNORE_MARKER = "\n"


def create_image(extra_data, types=None, support_types=False,
                 support_multi_types=False, comment=None):
    return CoverArtImage(
        data=create_fake_png(extra_data),
        types=types,
        comment=comment,
        support_types=support_types,
        support_multi_types=support_multi_types,
    )


class CoverArtImageTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        settings = {
            'ascii_filenames': False,
            'image_type_as_filename': False,
            'cover_image_filename': 'cover',
            'enabled_plugins': [],
            'save_images_overwrite': True,
            'windows_compatibility': False,
        }
        self.set_config_values(settings)

    def test_is_front_image_no_types(self):
        image = create_image(b'a')
        self.assertTrue(image.is_front_image())
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

    def test_maintype(self):
        self.assertEqual("front", create_image(b'a').maintype)
        self.assertEqual("front", create_image(b'a', support_types=True).maintype)
        self.assertEqual("front", create_image(b'a', types=["back", "front"], support_types=True).maintype)
        self.assertEqual("back", create_image(b'a', types=["back", "medium"], support_types=True).maintype)
        self.assertEqual("front", create_image(b'a', types=["back", "medium"], support_types=False).maintype)

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

    def test_delete_file_removed(self):
        """Test unexpected removal of image temporary file"""
        # Create 2 images sharing same temporary file (same payload, different comment)
        data = create_fake_png(b'test')
        image1 = CoverArtImage(data=data, comment='1')
        image2 = CoverArtImage(data=data, comment='2')
        # Ensure both images share same content
        self.assertEqual(image2.datahash.data, data)
        self.assertEqual(image1.datahash.data, image2.datahash.data)
        # simulate removal of temporary file by external command
        self.assertTrue(os.path.exists(image2.datahash._filename))
        os.unlink(image2.datahash._filename)
        self.assertFalse(os.path.exists(image2.datahash._filename))
        # the following should handle this case without raising an exception
        image2.datahash.delete_file()
        self.assertIsNone(image2.datahash._filename)
        self.assertIsNone(image2.datahash.data)
        with self.assertRaises(CoverArtImageIOError):
            unused = image1.data  # noqa: F841

    def test_coverartimage_image_as_string(self):
        image = CoverArtImage(data=None)
        self.assertEqual(image.imageinfo_as_string(), '')
        image = create_image(b'a')
        self.assertEqual(
            image.imageinfo_as_string(),
            ('w=100 h=100 mime=image/png ext=.png datalen=25 file=%s' %
             image.tempfile_filename)
        )

    def test_coverartimage_url_with_query(self):
        image = CoverArtImage(url='http://example.com/image.jpg?size=1024')
        self.assertEqual(image.path, '/image.jpg?size=1024')

    def test_coverartimage_source(self):
        class CAImage(CoverArtImage):
            sourceprefix = 'TEST'
        image = CAImage(url='http://example.com/image.jpg')
        self.assertEqual(image.source, 'TEST: http://example.com/image.jpg')
        image = CAImage()
        self.assertEqual(image.source, 'TEST')

    def test_coverartimage_str_repr(self):
        image = CoverArtImage(url='url',
                              types=['front'], comment='comment')
        image.is_front = True
        self.assertEqual(
            str(image),
            "Image from url of type front and comment 'comment'"
        )
        self.assertEqual(
            repr(image),
            "CoverArtImage(url='url', types=['front'], support_types=False, "
            "support_multi_types=False, is_front=True, comment='comment')"
        )

    @staticmethod
    def _mkdummyfile(filename, tmpdir, images, metadata, marker=None):
        if marker is None:
            marker = IGNORE_MARKER
        with open(os.path.join(tmpdir, filename), 'wb') as f:
            f.write(marker.encode('ascii'))
            f.flush()
            os.fsync(f.fileno())

    def _save_images(self, cases, prerun=None, tests=None):
        config.setting.update(cases['options'])
        expected = cases['expected']
        types = cases.get('types', None)
        is_front = cases.get('is_front', None)

        keys = ['1', '2']
        metadata = Metadata({'foo': 'bar', 'nada': ''})
        images = dict()
        if types is None:
            for key in keys:
                images[key] = create_image(key.encode('ascii'))
        else:
            for key in keys:
                images[key] = create_image(key.encode('ascii'), types=types[key],
                                  support_types=True,
                                  support_multi_types=True)
        for key in keys:
            images[key].can_be_saved_to_metadata = True
            if is_front:
                images[key].is_front = is_front.get(key, False)

        tmpdir = self.mktmpdir()

        def listdir(tmpdir):
            result = dict()
            for name in sorted(os.listdir(tmpdir)):
                path = os.path.join(tmpdir, name)
                if os.path.isdir(path):
                    subresult = listdir(path)
                    for subname in subresult:
                        result[name + '/' + subname] = subresult[subname]
                else:
                    # read image file content
                    with open(path, 'rb') as f:
                        # last byte is a marker matching image number
                        marker = f.read()[-1]
                        if marker >= ord('0'):
                            # we intentionnaly ignore files with markers like
                            # "\n" to ease tests
                            result[name] = chr(marker)
            return result

        if prerun is not None:
            prerun(tmpdir, images, metadata)

        if tests is None:
            def default_tests(tmpdir, images, metadata, expected):
                for key in sorted(images):
                    images[key].can_be_saved_to_disk = False
                    images[key].save(tmpdir, metadata)
                self.assertEqual(listdir(tmpdir), expected[1])

                images['1'].can_be_saved_to_disk = True
                images['1'].save(tmpdir, metadata)
                self.assertEqual(listdir(tmpdir), expected[2])

                images['2'].can_be_saved_to_disk = True
                images['2'].save(tmpdir, metadata)
                self.assertEqual(listdir(tmpdir), expected[3])

            tests = default_tests

        tests(tmpdir, images, metadata, expected)

    def test_save_notype_1(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': 'cover',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover (1).png': '2', 'cover.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_2(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': 'folder',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'folder.png': '1'},
                3: {'folder (1).png': '2', 'folder.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_3(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'folder',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'folder.png': '1'},
                3: {'folder (1).png': '2', 'folder.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_4(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': 'folder',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {},
                2: {'folder.png': '1'},
                3: {'folder.png': '2'},
            },
        }
        self._save_images(cases)

    def test_save_notype_5(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'x%foo%',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'xbar.png': '1'},
                3: {'xbar (1).png': '2', 'xbar.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_6(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': '%nada%',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover (1).png': '2', 'cover.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_7(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'subdir/%foo%',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'subdir/bar.png': '1'},
                3: {'subdir/bar (1).png': '2', 'subdir/bar.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_8(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'subdir/%foo%/%nada%/%foo%/../%foo%',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'subdir/bar/bar.png': '1'},
                3: {'subdir/bar/bar (1).png': '2', 'subdir/bar/bar.png': '1'},
            },
        }
        self._save_images(cases)

    def test_save_notype_9(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'subdir/folder',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'subdir/folder.png': '1'},
                3: {'subdir/folder (1).png': '2', 'subdir/folder.png': '1'},
            },
        }

        def prerun(tmpdir, images, metadata):
            # we create a file with same name of the sub-directory to be created
            self._mkdummyfile('subdir', tmpdir, images, metadata)

        def tests(tmpdir, images, metadata, expected):
            keys = sorted(images)
            images[keys[0]].can_be_saved_to_disk = True
            with self.assertRaises(CoverArtImageIOError):
                images[keys[0]].save(tmpdir, metadata)

        self._save_images(cases, prerun=prerun, tests=tests)

    def test_save_types_1(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': 'cover',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover (1).png': '2', 'cover.png': '1'},
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            }
        }
        self._save_images(cases)

    def test_save_types_overwrite_1(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': 'cover',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover.png': '2'},
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            }
        }
        self._save_images(cases)

    def test_save_types_2(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'back.png': '2', 'cover.png': '1'},
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            }
        }
        self._save_images(cases)

    def test_save_types_overwrite_2(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'back.png': '2', 'cover.png': '1'},
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            }
        }
        self._save_images(cases)

    def test_save_types_3(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover (1).png': '2', 'cover.png': '1'}
            },
            'types': {
                '1': ['front'],
                '2': ['front'],
            }
        }
        self._save_images(cases)

    def test_save_types_overwrite_3(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {},
                2: {'cover.png': '1'},
                3: {'cover.png': '2'}
            },
            'types': {
                '1': ['front'],
                '2': ['front'],
            }
        }
        self._save_images(cases)

    def test_save_types_4(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': False,
            },
            'expected': {
                1: {},
                2: {'front.png': '1'},
                3: {'cover.png': '2', 'front.png': '1'},  # FIXME: is this what we expect?
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            },
            'is_front': {
                '1': False,
                '2': True,
            },
        }
        self._save_images(cases)

    def test_save_types_overwrite_4(self):
        cases = {
            'options': {
                'image_type_as_filename': True,
                'cover_image_filename': 'cover',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {},
                2: {'front.png': '1'},
                3: {'cover.png': '2', 'front.png': '1'},  # FIXME: is this what we expect?
            },
            'types': {
                '1': ['front'],
                '2': ['back'],
            },
            'is_front': {
                '1': False,
                '2': True,
            },
        }
        self._save_images(cases)

    def test_save_types_overwrite_5(self):
        cases = {
            'options': {
                'image_type_as_filename': False,
                'cover_image_filename': '$if($eq(%coverart_maintype%,{{cover}}),cover,%coverart_maintype%)',
                'save_images_overwrite': True,
            },
            'expected': {
                1: {'front.png': '9'},
                2: {'front.png': '1'},
                3: {'back.png': '2', 'front.png': '1'},  # FIXME: is this what we expect?
            },
            'types': {
                '1': ['front', 'booklet'],
                '2': ['back', 'booklet'],
            },
            'is_front': {
                '1': True,
                '2': False,
            },
        }

        def prerun(tmpdir, images, metadata):
            # we create a preexisting 'front.png' file
            self._mkdummyfile('front.png', tmpdir, images, metadata, marker='9')

        self._save_images(cases, prerun=prerun)

    def test_normalized_types(self):
        image = create_image(b'a', types=["front", 'back'], support_types=True, support_multi_types=True)
        self.assertEqual(image.normalized_types(), ['back', 'front'])

        image = create_image(b'a')
        self.assertEqual(image.normalized_types(), ['front'])

        image.is_front = False
        self.assertEqual(image.normalized_types(), ['-'])

    def test_types_as_string(self):
        image = create_image(b'a', types=["front", 'back'], support_types=True, support_multi_types=True)
        self.assertEqual(image.types_as_string(translate=False, separator=';'),
                         'back;front')
        # FIXME: translate=True


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

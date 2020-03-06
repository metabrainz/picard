# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
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

from picard import config
from picard.coverart.image import (
    CoverArtImage,
    TagCoverArtImage,
)
import picard.formats
from picard.metadata import Metadata

from .common import (
    CommonTests,
    load_metadata,
    save_and_load_metadata,
    skipUnlessTestfile,
)


def file_save_image(filename, image):
    f = picard.formats.open_(filename)
    metadata = Metadata(images=[image])
    f._save(filename, metadata)


def load_coverart_file(filename):
    with open(os.path.join('test', 'data', filename), 'rb') as f:
        return f.read()


class DummyUnsupportedCoverArt(CoverArtImage):
    def __init__(self, data=b'', mimetype='image/unknown'):
        super().__init__()
        self.mimetype = mimetype
        self.width = 100
        self.height = 100
        self.extension = '.cvr'
        self.set_data(data)

    def set_data(self, data):
        self._data = data
        self.datalength = len(data)

    @property
    def data(self):
        return self._data


# prevent unittest to run tests in those classes
class CommonCoverArtTests:

    class CoverArtTestCase(CommonTests.BaseFileTestCase):

        supports_types = True

        def setUp(self):
            super().setUp()
            self.jpegdata = load_coverart_file('mb.jpg')
            self.pngdata = load_coverart_file('mb.png')

        @skipUnlessTestfile
        def test_cover_art(self):
            source_types = ["front", "booklet"]
            # Use reasonable large data > 64kb.
            # This checks a mutagen error with ASF files.
            payload = b"a" * 1024 * 128
            tests = [
                CoverArtImage(data=self.jpegdata + payload, types=source_types),
                CoverArtImage(data=self.pngdata + payload, types=source_types),
            ]
            for test in tests:
                file_save_image(self.filename, test)
                loaded_metadata = load_metadata(self.filename)
                image = loaded_metadata.images[0]
                self.assertEqual(test.mimetype, image.mimetype)
                self.assertEqual(test, image)

        def test_cover_art_with_types(self):
            expected = set('abcdefg'[:]) if self.supports_types else set('a')
            loaded_metadata = save_and_load_metadata(self.filename, self._cover_metadata())
            found = set([chr(img.data[-1]) for img in loaded_metadata.images])
            self.assertEqual(expected, found)

        @skipUnlessTestfile
        def test_cover_art_types_only_one_front(self):
            config.setting['embed_only_one_front_image'] = True
            loaded_metadata = save_and_load_metadata(self.filename, self._cover_metadata())
            self.assertEqual(1, len(loaded_metadata.images))
            self.assertEqual(ord('a'), loaded_metadata.images[0].data[-1])

        @skipUnlessTestfile
        def test_unsupported_image_format(self):
            metadata = Metadata()
            # Save an image with unsupported mimetype
            metadata.images.append(DummyUnsupportedCoverArt(b'unsupported', 'image/unknown'))
            # Save an image with supported mimetype, but invalid data
            metadata.images.append(DummyUnsupportedCoverArt(b'unsupported', 'image/png'))
            loaded_metadata = save_and_load_metadata(self.filename, metadata)
            self.assertEqual(0, len(loaded_metadata.images))

        def _cover_metadata(self):
            imgdata = self.jpegdata
            metadata = Metadata()
            metadata.images.append(
                TagCoverArtImage(
                    file='a',
                    tag='a',
                    data=imgdata + b'a',
                    support_types=True,
                    types=['booklet', 'front'],
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='b',
                    tag='b',
                    data=imgdata + b'b',
                    support_types=True,
                    types=['back'],
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='c',
                    tag='c',
                    data=imgdata + b'c',
                    support_types=True,
                    types=['front'],
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='d',
                    tag='d',
                    data=imgdata + b'd',
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='e',
                    tag='e',
                    data=imgdata + b'e',
                    is_front=False
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='f',
                    tag='f',
                    data=imgdata + b'f',
                    types=['front']
                )
            )
            metadata.images.append(
                TagCoverArtImage(
                    file='g',
                    tag='g',
                    data=imgdata + b'g',
                    types=['back'],
                    is_front=True
                )
            )
            return metadata

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Philipp Wolfer
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
    skipUnlessTestfile,
)


def file_save_image(filename, image):
    f = picard.formats.open_(filename)
    metadata = Metadata(images=[image])
    f._save(filename, metadata)


def load_coverart_file(filename):
    with open(os.path.join('test', 'data', filename), 'rb') as f:
        return f.read()


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
                f = picard.formats.open_(self.filename)
                loaded_metadata = f._load(self.filename)
                image = loaded_metadata.images[0]
                self.assertEqual(test.mimetype, image.mimetype)
                self.assertEqual(test, image)

        def test_cover_art_with_types(self):
            expected = set('abcdefg'[:]) if self.supports_types else set('a')
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            found = set([chr(img.data[-1]) for img in loaded_metadata.images])
            self.assertEqual(expected, found)

        @skipUnlessTestfile
        def test_cover_art_types_only_one_front(self):
            config.setting['embed_only_one_front_image'] = True
            f = picard.formats.open_(self.filename)
            f._save(self.filename, self._cover_metadata())

            f = picard.formats.open_(self.filename)
            loaded_metadata = f._load(self.filename)
            self.assertEqual(1, len(loaded_metadata.images))
            self.assertEqual(ord('a'), loaded_metadata.images[0].data[-1])

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

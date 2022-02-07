# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


import os
import unittest

from picard import config
from picard.formats.ac3 import AC3File
from picard.formats.mutagenext.ac3 import native_ac3
from picard.metadata import Metadata

from .common import (
    CommonTests,
    load_metadata,
    save_and_load_metadata,
)
from .test_apev2 import CommonApeTests


class AC3WithAPETest(CommonApeTests.ApeTestCase):
    testfile = 'test.ac3'
    supports_ratings = False
    expected_info = {
        'length': 106,
        '~bitrate': '192.0',
        '~sample_rate': '44100',
        '~channels': '2',
    }
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        config.setting['ac3_save_ape'] = True
        config.setting['remove_ape_from_ac3'] = True

    @unittest.skipUnless(native_ac3, "mutagen.ac3 not available")
    def test_info(self):
        super().test_info()


class AC3NoTagsTest(CommonTests.BaseFileTestCase):
    testfile = 'test-apev2.ac3'

    def setUp(self):
        super().setUp()
        config.setting['ac3_save_ape'] = False
        config.setting['remove_ape_from_ac3'] = False

    def test_load_but_do_not_save_tags(self):
        metadata = load_metadata(self.filename)
        self.assertEqual('Test AC3 with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])
        metadata['artist'] = 'Foo'
        metadata['title'] = 'Bar'
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('Test AC3 with APEv2 tags', metadata['title'])
        self.assertEqual('The Artist', metadata['artist'])

    def test_remove_ape_tags(self):
        config.setting['remove_ape_from_ac3'] = True
        metadata = Metadata({
            'artist': 'Foo'
        })
        metadata = save_and_load_metadata(self.filename, metadata)
        self.assertEqual('AC-3', metadata['~format'])
        self.assertNotIn('title', metadata)
        self.assertNotIn('artist', metadata)

    def test_info_format(self):
        metadata = load_metadata(os.path.join('test', 'data', 'test.ac3'))
        self.assertEqual('AC-3', metadata['~format'])
        metadata = load_metadata(os.path.join('test', 'data', 'test-apev2.ac3'))
        self.assertEqual('AC-3 (APEv2)', metadata['~format'])
        if native_ac3:
            metadata = load_metadata(os.path.join('test', 'data', 'test.eac3'))
            self.assertEqual('Enhanced AC-3', metadata['~format'])

    def test_supports_tag(self):
        config.setting['ac3_save_ape'] = True
        self.assertTrue(AC3File.supports_tag('title'))
        config.setting['ac3_save_ape'] = False
        self.assertFalse(AC3File.supports_tag('title'))


@unittest.skipUnless(native_ac3, "mutagen.ac3 not available")
class EAC3Test(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.eac3'
    expected_info = {
        '~format': 'Enhanced AC-3',
        'length': 107,
        '~sample_rate': '44100',
        '~channels': '2',
    }
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        config.setting['ac3_save_ape'] = True

    def test_bitrate(self):
        # For EAC3 bitrate is calculated and often a fractional value
        metadata = load_metadata(os.path.join('test', 'data', 'test.ac3'))
        self.assertAlmostEqual(192.0, float(metadata['~bitrate']))

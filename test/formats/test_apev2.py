# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019, 2021 Philipp Wolfer
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

from mutagen.apev2 import (
    BINARY,
    APEValue,
)

from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard import config
from picard.formats import (
    apev2,
    open_,
)
from picard.formats.mutagenext.tak import native_tak
from picard.metadata import Metadata

from .common import (
    TAGS,
    CommonTests,
    load_metadata,
    load_raw,
    save_and_load_metadata,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
from .coverart import CommonCoverArtTests


VALID_KEYS = [
    ' valid Key}',
    '{ $ome tag~}',
    'xx',
    'x' * 255,
]

INVALID_KEYS = [
    'invalid\x7fkey',
    'invalid\x19key',
    '',
    'x',
    'x' * 256,
    'ID3',
    'TAG',
    'OggS',
    'MP+',
]


SUPPORTED_TAGS = list(set(TAGS.keys()) - apev2.UNSUPPORTED_TAGS)


class CommonApeTests:

    class ApeTestCase(CommonTests.TagFormatsTestCase):
        def setup_tags(self):
            super().setup_tags()
            self.unsupported_tags['r128_album_gain'] = '-2857'
            self.unsupported_tags['r128_track_gain'] = '-2857'

        def test_supports_tags(self):
            supports_tag = self.format.supports_tag
            for key in VALID_KEYS + SUPPORTED_TAGS:
                self.assertTrue(supports_tag(key), '%r should be supported' % key)
            for key in INVALID_KEYS + list(apev2.UNSUPPORTED_TAGS):
                self.assertFalse(supports_tag(key), '%r should be unsupported' % key)

        @skipUnlessTestfile
        def test_invalid_coverart(self):
            metadata = {
                'Cover Art (Front)': APEValue(b'filename.png\0NOTPNGDATA', BINARY)
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))

        @skipUnlessTestfile
        def test_clear_tags_preserve_images_all(self):
            imagedata = APEValue(b'filename.png\0' + create_fake_png(b'a'), BINARY)
            save_raw(self.filename, {
                'Cover Art (Front)': imagedata,
                'Cover Art': imagedata,
                'Cover Art (foo)': imagedata,
                'cover art (bar)': imagedata,
            })
            config.setting['clear_existing_tags'] = True
            config.setting['preserve_images'] = True
            metadata = save_and_load_metadata(self.filename, Metadata())
            self.assertEqual(4, len(metadata.images))
            config.setting['preserve_images'] = False
            metadata = save_and_load_metadata(self.filename, Metadata())
            self.assertEqual(0, len(metadata.images))

        def test_supports_extended_tags(self):
            performer_tag = "performer:accordéon clavier « boutons »"
            self.assertTrue(self.format.supports_tag(performer_tag))
            self.assertTrue(self.format.supports_tag('lyrics:foó'))
            self.assertTrue(self.format.supports_tag('comment:foó'))

        def test_case_insensitive_reading(self):
            self._read_case_insensitive_tag('artist', 'Artist')
            self._read_case_insensitive_tag('albumartist', 'Album Artist')
            self._read_case_insensitive_tag('performer:', 'Performer')
            self._read_case_insensitive_tag('tracknumber', 'Track')
            self._read_case_insensitive_tag('discnumber', 'Disc')

        @skipUnlessTestfile
        def test_ci_tags_preserve_case(self):
            # Ensure values are not duplicated on repeated save and are saved
            # case preserving.
            for name in ('CUStom', 'ARtist'):
                tags = {}
                tags[name] = 'foo'
                save_raw(self.filename, tags)
                loaded_metadata = load_metadata(self.filename)
                loaded_metadata[name.lower()] = 'bar'
                save_metadata(self.filename, loaded_metadata)
                raw_metadata = dict(load_raw(self.filename))
                self.assertIn(name, raw_metadata)
                self.assertEqual(
                    raw_metadata[name],
                    loaded_metadata[name.lower()])
                self.assertEqual(1, len(raw_metadata[name]))
                self.assertNotIn(name.upper(), raw_metadata)

        def _read_case_insensitive_tag(self, name, ape_name):
            upper_ape_name = ape_name.upper()
            metadata = {
                upper_ape_name: 'Some value'
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(metadata[upper_ape_name], loaded_metadata[name])
            save_metadata(self.filename, loaded_metadata)
            raw_metadata = load_raw(self.filename)
            self.assertIn(upper_ape_name, raw_metadata.keys())
            self.assertEqual(metadata[upper_ape_name], raw_metadata[ape_name])


class MonkeysAudioTest(CommonApeTests.ApeTestCase):
    testfile = 'test.ape'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }
    unexpected_info = ['~video']


class WavPackTest(CommonApeTests.ApeTestCase):
    testfile = 'test.wv'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }
    unexpected_info = ['~video']

    @skipUnlessTestfile
    def test_save_wavpack_correction_file(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = False
        config.setting['ascii_filenames'] = False
        config.setting['windows_compatibility'] = False
        config.setting['dont_write_tags'] = True
        config.setting['preserve_timestamps'] = False
        config.setting['delete_empty_dirs'] = False
        config.setting['save_images_to_files'] = False
        config.setting['file_renaming_scripts'] = {'test_id': {'script': '%title%'}}
        config.setting['selected_file_naming_script_id'] = 'test_id'
        # Create dummy WavPack correction file
        source_file_wvc = self.filename + 'c'
        open(source_file_wvc, 'a').close()
        # Open file and rename it
        f = open_(self.filename)
        metadata = Metadata({'title': 'renamed_' + os.path.basename(self.filename)})
        self.assertTrue(os.path.isfile(self.filename))
        target_file_wv = f._save_and_rename(self.filename, metadata)
        target_file_wvc = target_file_wv + 'c'
        # Register cleanups
        self.addCleanup(os.unlink, target_file_wv)
        self.addCleanup(os.unlink, target_file_wvc)
        # Check both the WavPack file and the correction file got moved
        self.assertFalse(os.path.isfile(self.filename))
        self.assertFalse(os.path.isfile(source_file_wvc))
        self.assertTrue(os.path.isfile(target_file_wv))
        self.assertTrue(os.path.isfile(target_file_wvc))


class MusepackSV7Test(CommonApeTests.ApeTestCase):
    testfile = 'test-sv7.mpc'
    supports_ratings = False
    expected_info = {
        'length': 91,
        '~channels': '2',
        '~sample_rate': '44100',
    }
    unexpected_info = ['~video']


class MusepackSV8Test(CommonApeTests.ApeTestCase):
    testfile = 'test-sv8.mpc'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }
    unexpected_info = ['~video']


class TAKTest(CommonApeTests.ApeTestCase):
    testfile = 'test.tak'
    supports_ratings = False
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        if native_tak:
            self.expected_info = {
                'length': 82,
                '~channels': '2',
                '~sample_rate': '44100',
                '~bits_per_sample': '16'
            }


class OptimFROGLosslessTest(CommonApeTests.ApeTestCase):
    testfile = 'test.ofr'
    supports_ratings = False
    expected_info = {
        'length': 0,
        '~channels': '2',
        '~sample_rate': '48000',
    }
    unexpected_info = ['~video']

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG Lossless Audio')


class OptimFROGDUalStreamTest(CommonApeTests.ApeTestCase):
    testfile = 'test.ofs'
    supports_ratings = False
    expected_info = {
        'length': 0,
        '~channels': '2',
        '~sample_rate': '48000',
    }
    unexpected_info = ['~video']

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG DualStream Audio')


class ApeCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.ape'
    supports_types = False


class Apev2UtilTest(PicardTestCase):
    def test_is_valid_key(self):
        for key in VALID_KEYS:
            self.assertTrue(apev2.is_valid_key(key), '%r is valid' % key)
        for key in INVALID_KEYS:
            self.assertFalse(apev2.is_valid_key(key), '%r is invalid' % key)

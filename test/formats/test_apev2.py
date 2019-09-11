import os

from mutagen.apev2 import (
    BINARY,
    APEValue,
)

from test.picardtestcase import PicardTestCase

from picard import config
from picard.formats import (
    apev2,
    open_,
)
from picard.metadata import Metadata

from .common import (
    TAGS,
    CommonTests,
    load_metadata,
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


SUPPORTED_TAGS = list(set(TAGS.keys()) - set(apev2.UNSUPPORTED_TAGS))


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
            for key in INVALID_KEYS + apev2.UNSUPPORTED_TAGS:
                self.assertFalse(supports_tag(key), '%r should be unsupported' % key)

        @skipUnlessTestfile
        def test_invalid_coverart(self):
            metadata = {
                'Cover Art (Front)': APEValue(b'filename.png\0NOTPNGDATA', BINARY)
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))


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
        config.setting['file_naming_format'] = '%title%'
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

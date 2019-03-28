from test.picardtestcase import PicardTestCase

from picard.formats import apev2
from .common import (
    CommonTests,
    load_metadata,
    TAGS,
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
        def test_supports_tags(self):
            supports_tag = self.format.supports_tag
            for key in VALID_KEYS + SUPPORTED_TAGS:
                self.assertTrue(supports_tag(key), '%r should be supported' % key)
            for key in INVALID_KEYS + apev2.UNSUPPORTED_TAGS:
                self.assertFalse(supports_tag(key), '%r should be unsupported' % key)


class MonkeysAudioTest(CommonApeTests.ApeTestCase):
    testfile = 'test.ape'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }


class WavPackTest(CommonApeTests.ApeTestCase):
    testfile = 'test.wv'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV7Test(CommonApeTests.ApeTestCase):
    testfile = 'test-sv7.mpc'
    supports_ratings = False
    expected_info = {
        'length': 91,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV8Test(CommonApeTests.ApeTestCase):
    testfile = 'test-sv8.mpc'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class TAKTest(CommonApeTests.ApeTestCase):
    testfile = 'test.tak'
    supports_ratings = False


class OptimFROGLosslessTest(CommonApeTests.ApeTestCase):
    testfile = 'test.ofr'
    supports_ratings = False
    expected_info = {
        'length': 0,
        '~channels': '2',
        '~sample_rate': '48000',
    }

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

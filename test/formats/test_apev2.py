from .common import (
    CommonTests,
    load_metadata,
)
from .coverart import CommonCoverArtTests


class MonkeysAudioTest(CommonTests.TagFormatsTestCase):
    testfile = 'test.ape'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }


class WavPackTest(CommonTests.TagFormatsTestCase):
    testfile = 'test.wv'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV7Test(CommonTests.TagFormatsTestCase):
    testfile = 'test-sv7.mpc'
    supports_ratings = False
    expected_info = {
        'length': 91,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV8Test(CommonTests.TagFormatsTestCase):
    testfile = 'test-sv8.mpc'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class TAKTest(CommonTests.TagFormatsTestCase):
    testfile = 'test.tak'
    supports_ratings = False


class OptimFROGLosslessTest(CommonTests.TagFormatsTestCase):
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


class OptimFROGDUalStreamTest(CommonTests.TagFormatsTestCase):
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

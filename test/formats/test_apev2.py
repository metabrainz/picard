from .common import (
    CommonTests,
    load_metadata,
)


class MonkeysAudioTest(CommonTests.TagFormatsTest):
    testfile = 'test.ape'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }


class WavPackTest(CommonTests.TagFormatsTest):
    testfile = 'test.wv'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV7Test(CommonTests.TagFormatsTest):
    testfile = 'test-sv7.mpc'
    supports_ratings = False
    expected_info = {
        'length': 91,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class MusepackSV8Test(CommonTests.TagFormatsTest):
    testfile = 'test-sv8.mpc'
    supports_ratings = False
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class TAKTest(CommonTests.TagFormatsTest):
    testfile = 'test.tak'
    supports_ratings = False


class OptimFROGLosslessTest(CommonTests.TagFormatsTest):
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


class OptimFROGDUalStreamTest(CommonTests.TagFormatsTest):
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

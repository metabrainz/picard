from .common import (
    CommonTests,
    load_metadata,
)


class WavPackTest(CommonTests.TagFormatsTest):
    testfile = 'test.wv'
    supports_ratings = False


class MusepackSV7Test(CommonTests.TagFormatsTest):
    testfile = 'test-sv7.mpc'
    supports_ratings = False


class MusepackSV8Test(CommonTests.TagFormatsTest):
    testfile = 'test-sv8.mpc'
    supports_ratings = False


class MonkeysAudioTest(CommonTests.TagFormatsTest):
    testfile = 'test.ape'
    supports_ratings = False


class TAKTest(CommonTests.TagFormatsTest):
    testfile = 'test.tak'
    supports_ratings = False


class OptimFROGLosslessTest(CommonTests.TagFormatsTest):
    testfile = 'test.ofr'
    supports_ratings = False

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG Lossless Audio')


class OptimFROGDUalStreamTest(CommonTests.TagFormatsTest):
    testfile = 'test.ofs'
    supports_ratings = False

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertEqual(metadata['~format'], 'OptimFROG DualStream Audio')

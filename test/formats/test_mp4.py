from picard.formats import ext_to_format

from .common import (
    CommonTests,
    load_metadata,
)
from .coverart import CommonCoverArtTests


class MP4Test(CommonTests.TagFormatsTestCase):
    testfile = 'test.m4a'
    supports_ratings = False
    expected_info = {
        'length': 106,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '14.376',
        '~bits_per_sample': '16',
    }

    def test_supports_tag(self):
        fmt = ext_to_format(self.testfile_ext[1:])
        self.assertTrue(fmt.supports_tag('copyright'))
        self.assertTrue(fmt.supports_tag('compilation'))
        self.assertTrue(fmt.supports_tag('bpm'))
        self.assertTrue(fmt.supports_tag('djmixer'))
        self.assertTrue(fmt.supports_tag('discnumber'))
        self.assertTrue(fmt.supports_tag('lyrics:lead'))
        self.assertTrue(fmt.supports_tag('~length'))

    def test_format(self):
        metadata = load_metadata(self.filename)
        self.assertIn('AAC LC', metadata['~format'])


class Mp4CoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.m4a'

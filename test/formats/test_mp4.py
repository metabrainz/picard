from picard.formats import ext_to_format
from .common import CommonTests


class MP4Test(CommonTests.TagFormatsTest):
    testfile = 'test.m4a'
    supports_ratings = False

    def test_supports_tag(self):
        fmt = ext_to_format(self.testfile_ext[1:])
        self.assertTrue(fmt.supports_tag('copyright'))
        self.assertTrue(fmt.supports_tag('compilation'))
        self.assertTrue(fmt.supports_tag('bpm'))
        self.assertTrue(fmt.supports_tag('djmixer'))
        self.assertTrue(fmt.supports_tag('discnumber'))
        self.assertTrue(fmt.supports_tag('lyrics:lead'))
        self.assertTrue(fmt.supports_tag('~length'))

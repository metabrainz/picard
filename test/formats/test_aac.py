from .common import CommonTests


class AACTest(CommonTests.SimpleFormatsTest):
    testfile = 'test.aac'


class AACWithAPETest(CommonTests.TagFormatsTest):
    testfile = 'test-apev2.aac'
    supports_ratings = False

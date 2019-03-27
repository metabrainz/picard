from .common import CommonTests


class ASFTest(CommonTests.TagFormatsTest):
    testfile = 'test.asf'
    supports_ratings = True


class WMATest(CommonTests.TagFormatsTest):
    testfile = 'test.wma'
    supports_ratings = True

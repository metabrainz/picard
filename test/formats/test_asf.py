from .common import CommonTests
from .coverart import CommonCoverArtTests


class ASFTest(CommonTests.TagFormatsTest):
    testfile = 'test.asf'
    supports_ratings = True
    expected_info = {
        'length': 92,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '128.0',
    }


class WMATest(CommonTests.TagFormatsTest):
    testfile = 'test.wma'
    supports_ratings = True
    expected_info = {
        'length': 139,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '64.0',
    }


class AsfCoverArtTest(CommonCoverArtTests.CoverArtTest):
    testfile = 'test.asf'


class WmaCoverArtTest(CommonCoverArtTests.CoverArtTest):
    testfile = 'test.wma'

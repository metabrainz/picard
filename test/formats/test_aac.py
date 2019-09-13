from .common import CommonTests
from .test_apev2 import CommonApeTests


class AACTest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.aac'
    expected_info = {
        'length': 120,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '123.824',
    }
    unexpected_info = ['~video']


class AACWithAPETest(CommonApeTests.ApeTestCase):
    testfile = 'test-apev2.aac'
    supports_ratings = False
    expected_info = {
        'length': 120,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '123.824',
    }
    unexpected_info = ['~video']

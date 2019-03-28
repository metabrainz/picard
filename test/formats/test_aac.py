from .common import CommonTests


class AACTest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.aac'
    expected_info = {
        'length': 120,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '123.824',
    }


class AACWithAPETest(CommonTests.TagFormatsTestCase):
    testfile = 'test-apev2.aac'
    supports_ratings = False

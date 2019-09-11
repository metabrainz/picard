from .common import (
    REPLAYGAIN_TAGS,
    TAGS,
    CommonTests,
    skipUnlessTestfile,
)


class WAVTest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.wav'
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }
    unexpected_info = ['~video']

    def setUp(self):
        super().setUp()
        self.unsupported_tags = {**TAGS, **REPLAYGAIN_TAGS}

    @skipUnlessTestfile
    def test_unsupported_tags(self):
        self._test_unsupported_tags(self.unsupported_tags)

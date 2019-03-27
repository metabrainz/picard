from .common import CommonTests


class WAVTest(CommonTests.SimpleFormatsTest):
    testfile = 'test.wav'
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bits_per_sample': '16',
    }

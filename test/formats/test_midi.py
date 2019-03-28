from .common import CommonTests


class MIDITest(CommonTests.SimpleFormatsTestCase):
    testfile = 'test.mid'
    expected_info = {
        'length': 127997,
    }

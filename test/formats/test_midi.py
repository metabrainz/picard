from .common import CommonTests


class MIDITest(CommonTests.SimpleFormatsTest):
    testfile = 'test.mid'
    expected_info = {
        'length': 127997,
    }

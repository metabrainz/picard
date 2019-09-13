from .test_apev2 import CommonApeTests


class AC3WithAPETest(CommonApeTests.ApeTestCase):
    testfile = 'test.ac3'
    supports_ratings = False
    expected_info = {}
    unexpected_info = ['~video']

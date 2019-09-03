from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.formats import (
    asf,
    ext_to_format,
)

from .common import CommonTests
from .coverart import CommonCoverArtTests


# prevent unittest to run tests in those classes
class CommonAsfTests:

    class AsfTestCase(CommonTests.TagFormatsTestCase):

        def test_supports_tag(self):
            fmt = ext_to_format(self.testfile_ext[1:])
            self.assertTrue(fmt.supports_tag('copyright'))
            self.assertTrue(fmt.supports_tag('compilation'))
            self.assertTrue(fmt.supports_tag('bpm'))
            self.assertTrue(fmt.supports_tag('djmixer'))
            self.assertTrue(fmt.supports_tag('discnumber'))
            self.assertTrue(fmt.supports_tag('lyrics:lead'))
            self.assertTrue(fmt.supports_tag('~length'))
            for tag in self.replaygain_tags.keys():
                self.assertTrue(fmt.supports_tag(tag))


class ASFTest(CommonAsfTests.AsfTestCase):
    testfile = 'test.asf'
    supports_ratings = True
    expected_info = {
        'length': 92,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '128.0',
    }


class WMATest(CommonAsfTests.AsfTestCase):
    testfile = 'test.wma'
    supports_ratings = True
    expected_info = {
        'length': 139,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '64.0',
    }


class AsfUtilTest(PicardTestCase):
    def test_pack_and_unpack_image(self):
        mime = 'image/png'
        image_data = create_fake_png(b'x')
        image_type = 4
        description = 'testing'
        tag_data = asf.pack_image(mime, image_data, image_type, description)
        expected_length = 5 + 2 * len(mime) + 2 + 2 * len(description) + 2 + len(image_data)
        self.assertEqual(tag_data[0], image_type)
        self.assertEqual(len(tag_data), expected_length)
        self.assertEqual(image_data, tag_data[-len(image_data):])

        unpacked = asf.unpack_image(tag_data)
        self.assertEqual(mime, unpacked[0])
        self.assertEqual(image_data, unpacked[1])
        self.assertEqual(image_type, unpacked[2])
        self.assertEqual(description, unpacked[3])


class AsfCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.asf'


class WmaCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.wma'

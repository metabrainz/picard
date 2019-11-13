from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard.formats import (
    asf,
    ext_to_format,
)

from .common import (
    CommonTests,
    load_metadata,
    load_raw,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
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

        @skipUnlessTestfile
        def test_ci_tags_preserve_case(self):
            # Ensure values are not duplicated on repeated save and are saved
            # case preserving.
            tags = {
                'Replaygain_Album_Peak': '-6.48 dB'
            }
            save_raw(self.filename, tags)
            loaded_metadata = load_metadata(self.filename)
            loaded_metadata['replaygain_album_peak'] = '1.0'
            save_metadata(self.filename, loaded_metadata)
            raw_metadata = load_raw(self.filename)
            self.assertIn('Replaygain_Album_Peak', raw_metadata)
            self.assertEqual(raw_metadata['Replaygain_Album_Peak'][0], loaded_metadata['replaygain_album_peak'])
            self.assertEqual(1, len(raw_metadata['Replaygain_Album_Peak']))
            self.assertNotIn('REPLAYGAIN_ALBUM_PEAK', raw_metadata)


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
    unexpected_info = ['~video']


class WMVTest(CommonAsfTests.AsfTestCase):
    testfile = 'test.wmv'
    supports_ratings = True
    expected_info = {
        'length': 565,
        '~channels': '2',
        '~sample_rate': '44100',
        '~bitrate': '128.0',
        '~video': '1',
    }


class AsfUtilTest(PicardTestCase):
    test_cases = [
        # Empty MIME, description and data
        (('', b'', 2, ''), b'\x02\x00\x00\x00\x00\x00\x00\x00\x00'),
        # MIME, description set, 1 byte data
        (('M', b'x', 2, 'D'), b'\x02\x01\x00\x00\x00M\x00\x00\x00D\x00\x00\x00x'),
        # Empty MIME and description, 3 byte data
        (('', b'abc', 0, ''), b'\x00\x03\x00\x00\x00\x00\x00\x00\x00abc'),
    ]

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

    def test_pack_image(self):
        for args, expected in self.test_cases:
            self.assertEqual(expected, asf.pack_image(*args))

    def test_unpack_image(self):
        for expected, packed in self.test_cases:
            self.assertEqual(expected, asf.unpack_image(packed))

    def test_unpack_image_value_errors(self):
        self.assertRaisesRegex(ValueError, "unpack_from requires a buffer of at least 5 bytes",
                               asf.unpack_image, b'')
        self.assertRaisesRegex(ValueError, "unpack_from requires a buffer of at least 5 bytes",
                               asf.unpack_image, b'\x02\x01\x00\x00')
        self.assertRaisesRegex(ValueError, "mime: missing data",
                               asf.unpack_image, b'\x00\x00\x00\x00\x00')
        self.assertRaisesRegex(ValueError, "mime: missing data",
                               asf.unpack_image, b'\x04\x19\x00\x00\x00a\x00')
        self.assertRaisesRegex(ValueError, "desc: missing data",
                               asf.unpack_image, b'\x04\x19\x00\x00\x00a\x00\x00\x00a\x00')
        self.assertRaisesRegex(ValueError, "image data size mismatch",
                               asf.unpack_image, b'\x04\x19\x00\x00\x00a\x00\x00\x00a\x00\x00\x00x')


class AsfCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.asf'


class WmaCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.wma'

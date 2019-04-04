import logging
import os

from test.picardtestcase import PicardTestCase

from picard import (
    config,
    log,
)
from picard.coverart.image import CoverArtImage
from picard.formats import vorbis

from .common import (
    TAGS,
    CommonTests,
    load_metadata,
    load_raw,
    save_and_load_metadata,
    skipUnlessTestfile,
)
from .coverart import (
    CommonCoverArtTests,
    file_save_image,
)

VALID_KEYS = [
    ' valid Key}',
    '{ $ome tag}',
]


INVALID_KEYS = [
    'invalid=key',
    'invalid\x19key',
    'invalid~key',
]


# prevent unittest to run tests in those classes
class CommonVorbisTests:

    class VorbisTestCase(CommonTests.TagFormatsTestCase):
        def test_invalid_rating(self):
            filename = os.path.join('test', 'data', 'test-invalid-rating.ogg')
            old_log_level = log.get_effective_level()
            log.set_level(logging.ERROR)
            metadata = load_metadata(filename)
            log.set_level(old_log_level)
            self.assertEqual(metadata["~rating"], "THERATING")

        def test_supports_tags(self):
            supports_tag = self.format.supports_tag
            for key in VALID_KEYS + list(TAGS.keys()):
                self.assertTrue(supports_tag(key), '%r should be supported' % key)
            for key in INVALID_KEYS + ['']:
                self.assertFalse(supports_tag(key), '%r should be unsupported' % key)


class FLACTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.flac'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }

    @skipUnlessTestfile
    def test_preserve_waveformatextensible_channel_mask(self):
        config.setting['clear_existing_tags'] = True
        original_metadata = load_metadata(self.filename)
        self.assertEqual(original_metadata['~waveformatextensible_channel_mask'], '0x3')
        new_metadata = save_and_load_metadata(self.filename, original_metadata)
        self.assertEqual(new_metadata['~waveformatextensible_channel_mask'], '0x3')


class OggVorbisTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.ogg'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
    }


class OggSpxTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.spx'
    supports_ratings = True
    expected_info = {
        'length': 89,
        '~channels': '2',
        '~bitrate': '29.6',
    }


class OggOpusTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.opus'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
    }


class VorbisUtilTest(PicardTestCase):
    def test_sanitize_key(self):
        sanitized = vorbis.sanitize_key(' \x1f=}~')
        self.assertEqual(sanitized, ' }')

    def test_is_valid_key(self):
        for key in VALID_KEYS:
            self.assertTrue(vorbis.is_valid_key(key), '%r is valid' % key)
        for key in INVALID_KEYS:
            self.assertFalse(vorbis.is_valid_key(key), '%r is invalid' % key)


class FlacCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.flac'

    def test_set_picture_dimensions(self):
        tests = [
            CoverArtImage(data=self.jpegdata),
            CoverArtImage(data=self.pngdata),
        ]
        for test in tests:
            file_save_image(self.filename, test)
            raw_metadata = load_raw(self.filename)
            pic = raw_metadata.pictures[0]
            self.assertNotEqual(pic.width, 0)
            self.assertEqual(pic.width, test.width)
            self.assertNotEqual(pic.height, 0)
            self.assertEqual(pic.height, test.height)


class OggCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.ogg'

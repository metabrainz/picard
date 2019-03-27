import logging
import os
from test.picardtestcase import PicardTestCase

from picard import (
    config,
    log,
)
from picard.formats import vorbis
from .common import (
    CommonTests,
    load_metadata,
    save_and_load_metadata,
    skipUnlessTestfile,
)


# prevent unittest to run tests in those classes
class CommonVorbisTests:

    class VorbisTest(CommonTests.TagFormatsTest):
        def test_invalid_rating(self):
            filename = os.path.join('test', 'data', 'test-invalid-rating.ogg')
            old_log_level = log.get_effective_level()
            log.set_level(logging.ERROR)
            metadata = load_metadata(filename)
            log.set_level(old_log_level)
            self.assertEqual(metadata["~rating"], "THERATING")


class FLACTest(CommonVorbisTests.VorbisTest):
    testfile = 'test.flac'
    supports_ratings = True

    @skipUnlessTestfile
    def test_preserve_waveformatextensible_channel_mask(self):
        config.setting['clear_existing_tags'] = True
        original_metadata = load_metadata(self.filename)
        self.assertEqual(original_metadata['~waveformatextensible_channel_mask'], '0x3')
        new_metadata = save_and_load_metadata(self.filename, original_metadata)
        self.assertEqual(new_metadata['~waveformatextensible_channel_mask'], '0x3')


class OggVorbisTest(CommonVorbisTests.VorbisTest):
    testfile = 'test.ogg'
    supports_ratings = True


class OggSpxTest(CommonVorbisTests.VorbisTest):
    testfile = 'test.spx'
    supports_ratings = True


class OggOpusTest(CommonVorbisTests.VorbisTest):
    testfile = 'test.opus'
    supports_ratings = True


class VorbisUtilTest(PicardTestCase):
    def test_sanitize_key(self):
        sanitized = vorbis.sanitize_key(' \x1f=}~')
        self.assertEqual(sanitized, ' }')


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

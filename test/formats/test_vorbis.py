import base64
import logging
import os
import shutil
from tempfile import mkstemp

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
    save_raw,
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

        @skipUnlessTestfile
        def test_r128_replaygain_tags(self):
            # Vorbis files other then Opus must not support the r128_* tags
            tags = {
                'r128_album_gain': '-2857',
                'r128_track_gain': '-2857',
            }
            self._test_unsupported_tags(tags)

        @skipUnlessTestfile
        def test_invalid_metadata_block_picture_nobase64(self):
            metadata = {
                'metadata_block_picture': 'notbase64'
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))

        @skipUnlessTestfile
        def test_invalid_metadata_block_picture_noflacpicture(self):
            metadata = {
                'metadata_block_picture': base64.b64encode(b'notaflacpictureblock').decode('ascii')
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))

        @skipUnlessTestfile
        def test_legacy_coverart(self):
            metadata = {
                'coverart': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC'
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(1, len(loaded_metadata.images))
            first_image = loaded_metadata.images[0]
            self.assertEqual('image/png', first_image.mimetype)
            self.assertEqual(69, first_image.datalength)

        @skipUnlessTestfile
        def test_invalid_legacy_coverart_nobase64(self):
            metadata = {
                'coverart': 'notbase64'
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))

        @skipUnlessTestfile
        def test_invalid_legacy_coverart_noimage(self):
            metadata = {
                'coverart': base64.b64encode(b'invalidimagedata').decode('ascii')
            }
            save_raw(self.filename, metadata)
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(0, len(loaded_metadata.images))


class FLACTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.flac'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
        '~sample_rate': '44100',
        '~format': 'FLAC',
    }
    unexpected_info = ['~video']

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
    unexpected_info = ['~video']


class OggOpusTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.opus'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
    }
    unexpected_info = ['~video']

    @skipUnlessTestfile
    def test_r128_replaygain_tags(self):
        tags = {
            'r128_album_gain': '-2857',
            'r128_track_gain': '-2857',
        }
        self._test_supported_tags(tags)


class OggTheoraTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test.ogv'
    supports_ratings = True
    expected_info = {
        'length': 520,
        '~bitrate': '200.0',
        '~video': '1',
    }


class OggFlacTest(CommonVorbisTests.VorbisTestCase):
    testfile = 'test-oggflac.oga'
    supports_ratings = True
    expected_info = {
        'length': 82,
        '~channels': '2',
    }
    unexpected_info = ['~video']


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


class OggAudioVideoFileTest(PicardTestCase):
    def test_ogg_audio(self):
        self._test_file_is_type(
            vorbis.OggAudioFile,
            self._copy_file_tmp('test-oggflac.oga', '.oga'),
            vorbis.OggFLACFile)
        self._test_file_is_type(
            vorbis.OggAudioFile,
            self._copy_file_tmp('test.spx', '.oga'),
            vorbis.OggSpeexFile)
        self._test_file_is_type(
            vorbis.OggAudioFile,
            self._copy_file_tmp('test.ogg', '.oga'),
            vorbis.OggVorbisFile)

    def test_ogg_video(self):
        self._test_file_is_type(
            vorbis.OggVideoFile,
            self._copy_file_tmp('test.ogv', '.ogv'),
            vorbis.OggTheoraFile)

    def _test_file_is_type(self, factory, filename, expected_type):
        f = factory(filename)
        self.assertIsInstance(f, expected_type)

    def _copy_file_tmp(self, filename, ext):
        fd, copy = mkstemp(suffix=ext)
        self.addCleanup(os.unlink, copy)
        os.close(fd)
        shutil.copy(os.path.join('test', 'data', filename), copy)
        return copy


class OggCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.ogg'

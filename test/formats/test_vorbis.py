# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import base64
import logging
import os

from mutagen.flac import (
    Padding,
    Picture,
    VCFLACDict,
)

from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
)

from picard import (
    config,
    log,
)
from picard.coverart.image import CoverArtImage
from picard.formats import vorbis
from picard.formats.util import open_ as open_format
from picard.metadata import Metadata

from .common import (
    TAGS,
    CommonTests,
    load_metadata,
    load_raw,
    save_and_load_metadata,
    save_metadata,
    save_raw,
    skipUnlessTestfile,
)
from .coverart import (
    CommonCoverArtTests,
    file_save_image,
    load_coverart_file,
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

PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC'


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
            save_raw(self.filename, {'coverart': PNG_BASE64})
            loaded_metadata = load_metadata(self.filename)
            self.assertEqual(1, len(loaded_metadata.images))
            first_image = loaded_metadata.images[0]
            self.assertEqual('image/png', first_image.mimetype)
            self.assertEqual(69, first_image.datalength)

        @skipUnlessTestfile
        def test_clear_tags_preserve_legacy_coverart(self):
            save_raw(self.filename, {'coverart': PNG_BASE64})
            config.setting['clear_existing_tags'] = True
            config.setting['preserve_images'] = True
            metadata = save_and_load_metadata(self.filename, Metadata())
            self.assertEqual(1, len(metadata.images))
            config.setting['preserve_images'] = False
            metadata = save_and_load_metadata(self.filename, Metadata())
            self.assertEqual(0, len(metadata.images))

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

        def test_supports_extended_tags(self):
            performer_tag = "performer:accordéon clavier « boutons »"
            self.assertTrue(self.format.supports_tag(performer_tag))
            self.assertTrue(self.format.supports_tag('lyrics:foó'))
            self.assertTrue(self.format.supports_tag('comment:foó'))

        @skipUnlessTestfile
        def test_delete_totaldiscs_totaltracks(self):
            # Create a test file that contains only disctotal / tracktotal,
            # but not totaldiscs and totaltracks
            save_raw(self.filename, {
                'disctotal': '3',
                'tracktotal': '2',
            })
            metadata = Metadata()
            del metadata['totaldiscs']
            del metadata['totaltracks']
            save_metadata(self.filename, metadata)
            loaded_metadata = load_raw(self.filename)
            self.assertNotIn('disctotal', loaded_metadata)
            self.assertNotIn('totaldiscs', loaded_metadata)
            self.assertNotIn('tracktotal', loaded_metadata)
            self.assertNotIn('totaltracks', loaded_metadata)


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

    @skipUnlessTestfile
    def test_clear_tags_preserve_legacy_coverart(self):
        # FLAC does not use the cover art tags but has its separate image implementation
        pic = Picture()
        pic.data = load_coverart_file('mb.png')
        save_raw(self.filename, {
            'coverart': PNG_BASE64,
            'metadata_block_picture': base64.b64encode(pic.write()).decode('ascii')
        })
        config.setting['clear_existing_tags'] = True
        config.setting['preserve_images'] = True
        metadata = save_and_load_metadata(self.filename, Metadata())
        self.assertEqual(0, len(metadata.images))

    @skipUnlessTestfile
    def test_sort_pics_after_tags(self):
        # First save file with pic block before tags
        pic = Picture()
        pic.data = load_coverart_file('mb.png')
        f = load_raw(self.filename)
        f.metadata_blocks.insert(1, pic)
        f.save()

        # Save the file with Picard
        metadata = Metadata()
        save_metadata(self.filename, metadata)

        # Load raw file and verify picture block position
        f = load_raw(self.filename)
        tagindex = f.metadata_blocks.index(f.tags)
        haspics = False
        for b in f.metadata_blocks:
            if b.code == Picture.code:
                haspics = True
                self.assertGreater(f.metadata_blocks.index(b), tagindex)
        self.assertTrue(haspics, "Picture block expected, none found")


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

    def test_flac_sort_pics_after_tags(self):
        pic1 = Picture()
        pic2 = Picture()
        pic3 = Picture()
        tags = VCFLACDict()
        pad = Padding()

        blocks = []
        vorbis.flac_sort_pics_after_tags(blocks)
        self.assertEqual([], blocks)

        blocks = [tags]
        vorbis.flac_sort_pics_after_tags(blocks)
        self.assertEqual([tags], blocks)

        blocks = [tags, pad, pic1]
        vorbis.flac_sort_pics_after_tags(blocks)
        self.assertEqual([tags, pad, pic1], blocks)

        blocks = [pic1, pic2, tags, pad, pic3]
        vorbis.flac_sort_pics_after_tags(blocks)
        self.assertEqual([tags, pic1, pic2, pad, pic3], blocks)

        blocks = [pic1, pic2, pad, pic3]
        vorbis.flac_sort_pics_after_tags(blocks)
        self.assertEqual([pic1, pic2, pad, pic3], blocks)


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

    def test_save_large_pics(self):
        # 16 MB image
        data = create_fake_png(b"a" * 1024 * 1024 * 16)
        image = CoverArtImage(data=data)
        file_save_image(self.filename, image)
        raw_metadata = load_raw(self.filename)
        # Images with more than 16 MB cannot be saved to FLAC
        self.assertEqual(0, len(raw_metadata.pictures))


class OggAudioVideoFileTest(PicardTestCase):
    def test_ogg_audio(self):
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test-oggflac.oga', '.oga'),
            vorbis.OggFLACFile)
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test.spx', '.oga'),
            vorbis.OggSpeexFile)
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test.ogg', '.oga'),
            vorbis.OggVorbisFile)

    def test_ogg_opus(self):
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test.opus', '.oga'),
            vorbis.OggOpusFile)
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test.opus', '.ogg'),
            vorbis.OggOpusFile)

    def test_ogg_video(self):
        self._test_file_is_type(
            open_format,
            self._copy_file_tmp('test.ogv', '.ogv'),
            vorbis.OggTheoraFile)

    def _test_file_is_type(self, factory, filename, expected_type):
        f = factory(filename)
        self.assertIsInstance(f, expected_type)

    def _copy_file_tmp(self, filename, ext):
        path = os.path.join('test', 'data', filename)
        return self.copy_file_tmp(path, ext)


class OggCoverArtTest(CommonCoverArtTests.CoverArtTestCase):
    testfile = 'test.ogg'

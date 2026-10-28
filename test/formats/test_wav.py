# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2020, 2022, 2025-2026 Philipp Wolfer
# Copyright (C) 2020-2022, 2025 Laurent Monin
# Copyright (C) 2024 Suryansh Shakya
# Copyright (C) 2025 Bob Swift
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import os
import struct

from mutagen import version as mutagen_version
import mutagen.wave

from test.picardtestcase import PicardTestCase

from picard import config
from picard.formats.wav import (
    RiffListInfo,
    repair_wav_chunk_sizes,
)
from picard.metadata import Metadata

from .common import (
    load_metadata,
    save_metadata,
    skipUnlessTestfile,
)
from .test_id3 import CommonId3Tests


expected_info = {
    'length': 82,
    '~channels': '2',
    '~sample_rate': '44100',
    '~bits_per_sample': '16',
    '~filesize': '14652',
}

riff_info_tags = {
    'IART': 'the artist',
    'ICMT': 'the comment',
    'ICOP': 'the copyright',
    'ICRD': 'the date',
    'IGNR': 'the genre',
    'INAM': 'the title',
    'IPRD': 'the album',
    'ITRK': 'the tracknumber',
    'ICNT': 'the releasecountry',
    'IENC': 'the encodedby',
    'IENG': 'the engineer',
    'ILNG': 'the language',
    'IMED': 'the media',
    'IMUS': 'the composer',
    'IPRO': 'the producer',
    'IWRI': 'the writer',
}


class WAVTest(CommonId3Tests.Id3TestCase):
    testfile = 'test.wav'
    expected_info = expected_info
    unexpected_info = ('~video',)
    supports_ratings = True

    def setUp(self):
        super().setUp()
        # mutagen < 1.46 has broken bitrate calculation for WAVE files
        if mutagen_version >= (1, 46, 0):
            self.expected_info['~bitrate'] = '1411.2'

    @skipUnlessTestfile
    def test_invalid_track_and_discnumber(self):
        config.setting['write_wave_riff_info'] = False
        super().test_invalid_track_and_discnumber()

    @skipUnlessTestfile
    def test_load_riff_info_fallback(self):
        self._save_riff_info_tags()
        metadata = load_metadata(self.format_registry, self.filename)
        self.assertEqual(metadata['artist'], 'the artist')

    @skipUnlessTestfile
    def test_save_riff_info(self):
        metadata = Metadata(
            {
                'artist': 'the artist',
                'album': 'the album',
            }
        )
        save_metadata(self.format_registry, self.filename, metadata)
        info = RiffListInfo()
        info.load(self.filename)
        self.assertEqual(info['IART'], 'the artist')
        self.assertEqual(info['IPRD'], 'the album')

    @skipUnlessTestfile
    def test_delete_riff_info_tag(self):
        self._save_riff_info_tags()
        metadata = Metadata()
        del metadata['title']
        save_metadata(self.format_registry, self.filename, metadata)
        info = RiffListInfo()
        info.load(self.filename)
        self.assertEqual(info['IART'], 'the artist')
        self.assertNotIn('INAM', info)

    @skipUnlessTestfile
    def test_riff_save_and_load(self):
        self._save_riff_info_tags()
        loaded_info = RiffListInfo()
        loaded_info.load(self.filename)

        for key, value in loaded_info.items():
            self.assertEqual(riff_info_tags[key], value)

    @skipUnlessTestfile
    def test_riff_info_encoding_windows_1252(self):
        info = RiffListInfo()
        info['INAM'] = 'fooßü‰€œžŸŌš文字…'
        info.save(self.filename)
        loaded_info = RiffListInfo()
        loaded_info.load(self.filename)
        self.assertEqual('fooßü‰€œžŸOš??…', loaded_info['INAM'])

    @skipUnlessTestfile
    def test_riff_info_encoding_utf_8(self):
        info = RiffListInfo(encoding="utf-8")
        info['INAM'] = 'fooßü‰€œžŸŌš文字…'
        info.save(self.filename)
        loaded_info = RiffListInfo()
        loaded_info.load(self.filename)
        self.assertEqual(info['INAM'], loaded_info['INAM'])

    def _save_riff_info_tags(self):
        info = RiffListInfo()
        for key, value in riff_info_tags.items():
            info[key] = value
        info.save(self.filename)

    @skipUnlessTestfile
    def test_save_with_invalid_chunk_sizes(self):
        # Regression test for PICARD-3519: WAV files with bogus (oversized)
        # RIFF root and data chunk sizes must still be saveable. Without the
        # repair, saving raised struct.error because mutagen could not pack the
        # overflowing root size into the 32-bit size field.
        filename = self.copy_file_tmp(os.path.join('test', 'data', 'test-invalid-chunk-sizes.wav'), '.wav')
        metadata = Metadata({'title': 'The Title', 'artist': 'The Artist'})
        save_metadata(self.format_registry, filename, metadata)
        loaded_metadata = load_metadata(self.format_registry, filename)
        self.assertEqual(loaded_metadata['title'], 'The Title')
        self.assertEqual(loaded_metadata['artist'], 'The Artist')
        # The repaired file reports a sane (non-inflated) length again.
        self.assertLess(loaded_metadata.length, 10 * 60 * 1000)

    def test_length_with_invalid_chunk_sizes(self):
        # PICARD-3519: the displayed length must be correct on load, before the
        # file is repaired on save, and without modifying the file.
        filename = self.copy_file_tmp(os.path.join('test', 'data', 'test-invalid-chunk-sizes.wav'), '.wav')
        with open(filename, 'rb') as fileobj:
            original = fileobj.read()
        metadata = load_metadata(self.format_registry, filename)
        self.assertEqual(metadata.length, self.expected_info['length'])
        # Loading must not have modified the file.
        with open(filename, 'rb') as fileobj:
            self.assertEqual(original, fileobj.read())


class RepairWavChunkSizesTest(PicardTestCase):
    def _copy_testfile(self, name):
        return self.copy_file_tmp(os.path.join('test', 'data', name), '.wav')

    def test_repairs_bogus_sizes(self):
        filename = self._copy_testfile('test-invalid-chunk-sizes.wav')

        repair_wav_chunk_sizes(filename)

        # Root size now fits the file and the length is no longer inflated.
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as fileobj:
            self.assertEqual(struct.unpack('<I', fileobj.read(12)[4:8])[0], file_size - 8)
        info = mutagen.wave.WAVE(filename).info
        assert info is not None
        self.assertLess(info.length, 10 * 60)

    def test_leaves_valid_file_untouched(self):
        filename = self._copy_testfile('test.wav')
        with open(filename, 'rb') as fileobj:
            original = fileobj.read()

        repair_wav_chunk_sizes(filename)

        with open(filename, 'rb') as fileobj:
            self.assertEqual(original, fileobj.read())

    def test_non_riff_file_is_ignored(self):
        tmpdir = self.mktmpdir()
        filename = os.path.join(tmpdir, 'notawav.bin')
        with open(filename, 'wb') as fileobj:
            fileobj.write(b'NOTARIFFFILECONTENTS' * 4)
        repair_wav_chunk_sizes(filename)  # Must not raise.

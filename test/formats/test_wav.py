# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2020 Philipp Wolfer
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


from picard import config
from picard.formats import WAVFile
from picard.metadata import Metadata

from .common import (
    REPLAYGAIN_TAGS,
    TAGS,
    CommonTests,
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
}

if WAVFile.supports_tag('artist'):
    from picard.formats.wav import RiffListInfo

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
        expected_info = {**expected_info, **{
            '~bitrate': '352.8',
        }}
        unexpected_info = ['~video']
        supports_ratings = True

        @skipUnlessTestfile
        def test_invalid_track_and_discnumber(self):
            config.setting['write_wave_riff_info'] = False
            super().test_invalid_track_and_discnumber()

        @skipUnlessTestfile
        def test_load_riff_info_fallback(self):
            self._save_riff_info_tags()
            metadata = load_metadata(self.filename)
            self.assertEqual(metadata['artist'], 'the artist')

        @skipUnlessTestfile
        def test_save_riff_info(self):
            metadata = Metadata({
                'artist': 'the artist',
                'album': 'the album'
            })
            save_metadata(self.filename, metadata)
            info = RiffListInfo()
            info.load(self.filename)
            self.assertEqual(info['IART'], 'the artist')
            self.assertEqual(info['IPRD'], 'the album')

        @skipUnlessTestfile
        def test_delete_riff_info_tag(self):
            self._save_riff_info_tags()
            metadata = Metadata()
            del metadata['title']
            save_metadata(self.filename, metadata)
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
            info['INAM'] = 'fooßü‰€œžŸ文字'
            info.save(self.filename)
            loaded_info = RiffListInfo()
            loaded_info.load(self.filename)
            self.assertEqual('fooßü‰€œžŸ??', loaded_info['INAM'])

        @skipUnlessTestfile
        def test_riff_info_encoding_utf_8(self):
            info = RiffListInfo(encoding="utf-8")
            info['INAM'] = 'fooßü‰€œžŸ文字'
            info.save(self.filename)
            loaded_info = RiffListInfo()
            loaded_info.load(self.filename)
            self.assertEqual(info['INAM'], loaded_info['INAM'])

        def _save_riff_info_tags(self):
            info = RiffListInfo()
            for key, value in riff_info_tags.items():
                info[key] = value
            info.save(self.filename)
else:
    class WAVTest(CommonTests.SimpleFormatsTestCase):
        testfile = 'test.wav'
        expected_info = expected_info
        unexpected_info = ['~video']

        def setUp(self):
            super().setUp()
            self.unsupported_tags = {**TAGS, **REPLAYGAIN_TAGS}

        @skipUnlessTestfile
        def test_unsupported_tags(self):
            self._test_unsupported_tags(self.unsupported_tags)

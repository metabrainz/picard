# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from unittest.mock import MagicMock

from mutagen.id3 import (
    APIC,
    COMM,
    POPM,
    SYLT,
    TALB,
    TIPL,
    TIT1,
    TMCL,
    TXXX,
    USLT,
)

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.formats.id3 import ID3File
from picard.metadata import Metadata


class TestID3Load(PicardTestCase):
    """Test ID3 load processors"""

    def setUp(self):
        super().setUp()
        self.id3_file = ID3File(get_test_data_path("test.mp3"))
        self.id3_file.tagger = self.tagger

    def test_load_tit1_frame(self):
        frame = MagicMock(spec=TIT1)
        frame.FrameID = 'TIT1'
        frame.text = ['Test Work']
        metadata = Metadata()
        config_params = {'itunes_compatible': False}
        self.id3_file._load_tit1_frame(frame, metadata, config_params)
        self.assertIn('grouping', metadata)
        self.assertEqual(metadata['grouping'], 'Test Work')

    def test_load_tit1_frame_itunes(self):
        frame = MagicMock(spec=TIT1)
        frame.FrameID = 'TIT1'
        frame.text = ['Test Work']
        metadata = Metadata()
        config_params = {'itunes_compatible': True}
        self.id3_file._load_tit1_frame(frame, metadata, config_params)
        self.assertIn('work', metadata)
        self.assertEqual(metadata['work'], 'Test Work')

    def test_load_tmcl_frame(self):
        frame = MagicMock(spec=TMCL)
        frame.FrameID = 'TMCL'
        frame.people = [('performer', 'Test Artist')]
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_tmcl_frame(frame, metadata, config_params)
        self.assertIn('performer', metadata)
        self.assertEqual(metadata['performer'], 'Test Artist')

    def test_load_tipl_frame(self):
        frame = MagicMock(spec=TIPL)
        frame.FrameID = 'TIPL'
        frame.people = [('performer', 'Test Performer')]
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_tipl_frame(frame, metadata, config_params)
        self.assertIn('performer', metadata)
        self.assertEqual(metadata['performer'], 'Test Performer')

    def test_load_txxx_frame(self):
        frame = MagicMock(spec=TXXX)
        frame.FrameID = 'TXXX'
        frame.desc = 'Test Description'
        frame.text = ['Test Value']
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_txxx_frame(frame, metadata, config_params)
        self.assertIn('Test Description', metadata)
        self.assertEqual(metadata['Test Description'], 'Test Value')

    def test_load_uslt_frame(self):
        frame = MagicMock(spec=USLT)
        frame.FrameID = 'USLT'
        frame.desc = 'Test Lyrics'
        frame.text = 'These are the lyrics.'
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_uslt_frame(frame, metadata, config_params)
        self.assertIn('lyrics:Test Lyrics', metadata)
        self.assertEqual(metadata['lyrics:Test Lyrics'], 'These are the lyrics.')

    def test_load_sylt_frame(self):
        frame = MagicMock(spec=SYLT)
        frame.FrameID = 'SYLT'
        frame.type = 1
        frame.format = 2
        frame.lang = 'ENG'
        frame.desc = 'Test Lyrics'
        frame.text = [('These are the lyrics.', 0), ('etc.', 1000)]
        metadata = Metadata()
        config_params = {'file_length': 120, 'filename': 'test.mp3'}
        self.id3_file._load_sylt_frame(frame, metadata, config_params)
        self.assertIn('syncedlyrics:ENG:Test Lyrics', metadata)
        self.assertEqual(
            metadata['syncedlyrics:ENG:Test Lyrics'], '[00:00.000]<00:00.000>These are the lyrics.<00:01.000>etc.'
        )

    def test_load_sylt_frame_no_lang(self):
        frame = MagicMock(spec=SYLT)
        frame.FrameID = 'SYLT'
        frame.type = 1
        frame.format = 2
        frame.lang = ''
        frame.desc = 'Test Lyrics'
        frame.text = [('These are the lyrics.', 0), ('etc.', 1000)]
        metadata = Metadata()
        config_params = {'file_length': 120, 'filename': 'test.mp3'}
        self.id3_file._load_sylt_frame(frame, metadata, config_params)
        self.assertIn('syncedlyrics::Test Lyrics', metadata)
        self.assertEqual(
            metadata['syncedlyrics::Test Lyrics'], '[00:00.000]<00:00.000>These are the lyrics.<00:01.000>etc.'
        )

    def test_load_sylt_frame_unsupported_type(self):
        frame = MagicMock(spec=SYLT)
        frame.FrameID = 'SYLT'
        frame.type = 2
        frame.format = 2
        frame.lang = 'ENG'
        frame.desc = 'Test Lyrics'
        frame.text = [('These are the lyrics.', 0), ('etc.', 1000)]
        metadata = Metadata()
        config_params = {'file_length': 120, 'filename': 'test.mp3'}
        self.id3_file._load_sylt_frame(frame, metadata, config_params)
        self.assertEqual(len(metadata), 0)

    def test_load_sylt_frame_unsupported_format(self):
        frame = MagicMock(spec=SYLT)
        frame.FrameID = 'SYLT'
        frame.type = 1
        frame.format = 1
        frame.lang = 'ENG'
        frame.desc = 'Test Lyrics'
        frame.text = [('These are the lyrics.', 0), ('etc.', 1000)]
        metadata = Metadata()
        config_params = {'file_length': 120, 'filename': 'test.mp3'}
        self.id3_file._load_sylt_frame(frame, metadata, config_params)
        self.assertEqual(len(metadata), 0)

    def test_load_apic_frame(self):
        frame = MagicMock(spec=APIC)
        frame.FrameID = 'APIC'
        frame.type = 3
        frame.desc = 'Cover Art'
        file = get_test_data_path('mb.jpg')
        with open(file, 'rb') as f:
            frame.data = f.read()
        metadata = Metadata()
        config_params = {'filename': 'test.mp3'}
        self.id3_file._load_apic_frame(frame, metadata, config_params)
        self.assertEqual(len(metadata.images), 1)

    def test_load_popm_frame(self):
        frame = MagicMock(spec=POPM)
        frame.FrameID = 'POPM'
        frame.email = 'user@example.com'
        frame.rating = 127
        metadata = Metadata()
        config_params = {'rating_user_email': 'user@example.com', 'rating_steps': 5}
        self.id3_file._load_popm_frame(frame, metadata, config_params)
        self.assertIn('~rating', metadata)
        self.assertEqual(metadata['~rating'], '2')

        # Test with another rating_steps value
        metadata = Metadata()
        config_params = {'rating_user_email': 'user@example.com', 'rating_steps': 10}
        self.id3_file._load_popm_frame(frame, metadata, config_params)
        self.assertIn('~rating', metadata)
        self.assertEqual(metadata['~rating'], '4')

    def test_load_standard_text_frame_COMM(self):
        frame = MagicMock(spec=COMM)
        frame.FrameID = 'COMM'
        frame.lang = 'eng'
        frame.desc = 'Test Comment'
        frame.text = ['This is a test comment.']
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_standard_text_frame(frame, metadata, config_params)
        self.assertIn('comment:Test Comment', metadata)
        self.assertEqual(metadata['comment:Test Comment'], 'This is a test comment.')

    def test_load_standard_text_frame_TALB(self):
        frame = MagicMock(spec=TALB)
        frame.FrameID = 'TALB'
        frame.text = ['Title']
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_standard_text_frame(frame, metadata, config_params)
        self.assertIn('album', metadata)
        self.assertEqual(metadata['album'], 'Title')

    def test_load_tag_regex_frame_trck(self):
        frame = MagicMock()
        frame.FrameID = 'TRCK'
        frame.text = ['1/10']
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_tag_regex_frame(frame, metadata, config_params)
        self.assertIn('tracknumber', metadata)
        self.assertEqual(metadata['tracknumber'], '1')
        self.assertIn('totaltracks', metadata)
        self.assertEqual(metadata['totaltracks'], '10')

    def test_load_tag_regex_frame_tpos(self):
        frame_tpos = MagicMock()
        frame_tpos.FrameID = 'TPOS'
        frame_tpos.text = ['1/2']
        metadata = Metadata()
        config_params = {}
        self.id3_file._load_tag_regex_frame(frame_tpos, metadata, config_params)
        self.assertIn('discnumber', metadata)
        self.assertEqual(metadata['discnumber'], '1')
        self.assertIn('totaldiscs', metadata)
        self.assertEqual(metadata['totaldiscs'], '2')

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

import os
import re
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.coverart.providers.local import CoverArtProviderLocal
from picard.metadata import Metadata
from picard.util.scripttofilename import script_to_filename


class LocalCoverArtTestBase(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.provider = CoverArtProviderLocal.__new__(CoverArtProviderLocal)
        self.provider._default_types = ['front']
        self.provider._types_split_re = CoverArtProviderLocal._types_split_re
        self.provider._known_types = CoverArtProviderLocal._known_types
        self.tmpdir = self.mktmpdir()

    def _create_files(self, filenames):
        for name in filenames:
            open(os.path.join(self.tmpdir, name), 'w').close()

    def _filenames(self, results):
        return sorted(os.path.basename(r.url.toLocalFile()) for r in results)


class FindLocalImagesByScriptTest(LocalCoverArtTestBase):
    def _find(self, pattern, filepaths_done=None):
        if filepaths_done is None:
            filepaths_done = set()
        return list(self.provider.find_local_images_by_script(self.tmpdir, pattern, filepaths_done))

    def test_exact_match(self):
        self._create_files(['cover.jpg', 'back.jpg'])
        results = self._find('cover.jpg')
        self.assertEqual(['cover.jpg'], self._filenames(results))

    def test_glob_star(self):
        self._create_files(['cover.jpg', 'cover.png', 'back.jpg'])
        results = self._find('cover.*')
        self.assertEqual(['cover.jpg', 'cover.png'], self._filenames(results))

    def test_glob_question_mark(self):
        self._create_files(['cover1.jpg', 'cover2.jpg', 'cover10.jpg'])
        results = self._find('cover?.jpg')
        self.assertEqual(['cover1.jpg', 'cover2.jpg'], self._filenames(results))

    def test_case_insensitive(self):
        self._create_files(['Cover.JPG', 'COVER.png'])
        results = self._find('cover.*')
        self.assertEqual(['COVER.png', 'Cover.JPG'], self._filenames(results))

    def test_no_match(self):
        self._create_files(['back.jpg', 'inlay.png'])
        results = self._find('cover.*')
        self.assertEqual([], self._filenames(results))

    def test_deduplication(self):
        self._create_files(['cover.jpg'])
        filepath = os.path.join(self.tmpdir, 'cover.jpg')
        filepaths_done = {filepath}
        results = self._find('cover.jpg', filepaths_done)
        self.assertEqual([], self._filenames(results))

    def test_deduplication_adds_to_set(self):
        self._create_files(['cover.jpg'])
        filepaths_done = set()
        self._find('cover.jpg', filepaths_done)
        self.assertEqual(1, len(filepaths_done))

    def test_type_extraction_from_filename(self):
        self._create_files(['front.jpg', 'back.png'])
        results = self._find('*.*')
        by_name = {os.path.basename(r.url.toLocalFile()): r.types for r in results}
        self.assertIn('front', by_name['front.jpg'])
        self.assertIn('back', by_name['back.png'])

    def test_no_type_in_filename_uses_default(self):
        self._create_files(['cover.jpg'])
        results = self._find('cover.*')
        self.assertEqual(['front'], results[0].types)


class FindLocalImagesRegexTest(LocalCoverArtTestBase):
    def _find(self, regex):
        match_re = re.compile(regex, re.IGNORECASE)
        return list(self.provider.find_local_images(self.tmpdir, match_re))

    def test_simple_match(self):
        self._create_files(['cover.jpg', 'back.jpg'])
        results = self._find(r'cover')
        self.assertEqual(['cover.jpg'], self._filenames(results))

    def test_case_insensitive(self):
        self._create_files(['Cover.JPG', 'FRONT.png'])
        results = self._find(r'front')
        self.assertEqual(['FRONT.png'], self._filenames(results))

    def test_no_match(self):
        self._create_files(['song.mp3', 'notes.txt'])
        results = self._find(r'cover')
        self.assertEqual([], self._filenames(results))

    def test_type_extraction_from_group(self):
        self._create_files(['front.jpg'])
        results = self._find(r'(front)\.jpg')
        self.assertEqual(['front.jpg'], self._filenames(results))
        self.assertIn('front', results[0].types)

    def test_type_extraction_back(self):
        self._create_files(['back.png'])
        results = self._find(r'(back)\.')
        self.assertEqual(['back.png'], self._filenames(results))
        self.assertIn('back', results[0].types)

    def test_no_group_uses_default_types(self):
        self._create_files(['cover.jpg'])
        results = self._find(r'cover\.jpg')
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertEqual(['front'], results[0].types)

    def test_multiple_matches(self):
        self._create_files(['cover.jpg', 'cover.png', 'back.jpg'])
        results = self._find(r'cover\.')
        self.assertEqual(['cover.jpg', 'cover.png'], self._filenames(results))


class QueueImagesScriptTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.provider = CoverArtProviderLocal.__new__(CoverArtProviderLocal)
        self.provider._default_types = ['front']
        self.provider.album = MagicMock()
        self.provider.queue_put = MagicMock()

    @patch('picard.coverart.providers.local.script_to_filename')
    def test_empty_script_result_skipped(self, mock_stf):
        mock_stf.return_value = ''
        file = MagicMock()
        file.filename = '/music/song.mp3'
        file.metadata = {}
        self.provider.album.iterfiles.return_value = [file]
        self.provider._queue_images_script('%album%')
        self.provider.queue_put.assert_not_called()

    @patch('picard.coverart.providers.local.script_to_filename')
    def test_calls_find_local_images_by_script(self, mock_stf):
        mock_stf.return_value = 'cover.*'
        file = MagicMock()
        file.filename = '/music/song.mp3'
        file.metadata = {'album': 'Test'}
        self.provider.album.iterfiles.return_value = [file]
        self.provider.find_local_images_by_script = MagicMock(return_value=[])
        self.provider._queue_images_script('%album%')
        self.provider.find_local_images_by_script.assert_called_once()


_SCRIPT_SETTINGS = {
    'ascii_filenames': False,
    'enabled_plugins': [],
    'windows_compatibility': False,
    'win_compat_replacements': {},
    'replace_spaces_with_underscores': False,
    'replace_dir_separator': '_',
}


class ScriptToGlobMatchTest(LocalCoverArtTestBase):
    """Integration test: script evaluation → glob matching against real files."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(_SCRIPT_SETTINGS)

    def _find_with_script(self, script, metadata):
        pattern = script_to_filename(script, metadata)
        filepaths_done = set()
        return list(self.provider.find_local_images_by_script(self.tmpdir, pattern, filepaths_done))

    def test_album_variable_match(self):
        self._create_files(['Abbey Road.jpg', 'other.jpg'])
        metadata = Metadata({'album': 'Abbey Road'})
        results = self._find_with_script('%album%.*', metadata)
        self.assertEqual(['Abbey Road.jpg'], self._filenames(results))

    def test_album_variable_no_match(self):
        self._create_files(['Let It Be.jpg'])
        metadata = Metadata({'album': 'Abbey Road'})
        results = self._find_with_script('%album%.*', metadata)
        self.assertEqual([], self._filenames(results))

    def test_artist_album_pattern(self):
        self._create_files(['The Beatles - Abbey Road.png', 'cover.jpg'])
        metadata = Metadata({'albumartist': 'The Beatles', 'album': 'Abbey Road'})
        results = self._find_with_script('%albumartist% - %album%.*', metadata)
        self.assertEqual(['The Beatles - Abbey Road.png'], self._filenames(results))

    def test_plain_text_glob(self):
        self._create_files(['cover.jpg', 'cover.png', 'back.jpg'])
        metadata = Metadata()
        results = self._find_with_script('cover.*', metadata)
        self.assertEqual(['cover.jpg', 'cover.png'], self._filenames(results))

    def test_script_with_conditional_matches_image_extensions(self):
        """Script uses $if to build a glob that matches .jpg/.png but not .txt.
        Tests both the true branch (album matches) and fallback branch (album doesn't match).
        """
        self._create_files(
            [
                'Abbey Road.jpg',
                'Abbey Road.png',
                'Abbey Road.txt',
                'cover.jpg',
                'cover.png',
            ]
        )
        script = '$if($eq(%album%,Abbey Road),%album%.[jp][pn][g]*,cover.[jp][pn][g]*)'

        # True branch: album is "Abbey Road", matches Abbey Road.jpg and .png but not .txt
        metadata = Metadata({'album': 'Abbey Road'})
        results = self._find_with_script(script, metadata)
        self.assertEqual(['Abbey Road.jpg', 'Abbey Road.png'], self._filenames(results))

        # Fallback branch: album doesn't match, falls back to cover.*
        metadata = Metadata({'album': 'Let It Be'})
        results = self._find_with_script(script, metadata)
        self.assertEqual(['cover.jpg', 'cover.png'], self._filenames(results))

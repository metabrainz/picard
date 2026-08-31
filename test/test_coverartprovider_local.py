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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

import os
import re

from test.picardtestcase import PicardTestCase

from picard.coverart.providers.local import CoverArtProviderLocal


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
            path = os.path.join(self.tmpdir, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').close()

    def _filenames(self, results):
        return sorted(os.path.basename(r.url.toLocalFile()) for r in results)


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

    def test_match_in_subdirectory(self):
        self._create_files([os.path.join('sub', 'cover.jpg')])
        results = self._find(r'cover')
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertTrue(os.path.exists(results[0].url.toLocalFile()))

    def test_match_with_relative_start_dir(self):
        # Regression: os.walk(current_dir) yields a root that already includes
        # current_dir. The returned filepath must be os.path.join(root,
        # filename); joining current_dir + root + filename double-prepends the
        # base directory when current_dir is relative, producing a path that
        # never exists (so the image is silently dropped).
        self._create_files([os.path.join('sub', 'cover.jpg')])
        match_re = re.compile(r'cover', re.IGNORECASE)
        cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            results = list(self.provider.find_local_images('sub', match_re))
        finally:
            os.chdir(cwd)
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, results[0].url.toLocalFile())))


class DefaultTypesTest(PicardTestCase):
    def test_default_types_is_single_front(self):
        # Regression: _default_types must be the single-element tuple
        # ('front',), not tuple('front') which explodes into
        # ('f', 'r', 'o', 'n', 't').
        self.assertEqual(('front',), CoverArtProviderLocal._default_types)

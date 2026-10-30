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

from test.picardtestcase import PicardTestCase

from picard.util import scan_paths_recursive


class ScanPathsRecursiveTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.root = self.mktmpdir()
        self._touch('a.mp3')
        self._touch('b.flac')
        os.mkdir(os.path.join(self.root, 'sub'))
        self._touch('sub/c.ogg')

    def _touch(self, rel):
        path = os.path.join(self.root, rel)
        open(path, 'w').close()
        return path

    def _names(self, paths):
        return sorted(os.path.relpath(p, self.root) for p in paths)

    def test_file_path_yielded_as_is(self):
        f = os.path.join(self.root, 'a.mp3')
        self.assertEqual([f], list(scan_paths_recursive([f], recursive=True, ignore_hidden=True)))

    def test_directory_non_recursive(self):
        result = scan_paths_recursive([self.root], recursive=False, ignore_hidden=True)
        # Non-recursive: top-level entries are yielded as-is, including the
        # subdirectory path itself (the caller's file-open simply skips it).
        self.assertEqual(['a.mp3', 'b.flac', 'sub'], self._names(result))

    def test_directory_recursive(self):
        result = scan_paths_recursive([self.root], recursive=True, ignore_hidden=True)
        self.assertEqual(['a.mp3', 'b.flac', os.path.join('sub', 'c.ogg')], self._names(result))

    def test_ignore_hidden(self):
        self._touch('.hidden.mp3')
        visible = self._names(scan_paths_recursive([self.root], recursive=True, ignore_hidden=True))
        self.assertNotIn('.hidden.mp3', visible)
        all_files = self._names(scan_paths_recursive([self.root], recursive=True, ignore_hidden=False))
        self.assertIn('.hidden.mp3', all_files)

    def test_missing_path_is_skipped(self):
        missing = os.path.join(self.root, 'does-not-exist')
        # Non-dir, non-existent path is yielded as-is (caller decides); a
        # genuinely unreadable directory would be logged and skipped.
        self.assertEqual([missing], list(scan_paths_recursive([missing], recursive=True, ignore_hidden=True)))

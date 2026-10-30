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

from picard.const.sys import IS_WIN
from picard.util import (
    normpath,
    scan_paths_recursive,
)


class ScanPathsRecursiveTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # scan_paths_recursive runs every path through normpath() (which
        # resolves realpath), so normalize the root the same way. Otherwise on
        # Windows the temp dir's realpath (AppData\Local\Temp may be a junction)
        # differs from mktmpdir()'s raw path and os.path.relpath() below yields
        # "..\..\.." noise instead of the plain names. See PR #3544 CI failure.
        self.root = normpath(self.mktmpdir())
        self._touch('a.mp3')
        self._touch('b.flac')
        os.mkdir(os.path.join(self.root, 'sub'))
        self._touch('sub/c.ogg')

    def _touch(self, rel):
        path = os.path.join(self.root, rel)
        open(path, 'w').close()
        return path

    def _touch_hidden(self, rel):
        # is_hidden() uses the leading-dot convention only on non-Windows; on
        # Windows it checks the FILE_ATTRIBUTE_HIDDEN flag, which a plain
        # open() does not set. Set it explicitly so the file is genuinely
        # hidden on every platform.
        path = self._touch(rel)
        if IS_WIN:
            import ctypes

            FILE_ATTRIBUTE_HIDDEN = 0x02
            if not ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN):
                raise ctypes.WinError()
        return path

    def _names(self, paths):
        return sorted(os.path.relpath(p, self.root) for p in paths)

    def test_file_path_yielded_as_is(self):
        f = normpath(os.path.join(self.root, 'a.mp3'))
        self.assertEqual([f], list(scan_paths_recursive([f], recursive=True, ignore_hidden=True)))

    def test_directory_non_recursive(self):
        result = scan_paths_recursive([self.root], recursive=False, ignore_hidden=True)
        # Non-recursive: yield the directory's files but NOT its subdirectory
        # paths. The function yields file paths only (see docstring); a
        # subdirectory must never be yielded, recursive or not.
        self.assertEqual(['a.mp3', 'b.flac'], self._names(result))

    def test_subdirectory_never_yielded(self):
        # Regression: with recursive=False a nested directory entry used to be
        # yielded (it fell through to the else branch). Ensure no yielded path
        # is a directory, in either mode.
        for recursive in (False, True):
            for path in scan_paths_recursive([self.root], recursive=recursive, ignore_hidden=True):
                self.assertFalse(os.path.isdir(path), f"directory yielded (recursive={recursive}): {path!r}")

    def test_directory_recursive(self):
        result = scan_paths_recursive([self.root], recursive=True, ignore_hidden=True)
        self.assertEqual(['a.mp3', 'b.flac', os.path.join('sub', 'c.ogg')], self._names(result))

    def test_ignore_hidden(self):
        self._touch_hidden('.hidden.mp3')
        visible = self._names(scan_paths_recursive([self.root], recursive=True, ignore_hidden=True))
        self.assertNotIn('.hidden.mp3', visible)
        all_files = self._names(scan_paths_recursive([self.root], recursive=True, ignore_hidden=False))
        self.assertIn('.hidden.mp3', all_files)

    def test_hidden_path_passed_directly_respects_ignore_hidden(self):
        # A hidden file given directly as a path (not discovered by scanning)
        # must also honour ignore_hidden: skipped when True, yielded when False.
        hidden = normpath(self._touch_hidden('.hidden.mp3'))
        self.assertEqual([], list(scan_paths_recursive([hidden], recursive=True, ignore_hidden=True)))
        self.assertEqual([hidden], list(scan_paths_recursive([hidden], recursive=True, ignore_hidden=False)))

    def test_missing_path_is_skipped(self):
        missing = normpath(os.path.join(self.root, 'does-not-exist'))
        # Non-dir, non-existent path is yielded as-is (caller decides); a
        # genuinely unreadable directory would be logged and skipped.
        self.assertEqual([missing], list(scan_paths_recursive([missing], recursive=True, ignore_hidden=True)))

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Ionuț Ciocîrlan
# Copyright (C) 2016 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2019 Laurent Monin
# Copyright (C) 2019-2021 Philipp Wolfer
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
import os.path
import sys
from tempfile import (
    NamedTemporaryFile,
    TemporaryDirectory,
)
import unittest

from test.picardtestcase import PicardTestCase

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.util.filenaming import (
    WinPathTooLong,
    get_available_filename,
    make_save_path,
    make_short_filename,
    move_ensure_casing,
    samefile_different_casing,
)


class ShortFilenameTest(PicardTestCase):

    def __init__(self, *args, **kwargs):
        self.maxDiff = None
        self.root = os.path.join(IS_WIN and "X:\\" or "/", "x" * 10)
        if IS_WIN:
            self.max_len = 255
        else:
            self.max_len = os.statvfs("/").f_namemax
        super().__init__(*args, **kwargs)

    @unittest.skipUnless(IS_WIN or IS_MACOS, "windows / macOS test")
    def test_bmp_unicode_on_unicode_fs(self):
        char = "\N{LATIN SMALL LETTER SHARP S}"
        fn = make_short_filename(self.root, os.path.join(*[char * 120] * 2))
        self.assertEqual(fn, os.path.join(*[char * 120] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_bmp_unicode_on_nix(self):
        char = "\N{LATIN SMALL LETTER SHARP S}"
        max_len = self.max_len
        divisor = len(char.encode(sys.getfilesystemencoding()))
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // divisor)] * 2))

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_precomposed_unicode_on_osx(self):
        char = "\N{LATIN SMALL LETTER A WITH BREVE}"
        max_len = self.max_len
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // 2)] * 2))

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_nonbmp_unicode_on_windows(self):
        char = "\N{MUSICAL SYMBOL G CLEF}"
        remaining = 259 - (3 + 10 + 1 + 200 + 1)
        fn = make_short_filename(self.root, os.path.join(*[char * 100] * 2))
        self.assertEqual(fn, os.path.join(char * 100, char * (remaining // 2)))

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_nonbmp_unicode_on_osx(self):
        char = "\N{MUSICAL SYMBOL G CLEF}"
        max_len = self.max_len
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // 2)] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_nonbmp_unicode_on_nix(self):
        char = "\N{MUSICAL SYMBOL G CLEF}"
        max_len = self.max_len
        divisor = len(char.encode(sys.getfilesystemencoding()))
        fn = make_short_filename(self.root, os.path.join(*[char * 100] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // divisor)] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_nonbmp_unicode_on_nix_with_windows_compat(self):
        char = "\N{MUSICAL SYMBOL G CLEF}"
        max_len = self.max_len
        remaining = 259 - (3 + 10 + 1 + 200 + 1)
        divisor = len(char.encode(sys.getfilesystemencoding()))
        fn = make_short_filename(self.root, os.path.join(*[char * 100] * 2), win_compat=True)
        self.assertEqual(fn, os.path.join(char * (max_len // divisor), char * (remaining // 2)))

    def test_windows_shortening(self):
        fn = make_short_filename(self.root, os.path.join("a" * 200, "b" * 200, "c" * 200 + ".ext"), win_compat=True)
        self.assertEqual(fn, os.path.join("a" * 116, "b" * 116, "c" * 7 + ".ext"))

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_windows_shortening_with_ancestor_on_nix(self):
        root = os.path.join(self.root, "w" * 10, "x" * 10, "y" * 9, "z" * 9)
        fn = make_short_filename(
            root, os.path.join("b" * 200, "c" * 200, "d" * 200 + ".ext"),
            win_compat=True, relative_to=self.root)
        self.assertEqual(fn, os.path.join("b" * 100, "c" * 100, "d" * 7 + ".ext"))

    def test_windows_node_maxlength_shortening(self):
        max_len = 226
        remaining = 259 - (3 + 10 + 1 + max_len + 1)
        fn = make_short_filename(self.root, os.path.join("a" * 300, "b" * 100 + ".ext"), win_compat=True)
        self.assertEqual(fn, os.path.join("a" * max_len, "b" * (remaining - 4) + ".ext"))

    def test_windows_selective_shortening(self):
        root = self.root + "x" * (44 - 10 - 3)
        fn = make_short_filename(root, os.path.join(
            os.path.join(*["a" * 9] * 10 + ["b" * 15] * 10), "c" * 10), win_compat=True)
        self.assertEqual(fn, os.path.join(os.path.join(*["a" * 9] * 10 + ["b" * 9] * 10), "c" * 10))

    def test_windows_shortening_not_needed(self):
        root = self.root + "x" * 33
        fn = make_short_filename(root, os.path.join(
            os.path.join(*["a" * 9] * 20), "b" * 10), win_compat=True)
        self.assertEqual(fn, os.path.join(os.path.join(*["a" * 9] * 20), "b" * 10))

    def test_windows_path_too_long(self):
        root = self.root + "x" * 230
        self.assertRaises(WinPathTooLong, make_short_filename,
                          root, os.path.join("a", "b", "c", "d"), win_compat=True)

    def test_windows_path_not_too_long(self):
        root = self.root + "x" * 230
        fn = make_short_filename(root, os.path.join("a", "b", "c"), win_compat=True)
        self.assertEqual(fn, os.path.join("a", "b", "c"))

    def test_whitespace(self):
        fn = make_short_filename(self.root, os.path.join("a1234567890   ", "  b1234567890  "))
        self.assertEqual(fn, os.path.join("a1234567890", "b1234567890"))


class SamefileDifferentCasingTest(PicardTestCase):

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_samefile_different_casing(self):
        with NamedTemporaryFile(prefix='Foo') as f:
            real_name = f.name
            lower_name = real_name.lower()
            self.assertFalse(samefile_different_casing(real_name, real_name))
            self.assertFalse(samefile_different_casing(lower_name, lower_name))
            self.assertTrue(samefile_different_casing(real_name, lower_name))

    def test_samefile_different_casing_non_existant_file(self):
        self.assertFalse(samefile_different_casing("/foo/bar", "/foo/BAR"))

    def test_samefile_different_casing_identical_path(self):
        self.assertFalse(samefile_different_casing("/foo/BAR", "/foo/BAR"))


class MoveEnsureCasingTest(PicardTestCase):

    def test_move_ensure_casing(self):
        with TemporaryDirectory() as d:
            file_path = os.path.join(d, 'foo')
            target_path = os.path.join(d, 'FOO')
            open(file_path, 'a').close()
            move_ensure_casing(file_path, target_path)
            files = os.listdir(d)
            self.assertIn('FOO', files)


class MakeSavePathTest(PicardTestCase):

    def test_replace_trailing_dots(self):
        path = 'foo./bar.'
        self.assertEqual(path, make_save_path(path))
        self.assertEqual('foo_/bar_', make_save_path(path, win_compat=True))

    def test_replace_leading_dots(self):
        path = '.foo/.bar'
        self.assertEqual('_foo/_bar', make_save_path(path))

    def test_decompose_precomposed_chars(self):
        path = 'foo/\u00E9bar'  # é
        self.assertEqual('foo/\u0065\u0301bar', make_save_path(path, mac_compat=True))


class GetAvailableFilenameTest(PicardTestCase):

    def _add_number(self, filename, number):
        name, ext = os.path.splitext(filename)
        return '%s (%i)%s' % (name, number, ext)

    def test_append_number(self):
        with NamedTemporaryFile(prefix='foo', suffix='.mp3') as f:
            new_filename = get_available_filename(f.name)
            self.assertEqual(self._add_number(f.name, 1), new_filename)

    def test_do_not_append_number_on_same_file(self):
        with NamedTemporaryFile(prefix='foo', suffix='.mp3') as f:
            new_filename = get_available_filename(f.name, f.name)
            self.assertEqual(f.name, new_filename)

    def test_handle_non_existant_old_path(self):
        with NamedTemporaryFile(prefix='foo', suffix='.mp3') as f:
            new_filename = get_available_filename(f.name, '/foo/old.mp3')
            self.assertEqual(self._add_number(f.name, 1), new_filename)

    def test_append_additional_numbers(self):
        with TemporaryDirectory() as d:
            expected_number = 3
            oldname = os.path.join(d, 'bar.mp3')
            open(oldname, 'a').close()
            filename = os.path.join(d, 'foo.mp3')
            open(filename, 'a').close()
            for i in range(1, expected_number):
                open(self._add_number(filename, i), 'a').close()
            new_filename = get_available_filename(filename, oldname)
            self.assertEqual(self._add_number(filename, expected_number), new_filename)

    def test_reuse_existing_number(self):
        with TemporaryDirectory() as d:
            expected_number = 2
            filename = os.path.join(d, 'foo.mp3')
            open(filename, 'a').close()
            for i in range(1, 3):
                open(self._add_number(filename, i), 'a').close()
            oldname = self._add_number(filename, expected_number)
            new_filename = get_available_filename(filename, oldname)
            self.assertEqual(self._add_number(filename, expected_number), new_filename)

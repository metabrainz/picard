# -*- coding: utf-8 -*-

import os
import os.path
import sys
from test.picardtestcase import PicardTestCase
import unittest

from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.util.filenaming import make_short_filename

class ShortFilenameTest(PicardTestCase):

    def __init__(self, *args, **kwargs):
        self.maxDiff = None
        self.root = os.path.join(IS_WIN and "X:\\" or "/", "x" * 10)
        if IS_WIN:
            self.max_len = 255
        else:
            self.max_len = os.statvfs("/").f_namemax
        super().__init__(*args, **kwargs)

    @unittest.skipUnless(IS_WIN or IS_MACOS, "windows / os x test")
    def test_bmp_unicode_on_unicode_fs(self):
        char = u"\N{LATIN SMALL LETTER SHARP S}"
        fn = make_short_filename(self.root, os.path.join(*[char * 120] * 2))
        self.assertEqual(fn, os.path.join(*[char * 120] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_bmp_unicode_on_nix(self):
        char = u"\N{LATIN SMALL LETTER SHARP S}"
        max_len = self.max_len
        divisor = len(char.encode(sys.getfilesystemencoding()))
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // divisor)] * 2))

    @unittest.skipUnless(IS_MACOS, "os x test")
    def test_precomposed_unicode_on_osx(self):
        char = u"\N{LATIN SMALL LETTER A WITH BREVE}"
        max_len = self.max_len
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // 2)] * 2))

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_nonbmp_unicode_on_windows(self):
        char = u"\N{MUSICAL SYMBOL G CLEF}"
        remaining = 259 - (3 + 10 + 1 + 200 + 1)
        fn = make_short_filename(self.root, os.path.join(*[char * 100] * 2))
        self.assertEqual(fn, os.path.join(char * 100, char * (remaining // 2)))

    @unittest.skipUnless(IS_MACOS, "os x test")
    def test_nonbmp_unicode_on_osx(self):
        char = u"\N{MUSICAL SYMBOL G CLEF}"
        max_len = self.max_len
        fn = make_short_filename(self.root, os.path.join(*[char * 200] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // 2)] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_nonbmp_unicode_on_nix(self):
        char = u"\N{MUSICAL SYMBOL G CLEF}"
        max_len = self.max_len
        divisor = len(char.encode(sys.getfilesystemencoding()))
        fn = make_short_filename(self.root, os.path.join(*[char * 100] * 2))
        self.assertEqual(fn, os.path.join(*[char * (max_len // divisor)] * 2))

    @unittest.skipUnless(not IS_WIN and not IS_MACOS, "non-windows, non-osx test")
    def test_nonbmp_unicode_on_nix_with_windows_compat(self):
        char = u"\N{MUSICAL SYMBOL G CLEF}"
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
        self.assertRaises(IOError, make_short_filename,
                          root, os.path.join("a", "b", "c", "d"), win_compat=True)

    def test_windows_path_not_too_long(self):
        root = self.root + "x" * 230
        fn = make_short_filename(root, os.path.join("a", "b", "c"), win_compat=True)
        self.assertEqual(fn, os.path.join("a", "b", "c"))

    def test_whitespace(self):
        fn = make_short_filename(self.root, os.path.join("a1234567890   ", "  b1234567890  "))
        self.assertEqual(fn, os.path.join("a1234567890", "b1234567890"))

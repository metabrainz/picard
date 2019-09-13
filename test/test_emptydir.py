# -*- coding: utf-8 -*-

import os.path
from tempfile import (
    mkdtemp,
    mkstemp,
)
import unittest

from picard.util import emptydir


class EmptyDirTest(unittest.TestCase):

    def test_is_empty_dir_really_empty(self):
        dir = _create_temp_dir()
        self.assertTrue(emptydir.is_empty_dir(dir))

    def test_is_empty_dir_only_junk_files(self):
        dir = _create_temp_dir(extra_files=emptydir.JUNK_FILES)
        self.assertTrue(len(os.listdir(dir)) > 0)
        self.assertTrue(emptydir.is_empty_dir(dir))

    def test_is_empty_dir_not_empty(self):
        dir = _create_temp_dir(extra_files=['.notempty'])
        self.assertEqual(1, len(os.listdir(dir)))
        self.assertFalse(emptydir.is_empty_dir(dir))

    def test_is_empty_dir_custom_ignore_files(self):
        ignored_files = ['.empty']
        dir = _create_temp_dir(extra_files=ignored_files)
        self.assertEqual(1, len(os.listdir(dir)))
        self.assertTrue(emptydir.is_empty_dir(dir, ignored_files=ignored_files))

    def test_is_empty_dir_not_empty_child_dir(self):
        dir = _create_temp_dir(extra_dirs=['childdir'])
        self.assertEqual(1, len(os.listdir(dir)))
        self.assertFalse(emptydir.is_empty_dir(dir))

    def test_is_empty_dir_on_file(self):
        fd, file_ = mkstemp()
        self.assertRaises(NotADirectoryError, emptydir.is_empty_dir, file_)


class RmEmptyDirTest(unittest.TestCase):

    def test_rm_empty_dir_really_empty(self):
        dir = _create_temp_dir()
        self.assertTrue(os.path.isdir(dir))
        emptydir.rm_empty_dir(dir)
        self.assertFalse(os.path.exists(dir))

    def test_rm_empty_dir_only_junk_files(self):
        dir = _create_temp_dir(extra_files=emptydir.JUNK_FILES)
        self.assertTrue(os.path.isdir(dir))
        emptydir.rm_empty_dir(dir)
        self.assertFalse(os.path.exists(dir))

    def test_rm_empty_dir_not_empty(self):
        dir = _create_temp_dir(['.notempty'])
        self.assertEqual(1, len(os.listdir(dir)))
        self.assertRaises(emptydir.SkipRemoveDir, emptydir.rm_empty_dir, dir)

    def test_rm_empty_dir_is_special(self):
        dir = _create_temp_dir()
        orig_portected_dirs = emptydir.PROTECTED_DIRECTORIES
        emptydir.PROTECTED_DIRECTORIES.add(os.path.realpath(dir))
        self.assertRaises(emptydir.SkipRemoveDir, emptydir.rm_empty_dir, dir)
        emptydir.PROTECTED_DIRECTORIES = orig_portected_dirs

    def test_is_empty_dir_on_file(self):
        fd, file_ = mkstemp()
        self.assertRaises(NotADirectoryError, emptydir.rm_empty_dir, file_)


def _create_temp_dir(extra_files=(), extra_dirs=()):
    dir = mkdtemp()
    for f in extra_files:
        open(os.path.join(dir, f), 'a').close()
    for f in extra_dirs:
        os.mkdir(os.path.join(dir, f))
    return dir

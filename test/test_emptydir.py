# -*- coding: utf-8 -*-

import os.path
from tempfile import NamedTemporaryFile

from test.picardtestcase import PicardTestCase

from picard.util import emptydir


class EmptyDirTestCommon(PicardTestCase):

    def create_temp_dir(self, extra_files=(), extra_dirs=(), ignore_errors=False):
        tempdir = self.mktmpdir(ignore_errors=ignore_errors)
        for f in extra_files:
            open(os.path.join(tempdir, f), 'a').close()
        for f in extra_dirs:
            os.mkdir(os.path.join(tempdir, f))
        return tempdir


class EmptyDirTest(EmptyDirTestCommon):

    def test_is_empty_dir_really_empty(self):
        tempdir = self.create_temp_dir()
        self.assertTrue(emptydir.is_empty_dir(tempdir))

    def test_is_empty_dir_only_junk_files(self):
        tempdir = self.create_temp_dir(extra_files=emptydir.JUNK_FILES)
        self.assertTrue(len(os.listdir(tempdir)) > 0)
        self.assertTrue(emptydir.is_empty_dir(tempdir))

    def test_is_empty_dir_not_empty(self):
        tempdir = self.create_temp_dir(extra_files=['.notempty'])
        self.assertEqual(1, len(os.listdir(tempdir)))
        self.assertFalse(emptydir.is_empty_dir(tempdir))

    def test_is_empty_dir_custom_ignore_files(self):
        ignored_files = ['.empty']
        tempdir = self.create_temp_dir(extra_files=ignored_files)
        self.assertEqual(1, len(os.listdir(tempdir)))
        self.assertTrue(emptydir.is_empty_dir(tempdir, ignored_files=ignored_files))

    def test_is_empty_dir_not_empty_child_dir(self):
        tempdir = self.create_temp_dir(extra_dirs=['childdir'])
        self.assertEqual(1, len(os.listdir(tempdir)))
        self.assertFalse(emptydir.is_empty_dir(tempdir))

    def test_is_empty_dir_on_file(self):
        with NamedTemporaryFile() as f:
            self.assertRaises(NotADirectoryError, emptydir.is_empty_dir, f.name)


class RmEmptyDirTest(EmptyDirTestCommon):

    def test_rm_empty_dir_really_empty(self):
        tempdir = self.create_temp_dir(ignore_errors=True)
        self.assertTrue(os.path.isdir(tempdir))
        emptydir.rm_empty_dir(tempdir)
        self.assertFalse(os.path.exists(tempdir))

    def test_rm_empty_dir_only_junk_files(self):
        tempdir = self.create_temp_dir(extra_files=emptydir.JUNK_FILES, ignore_errors=True)
        self.assertTrue(os.path.isdir(tempdir))
        emptydir.rm_empty_dir(tempdir)
        self.assertFalse(os.path.exists(tempdir))

    def test_rm_empty_dir_not_empty(self):
        tempdir = self.create_temp_dir(['.notempty'])
        self.assertEqual(1, len(os.listdir(tempdir)))
        self.assertRaises(emptydir.SkipRemoveDir, emptydir.rm_empty_dir, tempdir)

    def test_rm_empty_dir_is_special(self):
        tempdir = self.create_temp_dir()
        orig_portected_dirs = emptydir.PROTECTED_DIRECTORIES
        emptydir.PROTECTED_DIRECTORIES.add(os.path.realpath(tempdir))
        self.assertRaises(emptydir.SkipRemoveDir, emptydir.rm_empty_dir, tempdir)
        emptydir.PROTECTED_DIRECTORIES = orig_portected_dirs

    def test_is_empty_dir_on_file(self):
        with NamedTemporaryFile() as f:
            self.assertRaises(NotADirectoryError, emptydir.rm_empty_dir, f.name)

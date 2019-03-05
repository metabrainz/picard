# -*- coding: utf-8 -*-
from contextlib import suppress
import os.path
import shutil
from tempfile import mkdtemp
from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_WIN
from picard.util.scantree import scantree


if IS_WIN:
    from ctypes import windll
    import stat

    # https://docs.python.org/3/library/stat.html#stat.FILE_ATTRIBUTE_ARCHIVE
    #
    # https://docs.microsoft.com/en-us/windows/desktop/FileIO/file-attribute-constants
    # (0x2) The file or directory is hidden. It is not included in an ordinary directory listing.
    # FILE_ATTRIBUTE_HIDDEN=2
    #
    # (0x80) A file that does not have other attributes set. This attribute is valid only when used alone.
    # FILE_ATTRIBUTE_NORMAL=128
    #
    # (0x4) A file or directory that the operating system uses a part of, or uses exclusively.
    # FILE_ATTRIBUTE_SYSTEM=4

    win_hidden_files = set()

    _set_attr = windll.kernel32.SetFileAttributesW
    _get_attr = windll.kernel32.GetFileAttributesW

    def win_set_hidden(path):
        attrs = _get_attr(path)
        if attrs != -1 and _set_attr(path, attrs | stat.FILE_ATTRIBUTE_HIDDEN):
            win_hidden_files.add(path)
            return True
        return False

    def win_set_normal(path):
        if _set_attr(path, stat.FILE_ATTRIBUTE_NORMAL):
            win_hidden_files.discard(path)
            return True
        return False


class TestFileSystem(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.src_directory = mkdtemp()

    def tearDown(self):
        if IS_WIN:
            # reset hidden files to normal, else they may not be removed
            for path in list(win_hidden_files):
                win_set_normal(path)
        shutil.rmtree(self.src_directory)

    def _prepare_files(self, src_rel_path=''):
        """Prepare src files filenames for a test."""
        topdir = os.path.join(self.src_directory, src_rel_path)
        with suppress(FileExistsError):
            os.mkdir(topdir)

        # create a subdir
        subdir = os.path.join(topdir, 'subdir')
        with suppress(FileExistsError):
            os.mkdir(subdir)

        # Prepare the source directory structure under self.src_directory
        # .../<src_rel_path>/test.mp3
        # .../<src_rel_path>/cover.jpg

        def src_file(name, sample_name=None, subdir=''):
            """Copy file from samples and returns path to temporary file to be
            used as source.
            If sample_name isn't provided, it will use name for it
            """
            if sample_name is None:
                sample_name = name
            sample = os.path.join('test', 'data', sample_name)
            copy_to = os.path.join(
                self.src_directory, src_rel_path, subdir, name)
            shutil.copy(sample, copy_to)
            return copy_to

        files = dict()
        files['mp3'] = src_file('test.mp3')
        files['img'] = src_file('cover.jpg', 'mb.jpg')
        files['hidden_img'] = src_file('.hidden.jpg', 'mb.jpg')
        if IS_WIN:
            win_set_hidden(files['hidden_img'])

        files['sub_mp3'] = src_file('test.mp3', subdir='subdir')
        files['sub_img'] = src_file('cover.jpg', 'mb.jpg', subdir='subdir')
        files['sub_hidden_img'] = src_file('.hidden.jpg', 'mb.jpg', subdir='subdir')
        if IS_WIN:
            win_set_hidden(files['sub_hidden_img'])

        files['topdir'] = topdir
        files['subdir'] = subdir

        # TODO: test symlink to file
        # TODO: test symlink to subdir
        # TODO: test subdir starting with a dot
        # TODO: test subdir with win hidden attribute

        return files

    def test_scantree(self):
        files = self._prepare_files(src_rel_path='música')
        l = list(scantree(files['topdir']))

        self.assertTrue(files['mp3'] in l)
        self.assertTrue(files['img'] in l)

        self.assertFalse(files['hidden_img'] in l)
        self.assertFalse(files['subdir'] in l)

        self.assertEqual(len(l), 2)

    def test_scantree_hidden(self):
        files = self._prepare_files(src_rel_path='música')
        l = list(scantree(files['topdir'], ignore_hidden=False))

        self.assertTrue(files['mp3'] in l)
        self.assertTrue(files['img'] in l)
        self.assertTrue(files['hidden_img'] in l)

        self.assertFalse(files['subdir'] in l)

        self.assertEqual(len(l), 3)

    def test_scantree_recursive(self):
        files = self._prepare_files(src_rel_path='música')
        l = list(scantree(files['topdir'], recursive=True))

        self.assertTrue(files['mp3'] in l)
        self.assertTrue(files['img'] in l)
        self.assertTrue(files['sub_mp3'] in l)
        self.assertTrue(files['sub_img'] in l)

        self.assertFalse(files['hidden_img'] in l)
        self.assertFalse(files['sub_hidden_img'] in l)

        self.assertFalse(files['subdir'] in l)

        self.assertEqual(len(l), 4)

    def test_scantree_recursive_hidden(self):
        files = self._prepare_files(src_rel_path='música')
        l = list(scantree(files['topdir'], recursive=True, ignore_hidden=False))

        self.assertTrue(files['mp3'] in l)
        self.assertTrue(files['img'] in l)
        self.assertTrue(files['hidden_img'] in l)
        self.assertTrue(files['sub_mp3'] in l)
        self.assertTrue(files['sub_img'] in l)
        self.assertTrue(files['sub_hidden_img'] in l)

        self.assertFalse(files['subdir'] in l)

        self.assertEqual(len(l), 6)

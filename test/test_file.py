import os
import shutil
from tempfile import mkdtemp
import unittest

from test.picardtestcase import PicardTestCase

from picard import config
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.file import File
from picard.metadata import Metadata


def is_macos_10_14():
    if IS_MACOS:
        import platform
        return platform.mac_ver()[0].startswith('10.14')
    return False


class DataObjectTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.file = File('somepath/somefile.mp3')

    def test_filename(self):
        self.assertEqual('somepath/somefile.mp3', self.file.filename)
        self.assertEqual('somefile.mp3', self.file.base_filename)

    def test_tracknumber(self):
        self.assertEqual(0, self.file.tracknumber)
        self.file.metadata['tracknumber'] = '42'
        self.assertEqual(42, self.file.tracknumber)
        self.file.metadata['tracknumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.tracknumber)

    def test_discnumber(self):
        self.assertEqual(0, self.file.discnumber)
        self.file.metadata['discnumber'] = '42'
        self.assertEqual(42, self.file.discnumber)
        self.file.metadata['discnumber'] = 'FOURTYTWO'
        self.assertEqual(0, self.file.discnumber)


class TestPreserveTimes(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.tmp_directory = mkdtemp()
        filepath = os.path.join(self.tmp_directory, 'a.mp3')
        self.file = File(filepath)

    def tearDown(self):
        shutil.rmtree(self.tmp_directory)

    def _create_testfile(self):
        # create a dummy file
        with open(self.file.filename, 'w') as f:
            f.write('xxx')
            f.flush()
            os.fsync(f.fileno())

    def _modify_testfile(self):
        # dummy file modification, append data to it
        with open(self.file.filename, 'a') as f:
            f.write('yyy')
            f.flush()
            os.fsync(f.fileno())

    def _read_testfile(self):
        with open(self.file.filename, 'r') as f:
            return f.read()

    def test_preserve_times(self):
        self._create_testfile()

        # test if times are preserved
        (before_atime_ns, before_mtime_ns) = self.file._preserve_times(self.file.filename, self._modify_testfile)

        # HERE an external access to the file is possible, modifying its access time

        # read times again and compare with original
        st = os.stat(self.file.filename)
        (after_atime_ns, after_mtime_ns) = (st.st_atime_ns, st.st_mtime_ns)

        # on macOS 10.14 os.utime only sets the times with second precision
        # see https://tickets.metabrainz.org/browse/PICARD-1516
        if is_macos_10_14():
            before_atime_ns //= 1000
            before_mtime_ns //= 1000
            after_atime_ns //= 1000
            after_mtime_ns //= 1000

        # modification times should be equal
        self.assertEqual(before_mtime_ns, after_mtime_ns)

        # access times may not be equal
        # time difference should be positive and reasonably low (if no access in between, it should be 0)
        delta = after_atime_ns - before_atime_ns
        tolerance = 10**7  #  0.01 seconds
        self.assertTrue(0 <= delta < tolerance, "0 <= %s < %s" % (delta, tolerance))

        # ensure written data can be read back
        # keep it at the end, we don't want to access file before time checks
        self.assertEqual(self._read_testfile(), 'xxxyyy')

    def test_preserve_times_nofile(self):

        with self.assertRaises(self.file.PreserveTimesStatError):
            self.file._preserve_times(self.file.filename,
                                      self._modify_testfile)
        with self.assertRaises(FileNotFoundError):
            self._read_testfile()

    def test_preserve_times_nofile_utime(self):
        self._create_testfile()

        def save():
            os.remove(self.file.filename)

        with self.assertRaises(self.file.PreserveTimesUtimeError):
            self.file._preserve_times(self.file.filename, save)


class FileNamingTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.file = File('/somepath/somefile.mp3')
        config.setting = {
            'ascii_filenames': False,
            'clear_existing_tags': False,
            'enabled_plugins': [],
            'file_naming_format': '%album%/%title%',
            'move_files_to': '/media/music',
            'move_files': False,
            'rename_files': False,
            'windows_compatibility': True,
        }
        self.metadata = Metadata({
            'album': 'somealbum',
            'title': 'sometitle',
        })

    def test_make_filename_no_move_and_rename(self):
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath(self.file.filename), filename)

    def test_make_filename_rename_only(self):
        config.setting['rename_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(os.path.realpath('/somepath/sometitle.mp3'), filename)

    def test_make_filename_move_only(self):
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum/somefile.mp3'),
            filename)

    def test_make_filename_move_and_rename(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum/sometitle.mp3'),
            filename)

    def test_make_filename_move_relative_path(self):
        config.setting['move_files'] = True
        config.setting['move_files_to'] = 'subdir'
        filename = self.file.make_filename(self.file.filename, self.metadata)
        self.assertEqual(
            os.path.realpath('/somepath/subdir/somealbum/somefile.mp3'),
            filename)

    def test_make_filename_replace_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata({
            'album': 'somealbum.',
            'title': 'sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum_/sometitle.mp3'),
            filename)

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_make_filename_keep_trailing_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = False
        metadata = Metadata({
            'album': 'somealbum.',
            'title': 'sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/somealbum./sometitle.mp3'),
            filename)

    def test_make_filename_replace_leading_dots(self):
        config.setting['rename_files'] = True
        config.setting['move_files'] = True
        config.setting['windows_compatibility'] = True
        metadata = Metadata({
            'album': '.somealbum',
            'title': '.sometitle',
        })
        filename = self.file.make_filename(self.file.filename, metadata)
        self.assertEqual(
            os.path.realpath('/media/music/_somealbum/_sometitle.mp3'),
            filename)

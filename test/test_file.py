import os
import shutil
from tempfile import mkdtemp

from test.picardtestcase import PicardTestCase

from picard.file import File


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
        (after_atimes_ns, after_mtimes_ns) = (st.st_atime_ns, st.st_mtime_ns)

        # modification times should be equal
        self.assertEqual(before_mtime_ns, after_mtimes_ns)

        # access times may not be equal
        # time difference should be positive and reasonably low (if no access in between, it should be 0)
        delta = after_atimes_ns - before_atime_ns
        tolerance = 10**7  #  0.01 seconds
        self.assertTrue(0 <= delta < tolerance)

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
            result = self.file._preserve_times(self.file.filename, save)

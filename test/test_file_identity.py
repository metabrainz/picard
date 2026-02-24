# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 iron-prog
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import os
import tempfile
import time
import unittest

from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_WIN
from picard.file import (
    FileIdentity,
    FileIdentityError,
)


class TestFileIdentity(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.temp_files = set()

    def tearDown(self):
        for fname in self.temp_files:
            try:
                os.remove(fname)
            except OSError:
                pass
        super().tearDown()

    def _write_temp(self, contents=b"hello"):
        fd, fname = tempfile.mkstemp()
        self.temp_files.add(fname)
        with os.fdopen(fd, "wb") as f:
            f.write(contents)
        return fname

    def test_identity_equal(self):
        """Test that two FileIdentity objects for the same unchanged file are equal."""
        fname = self._write_temp(b"abcdef")
        id1 = FileIdentity(fname)
        time.sleep(0.01)
        id2 = FileIdentity(fname)
        self.assertEqual(id1, id2)

    def test_identity_same_file_unchanged(self):
        """Test that FileIdentity objects created immediately for the same file are equal."""
        fname = self._write_temp(b"test content")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        self.assertEqual(id1, id2)
        self.assertTrue(id1)
        self.assertTrue(id2)

    def test_identity_diff_mtime(self):
        """Test that FileIdentity detects mtime changes when hash not computed."""
        fname = self._write_temp(b"abcdef")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        os.utime(fname, (stat.st_atime, stat.st_mtime + 2))
        id2 = FileIdentity(fname)
        # Different mtime, no hash - should be not equal
        self.assertNotEqual(id1, id2)
        # Hashes should not have been computed
        self.assertIsNotNone(id1._hash)
        self.assertIsNotNone(id2._hash)

    def test_identity_diff_size(self):
        """Test that FileIdentity detects file size changes."""
        fname = self._write_temp(b"short")
        id1 = FileIdentity(fname)
        with open(fname, "wb") as f:
            f.write(b"much longer content")
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_replaced_file_same_size_different_content(self):
        """Test that replacing a file with different content but same size is detected."""
        fname = self._write_temp(b"AAAA")
        id1 = FileIdentity(fname)
        fd, newname = tempfile.mkstemp()
        self.temp_files.add(newname)
        with os.fdopen(fd, "wb") as f:
            f.write(b"BBBB")
        os.replace(newname, fname)
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_hash_diff(self):
        """Test that FileIdentity distinguishes between different files."""
        f1 = self._write_temp(b"A" * (FileIdentity._READ_SIZE + 10))
        f2 = self._write_temp(b"B" * (FileIdentity._READ_SIZE + 10))
        id1 = FileIdentity(f1)
        id2 = FileIdentity(f2)
        self.assertNotEqual(id1, id2)

    def test_identity_missing_file(self):
        """Test that FileIdentity handles missing files correctly."""
        fname = self._write_temp(b"xxx")
        os.remove(fname)
        id_missing = FileIdentity(fname)
        self.assertFalse(id_missing)

    def test_identity_missing_vs_existing(self):
        """Test that FileIdentity distinguishes between existing and missing files."""
        fname = self._write_temp(b"exists")
        id_exists = FileIdentity(fname)
        os.remove(fname)
        id_missing = FileIdentity(fname)
        self.assertNotEqual(id_exists, id_missing)
        self.assertTrue(id_exists)
        self.assertFalse(id_missing)

    def test_identity_not_equal_to_none(self):
        """Test that FileIdentity is not equal to None."""
        fname = self._write_temp(b"test")
        identity = FileIdentity(fname)
        self.assertNotEqual(identity, None)

    def test_fast_hash(self):
        """Test that _fast_hash generates consistent hashes."""
        fname = self._write_temp(b"test content for hashing")
        identity = FileIdentity(fname)
        hash1 = identity._fast_hash()
        self.assertIsNotNone(hash1)
        self.assertIsInstance(hash1, str)
        hash2 = identity._fast_hash()
        self.assertEqual(hash1, hash2)

    def test_fast_hash_different_content(self):
        """Test that _fast_hash generates different hashes for different files."""
        f1 = self._write_temp(b"content A")
        f2 = self._write_temp(b"content B")
        id1 = FileIdentity(f1)
        id2 = FileIdentity(f2)
        self.assertNotEqual(id1._fast_hash(), id2._fast_hash())

    def test_fast_hash_large_file(self):
        """Test that _fast_hash works with files larger than _READ_SIZE."""
        fname = self._write_temp(b"X" * (FileIdentity._READ_SIZE * 2))
        identity = FileIdentity(fname)
        hash_result = identity._fast_hash()
        self.assertIsNotNone(hash_result)

    def test_fast_hash_missing_file(self):
        """Test that _fast_hash raises FileIdentityError for missing files."""
        fname = self._write_temp(b"temp")
        identity = FileIdentity(fname)
        os.remove(fname)
        with self.assertRaises(FileIdentityError):
            identity._fast_hash()

    def test_identity_file_deleted_after_capture(self):
        """Test that deleting a file after identity capture is detected."""
        fname = self._write_temp(b"content")
        id1 = FileIdentity(fname)
        os.remove(fname)
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)
        self.assertTrue(id1)
        self.assertFalse(id2)

    @unittest.skipIf(IS_WIN, "chmod doesn't work the same on Windows")
    def test_identity_comparison_unreadable_file(self):
        """Test that comparing identities raises FileIdentityError if file becomes unreadable."""
        fname = self._write_temp(b"content")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        # Make file unreadable
        os.chmod(fname, 0o000)
        try:
            with self.assertRaises(FileIdentityError):
                id1 == id2  # noqa: B015
        finally:
            # Restore permissions for cleanup
            os.chmod(fname, 0o644)

    @unittest.skipUnless(IS_WIN, "Windows-specific test")
    def test_identity_comparison_deleted_file_windows(self):
        """Test that comparing identities raises FileIdentityError if file is deleted on Windows."""
        fname = self._write_temp(b"content")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        # Delete the file
        os.remove(fname)
        # Comparison should fail when trying to compute hash
        with self.assertRaises(FileIdentityError):
            id1 == id2  # noqa: B015

    def test_identity_with_hash_equal(self):
        """Test that FileIdentity equality considers hash values when set."""
        fname = self._write_temp(b"content")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        id1._hash = "abc123"
        id2._hash = "abc123"
        self.assertEqual(id1, id2)

    def test_identity_with_hash_different(self):
        """Test that FileIdentity detects different hash values."""
        fname = self._write_temp(b"content")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        id1._hash = "abc123"
        id2._hash = "def456"
        self.assertNotEqual(id1, id2)

    def test_identity_mtime_change_same_content(self):
        """Test that files with different mtime are not equal even if content is same."""
        fname = self._write_temp(b"same content")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        os.utime(fname, (stat.st_atime, stat.st_mtime + 2))
        id2 = FileIdentity(fname)
        # Different mtime means not equal, regardless of content
        self.assertNotEqual(id1, id2)

    def test_identity_mtime_change_different_content(self):
        """Test that files with different content and different mtime are not equal."""
        fname = self._write_temp(b"original")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        with open(fname, "wb") as f:
            f.write(b"modified")
        os.utime(fname, (stat.st_atime, stat.st_mtime + 2))
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_no_hash_mtime_preserved(self):
        """Test limitation: content changes with preserved mtime are not detected without hash."""
        fname = self._write_temp(b"original")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        with open(fname, "wb") as f:
            f.write(b"modified")
        # Preserve original mtime
        os.utime(fname, (stat.st_atime, stat.st_mtime))
        id2 = FileIdentity(fname)
        # Without comparison, hash not computed yet
        self.assertIsNotNone(id1._hash)
        self.assertIsNotNone(id2._hash)

    def test_identity_hash_detects_content_change_same_mtime(self):
        """Test limitation: lazy hash computation reads current file state, not creation state."""
        fname = self._write_temp(b"original")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        with open(fname, "wb") as f:
            f.write(b"modified")
        # Preserve original mtime
        os.utime(fname, (stat.st_atime, stat.st_mtime))
        id2 = FileIdentity(fname)
        # Lazy hash computation reads current file (both read "modified")
        result = id1 == id2
        # Now detects content change even if mtime preserved
        self.assertFalse(result)
        self.assertIsNotNone(id1._hash)
        self.assertIsNotNone(id2._hash)
        # Hashes differ because file contents changed between instances
        self.assertNotEqual(id1._hash, id2._hash)

    def test_identity_replaced_file_same_content(self):
        """Test that replacing a file with identical content but new inode is detected."""
        fname = self._write_temp(b"AAAA")
        id1 = FileIdentity(fname)
        fd, newname = tempfile.mkstemp()
        self.temp_files.add(newname)
        with os.fdopen(fd, "wb") as f:
            f.write(b"AAAA")
        os.replace(newname, fname)
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_truncated_file_same_mtime(self):
        """Test that truncating a file while preserving mtime is detected."""
        fname = self._write_temp(b"1234567890")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        with open(fname, "wb") as f:
            f.write(b"123")
        # Preserve original mtime
        os.utime(fname, (stat.st_atime, stat.st_mtime))
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

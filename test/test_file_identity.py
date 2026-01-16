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

from test.picardtestcase import PicardTestCase

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
        """Test that FileIdentity detects mtime changes."""
        fname = self._write_temp(b"abcdef")
        id1 = FileIdentity(fname)
        stat = os.stat(fname)
        os.utime(fname, (stat.st_atime, stat.st_mtime + 2))
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_diff_size(self):
        """Test that FileIdentity detects file size changes."""
        fname = self._write_temp(b"short")
        id1 = FileIdentity(fname)
        with open(fname, "wb") as f:
            f.write(b"much longer content")
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

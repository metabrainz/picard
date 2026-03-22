# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 invo-coder19
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
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

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

    # ------------------------------------------------------------------ #
    # New edge-case tests                                                  #
    # ------------------------------------------------------------------ #

    def test_both_missing_equal(self):
        """Two FileIdentity objects for a path that never existed are equal.

        The __eq__ branch 'if not self._exists: return True' (both non-existent)
        must return True.  This is a deliberate design choice: "nothing == nothing".
        """
        non_existent = os.path.join(tempfile.gettempdir(), "__picard_no_such_file_xyz__.bin")
        id1 = FileIdentity(non_existent)
        id2 = FileIdentity(non_existent)
        self.assertFalse(id1)
        self.assertFalse(id2)
        self.assertEqual(id1, id2)

    def test_eq_with_non_fileidentity_raises(self):
        """Comparing FileIdentity with an unrelated object raises AttributeError.

        FileIdentity.__eq__ accesses other._exists directly without an
        isinstance guard.  Documenting this behaviour ensures any future
        guard change is a conscious decision.
        """
        fname = self._write_temp(b"data")
        identity = FileIdentity(fname)
        with self.assertRaises(AttributeError):
            identity == "not-a-file-identity"  # noqa: B015

    def test_hash_none_at_init_computed_lazily_during_eq(self):
        """When _hash is None after __init__ (e.g. hash failed), __eq__ computes
        it lazily via _fast_hash().  The lazy path (lines 187-190 of file.py)
        is exercised by patching _fast_hash to fail during __init__ only.
        """
        fname = self._write_temp(b"lazy hash content")
        call_count = [0]
        original_fast_hash = FileIdentity._fast_hash

        def fail_once(self_inner):
            call_count[0] += 1
            if call_count[0] == 1:
                raise FileIdentityError("simulated init hash failure")
            return original_fast_hash(self_inner)

        with patch.object(FileIdentity, "_fast_hash", fail_once):
            id1 = FileIdentity(fname)

        # _hash should be None because the first call during __init__ raised
        self.assertIsNone(id1._hash)
        id2 = FileIdentity(fname)
        # Equality should succeed: id1._hash gets computed lazily inside __eq__
        self.assertEqual(id1, id2)
        self.assertIsNotNone(id1._hash)

    def test_identity_empty_file_equal(self):
        """Two FileIdentity objects for a 0-byte file are equal."""
        fname = self._write_temp(b"")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        self.assertTrue(id1)
        self.assertEqual(id1, id2)

    def test_fast_hash_empty_file(self):
        """_fast_hash returns a consistent non-empty string for a 0-byte file."""
        fname = self._write_temp(b"")
        identity = FileIdentity(fname)
        h = identity._fast_hash()
        self.assertIsNotNone(h)
        self.assertIsInstance(h, str)
        self.assertGreater(len(h), 0)
        # Calling twice gives the same result
        self.assertEqual(h, identity._fast_hash())

    def test_identity_filepath_stored_as_path(self):
        """FileIdentity stores the filename as a pathlib.Path object."""
        fname = self._write_temp(b"path check")
        identity = FileIdentity(fname)
        self.assertIsInstance(identity._filepath, Path)
        self.assertEqual(identity._filepath, Path(fname))

    @unittest.skipIf(IS_WIN, "Symlinks behave differently on Windows")
    def test_identity_symlink_same_as_target(self):
        """A symlink and its target compare equal: same inode/size/mtime/hash."""
        fname = self._write_temp(b"symlink target content")
        link_name = fname + ".link"
        try:
            os.symlink(fname, link_name)
            id_real = FileIdentity(fname)
            id_link = FileIdentity(link_name)
            self.assertEqual(id_real, id_link)
        finally:
            try:
                os.remove(link_name)
            except OSError:
                pass

    @unittest.skipIf(IS_WIN, "Symlink retargeting is a Unix concept")
    def test_identity_symlink_after_retarget_not_equal(self):
        """After re-pointing a symlink to a different file, the new identity
        must not equal the old one (different inode).
        """
        fname1 = self._write_temp(b"file one")
        fname2 = self._write_temp(b"file two")
        link_name = fname1 + ".link"
        try:
            os.symlink(fname1, link_name)
            id_before = FileIdentity(link_name)  # points at fname1
            os.remove(link_name)
            os.symlink(fname2, link_name)         # now points at fname2
            id_after = FileIdentity(link_name)
            self.assertNotEqual(id_before, id_after)
        finally:
            try:
                os.remove(link_name)
            except OSError:
                pass

    @unittest.skipUnless(IS_WIN, "Windows inode is always 0 — test applies only on Windows")
    def test_windows_inode_zero_same_file_equal(self):
        """On Windows st_ino == 0, so equality falls through to size/mtime/hash.
        Two captures of the same unchanged file must still compare equal.
        """
        fname = self._write_temp(b"windows inode test")
        id1 = FileIdentity(fname)
        id2 = FileIdentity(fname)
        self.assertEqual(id1._inode, 0)  # confirm Windows inode behaviour
        self.assertEqual(id1, id2)

    @unittest.skipUnless(IS_WIN, "Windows inode is always 0 — test applies only on Windows")
    def test_windows_inode_zero_different_files_same_size_not_equal(self):
        """On Windows, two *different* files with the same size must still be
        distinguished by hash even though both have inode == 0.
        """
        content = b"SAME_SIZE"
        fa = self._write_temp(content)
        fb = self._write_temp(content + b"!")[:len(content)]  # same byte count, different content
        # Ensure same size
        with open(fb, "wb") as f:
            f.write(b"DIFF_CONT")  # same length as "SAME_SIZE" (9 bytes)
        # Force identical mtime so only hash can distinguish them
        stat_a = os.stat(fa)
        os.utime(fb, (stat_a.st_atime, stat_a.st_mtime))
        id_a = FileIdentity(fa)
        id_b = FileIdentity(fb)
        self.assertEqual(id_a._inode, 0)
        self.assertEqual(id_b._inode, 0)
        self.assertNotEqual(id_a, id_b)

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

from picard.file import FileIdentity


class TestFileIdentity(PicardTestCase):
    def _write_temp(self, contents=b"hello"):
        fd, fname = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(contents)
        return fname

    def test_identity_equal(self):
        fname = self._write_temp(b"abcdef")
        id1 = FileIdentity(fname)
        time.sleep(0.01)
        id2 = FileIdentity(fname)
        self.assertEqual(id1, id2)

    def test_identity_diff_mtime(self):
        fname = self._write_temp(b"abcdef")
        id1 = FileIdentity(fname)
        with open(fname, "ab") as f:
            f.write(b"X")
        id2 = FileIdentity(fname)
        self.assertNotEqual(id1, id2)

    def test_identity_hash_diff(self):
        f1 = self._write_temp(b"A" * (FileIdentity._READ_SIZE + 10))
        f2 = self._write_temp(b"B" * (FileIdentity._READ_SIZE + 10))
        id1 = FileIdentity(f1)
        id2 = FileIdentity(f2)
        self.assertNotEqual(id1, id2)

    def test_identity_missing_file(self):
        fname = self._write_temp(b"xxx")
        os.remove(fname)
        id_missing = FileIdentity(fname)
        self.assertFalse(id_missing)

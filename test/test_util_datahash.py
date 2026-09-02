# Picard, the next-generation MusicBrainz tagger
#
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import os

from test.picardtestcase import PicardTestCase

from picard.util.datahash import DataHash


class DataHashTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')

    def test_data_must_be_bytes(self):
        with self.assertRaises(TypeError):
            DataHash('foo')

    def test_data(self):
        h = DataHash(b'a')
        self.assertEqual(h.data(), b'a')

    def test_shorthash(self):
        h = DataHash(b'a')
        self.assertEqual(
            h.hash,
            "333fcb4ee1aa7c115355ec66ceac917c8bfd815bf7587d325aec1864edd24e34d5abe2c6b1b5ee3face62fed78dbef802f2a85cb91d455a8f5249d330853cb3c",
        )
        self.assertEqual(h.hash, str(h))
        self.assertEqual(h.shorthash, "333fcb4ee1aa7c11")

    def test_eq(self):
        # DataHash interns by content, so equal data yields the very same instance
        self.assertIs(DataHash(b'a'), DataHash(b'a'))
        self.assertIs(DataHash(b''), DataHash(b''))
        # Equality itself, rather than the identity that interning guarantees
        self.assertEqual(DataHash(b'a'), DataHash(b'a'))
        self.assertNotEqual(DataHash(b'a'), DataHash(b'b'))
        self.assertNotEqual(DataHash(b'a'), DataHash(b''))
        self.assertNotEqual(DataHash(b'a'), None)

    def test_tempfiles(self):
        a = DataHash(b'a')
        self.assertTrue(os.path.exists(a.filename))
        b = DataHash(b'a')
        self.assertTrue(os.path.exists(b.filename))
        self.assertEqual(a.filename, b.filename)
        filename = a.filename
        del a
        self.assertTrue(os.path.exists(filename))
        del b
        self.assertFalse(os.path.exists(filename))

    def test_ordering(self):
        # __lt__ orders by content hash (used e.g. to sort cover-art images).
        a = DataHash(b'a')
        b = DataHash(b'b')
        ordered = sorted([b, a])
        self.assertEqual(ordered, sorted([a, b], key=lambda h: h.hash))
        # Consistent, antisymmetric.
        self.assertEqual(a < b, not (b < a))

    def test_repr(self):
        h = DataHash(b'a')
        self.assertEqual(repr(h), f"<DataHash {h.shorthash}>")

    def test_hashable(self):
        # __hash__ is based on the content hash, so equal-content instances
        # (which are also identical due to interning) collapse in a set.
        h1 = DataHash(b'abc')
        h2 = DataHash(b'abc')
        h3 = DataHash(b'def')
        self.assertEqual(hash(h1), hash(h2))
        self.assertEqual(len({h1, h2, h3}), 2)

    def test_delete_file_on_last_reference(self):
        # Dropping the last reference removes the backing file. This exercises
        # the same _delete_file() path that remove_all_files() fans out to, but
        # per-instance and deterministically -- without touching the
        # process-global registry, which would delete temp files belonging to
        # unrelated live DataHash instances (e.g. cover art) in other tests.
        h = DataHash(b'per-instance-delete')
        filename = h.filename
        self.assertTrue(os.path.exists(filename))
        del h
        self.assertFalse(os.path.exists(filename))

    def test_delete_missing_file_is_safe(self):
        # Deleting an already-removed file must not raise (the error path is
        # swallowed and logged). Triggered per-instance by dropping the last
        # reference after the backing file was removed out from under it.
        h = DataHash(b'delete-twice')
        filename = h.filename
        os.unlink(filename)
        self.assertFalse(os.path.exists(filename))
        # Must not raise even though the file is already gone.
        del h

    def test_data_missing_file_raises_oserror(self):
        h = DataHash(b'read-after-delete')
        os.unlink(h.filename)
        with self.assertRaises(OSError):
            h.data()

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem


class TestRefItemSerialization(PicardTestCase):
    def test_to_dict(self):
        """Test RefItem serialization to dictionary."""
        ref_item = RefItem(
            name="v1.0.0",
            commit="abc123def456",
            is_tag=True,
            is_branch=False,
            is_current=True,
        )

        result = ref_item.to_dict()

        expected = {
            'name': "v1.0.0",
            'commit': "abc123def456",
            'is_tag': True,
            'is_branch': False,
            'is_current': True,
            'ref_type': 'tag',  # Added by enhancement
        }

        self.assertEqual(result, expected)

    def test_from_dict(self):
        """Test RefItem deserialization from dictionary."""
        data = {
            'name': "v1.0.0",
            'commit': "abc123def456",
            'is_tag': True,
            'is_branch': False,
            'is_current': True,
        }

        result = RefItem.from_dict(data)

        self.assertEqual(result.name, "v1.0.0")
        self.assertEqual(result.commit, "abc123def456")
        self.assertTrue(result.is_tag)
        self.assertFalse(result.is_branch)
        self.assertTrue(result.is_current)

    def test_from_dict_missing_optional_fields(self):
        """Test RefItem deserialization with missing optional fields."""
        data = {
            'name': "main",
            'commit': "def456ghi789",
        }

        result = RefItem.from_dict(data)

        self.assertEqual(result.name, "main")
        self.assertEqual(result.commit, "def456ghi789")
        self.assertFalse(result.is_tag)
        self.assertFalse(result.is_branch)
        self.assertFalse(result.is_current)

    def test_roundtrip_serialization(self):
        """Test that serialization and deserialization are symmetric."""
        original = RefItem(
            name="develop",
            commit="ghi789jkl012",
            is_tag=False,
            is_branch=True,
            is_current=False,
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = RefItem.from_dict(data)

        # Should be equal
        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.commit, restored.commit)
        self.assertEqual(original.is_tag, restored.is_tag)
        self.assertEqual(original.is_branch, restored.is_branch)
        self.assertEqual(original.is_current, restored.is_current)

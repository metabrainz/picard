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


class TestRefItemEnhancements(PicardTestCase):
    def test_refitem_equality(self):
        """Test RefItem equality comparison."""
        ref1 = RefItem(name="v1.0.0", commit="abc123")
        ref2 = RefItem(name="v1.0.0", commit="abc123")
        ref3 = RefItem(name="v1.0.0", commit="def456")

        self.assertEqual(ref1, ref2)
        self.assertNotEqual(ref1, ref3)
        self.assertNotEqual(ref1, "not a refitem")

    def test_refitem_hashing(self):
        """Test RefItem can be used in sets and dicts."""
        ref1 = RefItem(name="v1.0.0", commit="abc123")
        ref2 = RefItem(name="v1.0.0", commit="abc123")
        ref3 = RefItem(name="v1.0.1", commit="def456")

        ref_set = {ref1, ref2, ref3}
        self.assertEqual(len(ref_set), 2)  # ref1 and ref2 are the same

        ref_dict = {ref1: "first", ref2: "second", ref3: "third"}
        self.assertEqual(len(ref_dict), 2)
        self.assertEqual(ref_dict[ref1], "second")  # ref2 overwrote ref1

    def test_refitem_sorting(self):
        """Test RefItem sorting (tags first, then branches, then by name)."""
        branch1 = RefItem(name="main", is_branch=True)
        branch2 = RefItem(name="develop", is_branch=True)
        tag1 = RefItem(name="v2.0.0", is_tag=True)
        tag2 = RefItem(name="v1.0.0", is_tag=True)

        items = [branch1, tag1, branch2, tag2]
        sorted_items = sorted(items)

        # Tags should come first, then branches, sorted by name within each type
        expected_order = [tag2, tag1, branch2, branch1]  # v1.0.0, v2.0.0, develop, main
        self.assertEqual(sorted_items, expected_order)

    def test_refitem_validation(self):
        """Test RefItem validation methods."""
        valid_ref = RefItem(name="v1.0.0", commit="abc123")
        commit_only = RefItem(name="", commit="abc123")
        name_only = RefItem(name="v1.0.0", commit="")
        empty_ref = RefItem(name="", commit="")

        self.assertTrue(valid_ref.is_valid())
        self.assertTrue(commit_only.is_valid())
        self.assertTrue(name_only.is_valid())
        self.assertFalse(empty_ref.is_valid())

    def test_refitem_commit_only_detection(self):
        """Test detection of commit-only RefItems."""
        commit_only1 = RefItem(name="", commit="abc123")
        commit_only2 = RefItem(name="abc123", commit="abc123")
        commit_only3 = RefItem(name="abc1234", commit="abc1234567890")  # short commit as name
        named_ref = RefItem(name="v1.0.0", commit="abc123")

        self.assertTrue(commit_only1.is_commit_only())
        self.assertTrue(commit_only2.is_commit_only())
        self.assertTrue(commit_only3.is_commit_only())
        self.assertFalse(named_ref.is_commit_only())

    def test_refitem_type_detection(self):
        """Test RefItem type detection."""
        tag = RefItem(name="v1.0.0", is_tag=True)
        branch = RefItem(name="main", is_branch=True)
        commit = RefItem(name="", commit="abc123")
        unknown = RefItem(name="something", commit="abc123")

        self.assertEqual(tag.get_ref_type(), "tag")
        self.assertEqual(branch.get_ref_type(), "branch")
        self.assertEqual(commit.get_ref_type(), "commit")
        self.assertEqual(unknown.get_ref_type(), "unknown")

    def test_refitem_copy(self):
        """Test RefItem copying with overrides."""
        original = RefItem(name="v1.0.0", commit="abc123", is_tag=True)

        # Copy without changes
        copy1 = original.copy()
        self.assertEqual(original, copy1)
        self.assertIsNot(original, copy1)

        # Copy with changes
        copy2 = original.copy(is_current=True, name="v1.0.1")
        self.assertEqual(copy2.name, "v1.0.1")
        self.assertEqual(copy2.commit, "abc123")
        self.assertTrue(copy2.is_current)
        self.assertTrue(copy2.is_tag)

    def test_refitem_enhanced_serialization(self):
        """Test enhanced RefItem serialization with validation."""
        ref = RefItem(name="v1.0.0", commit="abc123", is_tag=True, is_current=True)

        # Test serialization
        data = ref.to_dict()
        self.assertIn('ref_type', data)
        self.assertEqual(data['ref_type'], 'tag')

        # Test deserialization
        restored = RefItem.from_dict(data)
        self.assertEqual(ref, restored)
        self.assertEqual(restored.get_ref_type(), 'tag')

    def test_refitem_serialization_validation(self):
        """Test RefItem deserialization validation."""
        # Test invalid data types
        with self.assertRaises(ValueError):
            RefItem.from_dict("not a dict")

        # Test missing required data
        with self.assertRaises(ValueError):
            RefItem.from_dict({'name': '', 'commit': ''})

        # Test valid minimal data
        ref = RefItem.from_dict({'name': 'v1.0.0', 'commit': ''})
        self.assertEqual(ref.name, 'v1.0.0')
        self.assertEqual(ref.commit, '')

    def test_refitem_create_from_ref_name(self):
        """Test RefItem creation from ref names with type detection."""
        # Test tag ref
        tag_ref = RefItem.create_from_ref_name("refs/tags/v1.0.0", "abc123")
        self.assertEqual(tag_ref.name, "v1.0.0")
        self.assertTrue(tag_ref.is_tag)
        self.assertFalse(tag_ref.is_branch)

        # Test branch ref
        branch_ref = RefItem.create_from_ref_name("refs/heads/main", "def456")
        self.assertEqual(branch_ref.name, "main")
        self.assertFalse(branch_ref.is_tag)
        self.assertTrue(branch_ref.is_branch)

        # Test remote branch ref
        remote_ref = RefItem.create_from_ref_name("refs/remotes/origin/develop", "ghi789")
        self.assertEqual(remote_ref.name, "develop")
        self.assertFalse(remote_ref.is_tag)
        self.assertTrue(remote_ref.is_branch)

        # Test simple name (assumed to be tag)
        simple_ref = RefItem.create_from_ref_name("v2.0.0", "jkl012")
        self.assertEqual(simple_ref.name, "v2.0.0")
        self.assertTrue(simple_ref.is_tag)
        self.assertFalse(simple_ref.is_branch)

        # Test empty name
        empty_ref = RefItem.create_from_ref_name("", "mno345")
        self.assertEqual(empty_ref.name, "")
        self.assertEqual(empty_ref.commit, "mno345")
        self.assertFalse(empty_ref.is_tag)
        self.assertFalse(empty_ref.is_branch)

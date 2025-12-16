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

from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.manager import PluginManager


class TestGitStateResolution(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = PluginManager()
        self.manager._refs_cache = Mock()

    def test_normalize_ref_parameter_refitem(self):
        """Test normalizing RefItem parameter."""
        ref_item = RefItem(name="v1.0.0", commit="abc123")
        result = self.manager._normalize_ref_parameter(ref_item)
        self.assertEqual(result, ref_item)

    def test_normalize_ref_parameter_string(self):
        """Test normalizing string parameter."""
        result = self.manager._normalize_ref_parameter("v1.0.0")
        self.assertIsInstance(result, RefItem)
        self.assertEqual(result.name, "v1.0.0")
        self.assertEqual(result.commit, "")

    def test_normalize_ref_parameter_none(self):
        """Test normalizing None parameter."""
        result = self.manager._normalize_ref_parameter(None)
        self.assertIsNone(result)

    def test_default_ref_preference_tags_over_branches(self):
        """Test that tags are preferred over branches."""
        ref_items = [
            RefItem(name="main", commit="abc123", is_branch=True),
            RefItem(name="v1.0.0", commit="abc123", is_tag=True),
        ]

        result = self.manager._default_ref_preference(ref_items)
        self.assertEqual(result.name, "v1.0.0")
        self.assertTrue(result.is_tag)

    def test_default_ref_preference_no_tags(self):
        """Test preference when no tags are available."""
        ref_items = [
            RefItem(name="main", commit="abc123", is_branch=True),
            RefItem(name="develop", commit="abc123", is_branch=True),
        ]

        result = self.manager._default_ref_preference(ref_items)
        self.assertEqual(result.name, "main")  # First item

    def test_prefer_known_tag(self):
        """Test preferring known tag names."""
        ref_items = [
            RefItem(name="main", commit="abc123", is_branch=True),
            RefItem(name="v1.0.0", commit="abc123", is_tag=True),
            RefItem(name="v1.1.0", commit="abc123", is_tag=True),
        ]
        known_tags = ["v1.1.0", "v2.0.0"]

        result = self.manager._prefer_known_tag(ref_items, known_tags)
        self.assertEqual(result.name, "v1.1.0")

    def test_prefer_known_tag_fallback(self):
        """Test fallback when no known tags match."""
        ref_items = [
            RefItem(name="main", commit="abc123", is_branch=True),
            RefItem(name="v1.0.0", commit="abc123", is_tag=True),
        ]
        known_tags = ["v2.0.0", "v3.0.0"]

        result = self.manager._prefer_known_tag(ref_items, known_tags)
        self.assertEqual(result.name, "v1.0.0")  # Falls back to tag preference

    def test_get_ref_item_from_commit_single_item(self):
        """Test getting RefItem when only one exists for commit."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123"
        ref_item = RefItem(name="v1.0.0", commit=commit_id, is_tag=True)

        self.manager._refs_cache.get_ref_items_for_commit.return_value = [ref_item]

        result = self.manager._get_ref_item_from_commit(plugin_uuid, commit_id)
        self.assertEqual(result, ref_item)

    def test_get_ref_item_from_commit_no_items(self):
        """Test getting RefItem when no items exist for commit."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123"

        self.manager._refs_cache.get_ref_items_for_commit.return_value = []

        result = self.manager._get_ref_item_from_commit(plugin_uuid, commit_id)
        self.assertEqual(result.name, "")
        self.assertEqual(result.commit, commit_id)

    def test_get_ref_item_from_commit_with_preference(self):
        """Test getting RefItem with custom preference method."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123"
        ref_items = [
            RefItem(name="main", commit=commit_id, is_branch=True),
            RefItem(name="v1.0.0", commit=commit_id, is_tag=True),
        ]

        self.manager._refs_cache.get_ref_items_for_commit.return_value = ref_items

        # Custom preference that prefers branches
        def prefer_branches(items):
            for item in items:
                if getattr(item, 'is_branch', False):
                    return item
            return items[0]

        result = self.manager._get_ref_item_from_commit(plugin_uuid, commit_id, prefer_branches)
        self.assertEqual(result.name, "main")
        self.assertTrue(result.is_branch)

    def test_resolve_annotated_tag_info_exception(self):
        """Test that resolve_annotated_tag_info handles exceptions gracefully."""
        mock_repo = Mock()
        mock_repo.get_references.side_effect = Exception("Git error")

        result = self.manager._resolve_annotated_tag_info(mock_repo, "abc123")
        self.assertEqual(result, [])

    def test_get_ref_item_from_git_state_detached_head_no_tags(self):
        """Test git state resolution for detached HEAD with no matching tags."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123def456"

        mock_repo = Mock()
        mock_repo.get_head_target.return_value = commit_id
        mock_repo.is_head_detached.return_value = True

        # Mock resolve_annotated_tag_info to return no tags
        self.manager._resolve_annotated_tag_info = Mock(return_value=[])

        result = self.manager._get_ref_item_from_git_state(plugin_uuid, mock_repo)

        self.assertEqual(result.name, "abc123d")  # Short commit
        self.assertEqual(result.commit, commit_id)

    def test_get_ref_item_from_git_state_on_branch(self):
        """Test git state resolution when on a branch."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123def456"

        mock_repo = Mock()
        mock_repo.get_head_target.return_value = commit_id
        mock_repo.is_head_detached.return_value = False
        mock_repo.get_head_shorthand.return_value = "main"

        result = self.manager._get_ref_item_from_git_state(plugin_uuid, mock_repo)

        self.assertEqual(result.name, "main")
        self.assertEqual(result.commit, commit_id)
        self.assertTrue(result.is_branch)

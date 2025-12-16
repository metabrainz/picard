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

from pathlib import Path
import tempfile

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.refs_cache import RefsCache


class TestRefsCacheEnhanced(PicardTestCase):
    def setUp(self):
        super().setUp()
        from unittest.mock import Mock

        # Create a mock registry with proper cache_path
        self.temp_dir = Path(tempfile.mkdtemp())
        mock_registry = Mock()
        mock_registry.cache_path = str(self.temp_dir / "registry_cache.json")

        self.cache = RefsCache(mock_registry)

    def tearDown(self):
        super().tearDown()
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_ref_items_for_commit(self):
        """Test caching RefItems for a specific commit."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123def456"
        ref_items = [
            RefItem(name="v1.0.0", commit=commit_id, is_tag=True),
            RefItem(name="main", commit=commit_id, is_branch=True),
        ]

        self.cache.cache_ref_items_for_commit(plugin_uuid, commit_id, ref_items)

        # Verify items were cached
        cached_items = self.cache.get_ref_items_for_commit(plugin_uuid, commit_id)
        self.assertEqual(len(cached_items), 2)

        # Check first item
        self.assertEqual(cached_items[0].name, "v1.0.0")
        self.assertEqual(cached_items[0].commit, commit_id)
        self.assertTrue(cached_items[0].is_tag)
        self.assertFalse(cached_items[0].is_branch)

        # Check second item
        self.assertEqual(cached_items[1].name, "main")
        self.assertEqual(cached_items[1].commit, commit_id)
        self.assertFalse(cached_items[1].is_tag)
        self.assertTrue(cached_items[1].is_branch)

    def test_get_ref_items_for_commit_not_found(self):
        """Test getting RefItems for non-existent commit."""
        result = self.cache.get_ref_items_for_commit("nonexistent", "abc123")
        self.assertEqual(result, [])

    def test_add_ref_item_to_commit(self):
        """Test adding a single RefItem to commit cache."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123def456"

        # Add first item
        ref_item1 = RefItem(name="v1.0.0", commit=commit_id, is_tag=True)
        self.cache.add_ref_item_to_commit(plugin_uuid, commit_id, ref_item1)

        cached_items = self.cache.get_ref_items_for_commit(plugin_uuid, commit_id)
        self.assertEqual(len(cached_items), 1)
        self.assertEqual(cached_items[0].name, "v1.0.0")

        # Add second item
        ref_item2 = RefItem(name="main", commit=commit_id, is_branch=True)
        self.cache.add_ref_item_to_commit(plugin_uuid, commit_id, ref_item2)

        cached_items = self.cache.get_ref_items_for_commit(plugin_uuid, commit_id)
        self.assertEqual(len(cached_items), 2)

    def test_add_duplicate_ref_item(self):
        """Test that duplicate RefItems are not added."""
        plugin_uuid = "test-uuid"
        commit_id = "abc123def456"

        ref_item = RefItem(name="v1.0.0", commit=commit_id, is_tag=True)

        # Add same item twice
        self.cache.add_ref_item_to_commit(plugin_uuid, commit_id, ref_item)
        self.cache.add_ref_item_to_commit(plugin_uuid, commit_id, ref_item)

        cached_items = self.cache.get_ref_items_for_commit(plugin_uuid, commit_id)
        self.assertEqual(len(cached_items), 1)  # Should only have one item

    def test_multiple_commits_same_plugin(self):
        """Test caching RefItems for multiple commits of same plugin."""
        plugin_uuid = "test-uuid"
        commit1 = "abc123"
        commit2 = "def456"

        # Cache items for first commit
        ref_items1 = [RefItem(name="v1.0.0", commit=commit1, is_tag=True)]
        self.cache.cache_ref_items_for_commit(plugin_uuid, commit1, ref_items1)

        # Cache items for second commit
        ref_items2 = [RefItem(name="v1.1.0", commit=commit2, is_tag=True)]
        self.cache.cache_ref_items_for_commit(plugin_uuid, commit2, ref_items2)

        # Verify both commits have their items
        cached1 = self.cache.get_ref_items_for_commit(plugin_uuid, commit1)
        cached2 = self.cache.get_ref_items_for_commit(plugin_uuid, commit2)

        self.assertEqual(len(cached1), 1)
        self.assertEqual(cached1[0].name, "v1.0.0")

        self.assertEqual(len(cached2), 1)
        self.assertEqual(cached2[0].name, "v1.1.0")

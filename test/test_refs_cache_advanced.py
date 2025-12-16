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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.refs_cache import RefsCache


class TestRefsCacheAdvanced(PicardTestCase):
    def setUp(self):
        super().setUp()
        # Create a mock registry with proper cache_path
        self.temp_dir = Path(tempfile.mkdtemp())
        mock_registry = Mock()
        mock_registry.cache_path = str(self.temp_dir / "registry_cache.json")

        self.cache = RefsCache(mock_registry)
        self.plugin_uuid = "test-plugin-uuid"
        self.commit_id = "abc123def456"

    def tearDown(self):
        super().tearDown()
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_ref_items_sorted(self):
        """Test that RefItems are returned sorted."""
        ref_items = [
            RefItem(name="main", commit=self.commit_id, is_branch=True),
            RefItem(name="v2.0.0", commit=self.commit_id, is_tag=True),
            RefItem(name="v1.0.0", commit=self.commit_id, is_tag=True),
        ]

        self.cache.cache_ref_items_for_commit(self.plugin_uuid, self.commit_id, ref_items)
        retrieved = self.cache.get_ref_items_for_commit(self.plugin_uuid, self.commit_id)

        # Should be sorted: tags first (v1.0.0, v2.0.0), then branches (main)
        expected_names = ["v1.0.0", "v2.0.0", "main"]
        actual_names = [item.name for item in retrieved]

        self.assertEqual(actual_names, expected_names)

    def test_get_sorted_ref_items_prefer_branches(self):
        """Test getting RefItems with branch preference."""
        ref_items = [
            RefItem(name="main", commit=self.commit_id, is_branch=True),
            RefItem(name="v1.0.0", commit=self.commit_id, is_tag=True),
        ]

        self.cache.cache_ref_items_for_commit(self.plugin_uuid, self.commit_id, ref_items)

        # Test default (prefer tags)
        default_sorted = self.cache.get_sorted_ref_items_for_commit(self.plugin_uuid, self.commit_id)
        self.assertEqual(default_sorted[0].name, "v1.0.0")  # Tag first

        # Test prefer branches
        branch_sorted = self.cache.get_sorted_ref_items_for_commit(self.plugin_uuid, self.commit_id, prefer_tags=False)
        self.assertEqual(branch_sorted[0].name, "main")  # Branch first

    def test_find_ref_items_by_name(self):
        """Test finding RefItems by name across commits."""
        commit1 = "abc123"
        commit2 = "def456"

        # Add same tag name to different commits
        ref_items1 = [RefItem(name="v1.0.0", commit=commit1, is_tag=True)]
        ref_items2 = [RefItem(name="v1.0.0", commit=commit2, is_tag=True)]

        self.cache.cache_ref_items_for_commit(self.plugin_uuid, commit1, ref_items1)
        self.cache.cache_ref_items_for_commit(self.plugin_uuid, commit2, ref_items2)

        matches = self.cache.find_ref_items_by_name(self.plugin_uuid, "v1.0.0")

        self.assertEqual(len(matches), 2)
        commit_ids = [commit_id for commit_id, _ in matches]
        self.assertIn(commit1, commit_ids)
        self.assertIn(commit2, commit_ids)

    def test_find_ref_items_by_name_no_matches(self):
        """Test finding RefItems when no matches exist."""
        ref_items = [RefItem(name="v1.0.0", commit=self.commit_id, is_tag=True)]
        self.cache.cache_ref_items_for_commit(self.plugin_uuid, self.commit_id, ref_items)

        matches = self.cache.find_ref_items_by_name(self.plugin_uuid, "nonexistent")

        self.assertEqual(matches, [])

    def test_cleanup_invalid_ref_items(self):
        """Test cleanup of invalid RefItems."""
        # Create cache with mix of valid and invalid data
        cache_data = {
            'ref_items': {
                self.plugin_uuid: {
                    'commit1': [
                        {'name': 'v1.0.0', 'commit': 'abc123', 'is_tag': True},  # Valid
                        {'name': '', 'commit': ''},  # Invalid (empty)
                    ],
                    'commit2': [
                        {'name': '', 'commit': ''},  # Invalid (will remove entire commit)
                    ],
                    'commit3': [
                        {'invalid': 'data'},  # Invalid structure
                        {'name': 'v2.0.0', 'commit': 'def456', 'is_tag': True},  # Valid
                    ],
                }
            }
        }

        self.cache.save_cache(cache_data)

        removed_count = self.cache.cleanup_invalid_ref_items(self.plugin_uuid)

        # Should remove 3 invalid items
        self.assertEqual(removed_count, 3)

        # Check remaining valid items
        remaining_commit1 = self.cache.get_ref_items_for_commit(self.plugin_uuid, 'commit1')
        self.assertEqual(len(remaining_commit1), 1)
        self.assertEqual(remaining_commit1[0].name, 'v1.0.0')

        remaining_commit2 = self.cache.get_ref_items_for_commit(self.plugin_uuid, 'commit2')
        self.assertEqual(len(remaining_commit2), 0)  # Commit removed entirely

        remaining_commit3 = self.cache.get_ref_items_for_commit(self.plugin_uuid, 'commit3')
        self.assertEqual(len(remaining_commit3), 1)
        self.assertEqual(remaining_commit3[0].name, 'v2.0.0')

    def test_get_ref_items_corrupted_cache(self):
        """Test handling of corrupted cache data."""
        # Create corrupted cache data
        cache_data = {
            'ref_items': {
                self.plugin_uuid: {
                    self.commit_id: [
                        {'name': 'v1.0.0'},  # Missing required fields
                        'not a dict',  # Wrong type
                        {'name': '', 'commit': ''},  # Invalid RefItem
                    ]
                }
            }
        }

        self.cache.save_cache(cache_data)

        # Should return empty list and not crash
        ref_items = self.cache.get_ref_items_for_commit(self.plugin_uuid, self.commit_id)
        self.assertEqual(ref_items, [])

    def test_cleanup_invalid_ref_items_no_invalid_data(self):
        """Test cleanup when no invalid data exists."""
        ref_items = [RefItem(name="v1.0.0", commit=self.commit_id, is_tag=True)]
        self.cache.cache_ref_items_for_commit(self.plugin_uuid, self.commit_id, ref_items)

        removed_count = self.cache.cleanup_invalid_ref_items(self.plugin_uuid)

        self.assertEqual(removed_count, 0)

        # Data should remain unchanged
        remaining = self.cache.get_ref_items_for_commit(self.plugin_uuid, self.commit_id)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].name, "v1.0.0")

    def test_find_ref_items_corrupted_data(self):
        """Test finding RefItems with some corrupted data."""
        # Mix valid and corrupted data
        cache_data = {
            'ref_items': {
                self.plugin_uuid: {
                    'commit1': [
                        {'name': 'v1.0.0', 'commit': 'abc123', 'is_tag': True},  # Valid
                    ],
                    'commit2': [
                        {'invalid': 'data'},  # Corrupted
                    ],
                    'commit3': [
                        {'name': 'v1.0.0', 'commit': 'def456', 'is_tag': True},  # Valid, same name
                    ],
                }
            }
        }

        self.cache.save_cache(cache_data)

        matches = self.cache.find_ref_items_by_name(self.plugin_uuid, "v1.0.0")

        # Should find 2 valid matches, skip corrupted data
        self.assertEqual(len(matches), 2)
        commit_ids = [commit_id for commit_id, _ in matches]
        self.assertIn('commit1', commit_ids)
        self.assertIn('commit3', commit_ids)
        self.assertNotIn('commit2', commit_ids)

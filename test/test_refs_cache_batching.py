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
from unittest.mock import Mock, patch

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.refs_cache import RefsCache


class TestRefsCacheBatching(PicardTestCase):
    def setUp(self):
        super().setUp()
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

    def test_batch_updates_context_manager(self):
        """Test that batch_updates context manager works."""
        # Initially not in batch mode
        self.assertFalse(self.cache._batch_mode)

        with self.cache.batch_updates():
            # Should be in batch mode
            self.assertTrue(self.cache._batch_mode)

        # Should exit batch mode
        self.assertFalse(self.cache._batch_mode)

    def test_batching_reduces_disk_writes(self):
        """Test that batching reduces the number of disk writes."""
        plugin_uuid = "test-plugin"
        commit_id = "abc123"

        ref_items = [
            RefItem(name="v1.0.0", commit=commit_id, is_tag=True),
            RefItem(name="v2.0.0", commit=commit_id, is_tag=True),
        ]

        # Mock the _flush_cache method to count calls
        with patch.object(self.cache, '_flush_cache') as mock_flush:
            # Without batching - should flush after each operation
            self.cache.cache_ref_items_for_commit(plugin_uuid, commit_id, ref_items[:1])
            self.cache.cache_ref_items_for_commit(plugin_uuid, commit_id + "2", ref_items[1:])

            # Should have called flush twice
            self.assertEqual(mock_flush.call_count, 2)

            mock_flush.reset_mock()

            # With batching - should only flush once at the end
            with self.cache.batch_updates():
                self.cache.cache_ref_items_for_commit(plugin_uuid, commit_id + "3", ref_items[:1])
                self.cache.cache_ref_items_for_commit(plugin_uuid, commit_id + "4", ref_items[1:])
                # Should not have flushed yet
                self.assertEqual(mock_flush.call_count, 0)

            # Should flush once when exiting context
            self.assertEqual(mock_flush.call_count, 1)

    def test_dirty_flag_tracking(self):
        """Test that dirty flag is properly tracked."""
        # Initially not dirty
        self.assertFalse(self.cache._dirty)

        # Save some data
        cache_data = {'test': 'data'}
        self.cache.save_cache(cache_data)

        # Should be dirty if not in batch mode (and flushed immediately)
        self.assertFalse(self.cache._dirty)  # Flushed immediately

        # Test with batch mode
        with self.cache.batch_updates():
            self.cache.save_cache({'test': 'data2'})
            # Should be dirty but not flushed
            self.assertTrue(self.cache._dirty)

        # Should be clean after batch ends
        self.assertFalse(self.cache._dirty)

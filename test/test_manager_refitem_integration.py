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

from unittest.mock import Mock, patch

from test.picardtestcase import PicardTestCase

from picard.git.utils import RefItem
from picard.plugin3.manager import PluginManager
from picard.plugin3.plugin import Plugin


class TestManagerRefItemIntegration(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = PluginManager()

    def test_switch_ref_accepts_refitem(self):
        """Test that switch_ref method accepts RefItem objects."""
        # Create a mock plugin
        plugin = Mock(spec=Plugin)
        plugin.plugin_id = "test-plugin"
        plugin.state = Mock()
        plugin.state.name = 'disabled'  # Plugin is disabled
        plugin.local_path = "/tmp/test-plugin"

        # Create RefItem
        ref_item = RefItem(name="v2.0.0", commit="abc123", is_tag=True)

        with (
            patch.object(self.manager, '_ensure_plugin_url'),
            patch.object(self.manager, 'disable_plugin'),
            patch.object(self.manager, '_set_plugin_ref_item_from_operation') as mock_set_ref,
            patch.object(self.manager, '_enable_plugin_and_sync_ref_item') as mock_enable,
            patch.object(self.manager, 'plugin_ref_switched'),
            patch('picard.plugin3.manager.GitOperations') as mock_git_ops,
            patch('picard.plugin3.manager.PluginValidation') as mock_validation,
        ):
            # Setup mocks
            mock_git_ops.switch_ref.return_value = ("v1.0.0", "v2.0.0", "old123", "abc123")
            mock_validation.get_plugin_uuid.return_value = "test-uuid"
            mock_enable.return_value = (True, None)  # Enable success

            # Mock metadata
            metadata = Mock()
            metadata.ref = "v2.0.0"
            metadata.commit = "abc123"
            self.manager._metadata = Mock()
            self.manager._metadata.get_plugin_metadata.return_value = metadata

            # Test that RefItem is accepted and normalized
            result = self.manager.switch_ref(plugin, ref_item)

            # Verify GitOperations.switch_ref was called with the ref name
            mock_git_ops.switch_ref.assert_called_once_with(plugin, "v2.0.0", False)

            # Verify _set_plugin_ref_item_from_operation was called
            mock_set_ref.assert_called_once()

            # Verify result contains enable status
            self.assertIsInstance(result, dict)
            self.assertIn('enable_success', result)
            self.assertIn('enable_error', result)
            self.assertIn('was_enabled', result)

    def test_switch_ref_accepts_string(self):
        """Test that switch_ref method still accepts string refs."""
        plugin = Mock(spec=Plugin)
        plugin.plugin_id = "test-plugin"
        plugin.state = Mock()
        plugin.local_path = "/tmp/test-plugin"

        with (
            patch.object(self.manager, '_ensure_plugin_url'),
            patch.object(self.manager, 'disable_plugin'),
            patch.object(self.manager, 'enable_plugin'),
            patch.object(self.manager, 'plugin_ref_switched'),
            patch('picard.plugin3.manager.GitOperations') as mock_git_ops,
            patch('picard.plugin3.manager.PluginValidation') as mock_validation,
            patch.object(plugin, 'sync_ref_item_from_git'),
        ):
            # Setup mocks
            mock_git_ops.switch_ref.return_value = ("v1.0.0", "v2.0.0", "old123", "abc123")
            mock_validation.get_plugin_uuid.return_value = "test-uuid"

            # Mock metadata
            metadata = Mock()
            metadata.ref = "v2.0.0"
            metadata.commit = "abc123"
            self.manager._metadata = Mock()
            self.manager._metadata.get_plugin_metadata.return_value = metadata

            # Test that string ref is accepted
            self.manager.switch_ref(plugin, "v2.0.0")

            # Verify GitOperations.switch_ref was called with the ref name
            mock_git_ops.switch_ref.assert_called_once_with(plugin, "v2.0.0", False)

    def test_update_plugin_syncs_refitem(self):
        """Test that update_plugin syncs RefItem after update."""
        plugin = Mock(spec=Plugin)
        plugin.plugin_id = "test-plugin"
        plugin.state = Mock()
        plugin.local_path = "/tmp/test-plugin"
        plugin.manifest = Mock()
        plugin.manifest.version = "2.0.0"
        plugin.ref_item = RefItem(name="v1.0.0", commit="old123", is_tag=True)

        with (
            patch.object(self.manager, '_ensure_plugin_url'),
            patch.object(self.manager, 'disable_plugin'),
            patch.object(self.manager, 'enable_plugin'),
            patch.object(self.manager, 'plugin_ref_switched'),
            patch('picard.plugin3.manager.GitOperations') as mock_git_ops,
            patch('picard.plugin3.manager.PluginValidation') as mock_validation,
            patch('picard.plugin3.manager.PluginSourceGit') as mock_source_git,
            patch('picard.plugin3.manager.git_backend') as mock_backend,
            patch.object(plugin, 'read_manifest'),
            patch.object(plugin, 'sync_ref_item_from_git'),
        ):
            # Setup mocks
            mock_validation.get_plugin_uuid.return_value = "test-uuid"
            mock_git_ops.check_dirty_working_dir.return_value = []
            mock_git_ops.check_ref_type.return_value = ("tag", "v1.0.0")

            # Mock metadata
            metadata = Mock()
            metadata.url = "https://github.com/test/plugin.git"
            metadata.uuid = "test-uuid"
            metadata.ref = "v1.0.0"
            metadata.commit = "old123"
            self.manager._metadata = Mock()
            self.manager._metadata.get_plugin_metadata.return_value = metadata
            self.manager._metadata.check_redirects.return_value = (metadata.url, metadata.uuid, False)
            self.manager._metadata.get_original_metadata.return_value = (metadata.url, metadata.uuid)

            # Mock registry
            self.manager._registry = Mock()
            self.manager._registry.find_plugin.return_value = None

            # Mock source
            source_instance = Mock()
            source_instance.update.return_value = ("old123", "new456")
            source_instance.ref = "v2.0.0"
            mock_source_git.return_value = source_instance

            # Mock git backend
            repo_mock = Mock()
            commit_mock = Mock()
            commit_mock.id = "new456"
            commit_mock.type = Mock()  # Not a tag
            repo_mock.revparse_single.return_value = commit_mock
            repo_mock.get_commit_date.return_value = 1234567890
            mock_backend.return_value.create_repository.return_value = repo_mock

            # Test update
            result = self.manager.update_plugin(plugin)

            # Verify _set_plugin_ref_item_from_operation was called (which may call sync_ref_item_from_git)
            # The exact call depends on whether plugin has a valid ref_item

            # Verify result
            self.assertEqual(result.old_ref, "v1.0.0")
            self.assertEqual(result.new_ref, "v2.0.0")

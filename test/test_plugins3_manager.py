# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockPlugin,
    MockTagger,
)

from picard.git.ops import GitOperations
from picard.plugin3.manager import (
    PluginManager,
    PluginManifestInvalidError,
)
from picard.plugin3.plugin import PluginState
from picard.plugin3.validation import PluginValidation


class TestPluginManagerHelpers(PicardTestCase):
    def test_validate_manifest_valid(self):
        """Test _validate_manifest with valid manifest."""
        mock_manifest = Mock()
        mock_manifest.validate.return_value = []

        # Should not raise
        PluginValidation.validate_manifest(mock_manifest)

    def test_validate_manifest_invalid(self):
        """Test _validate_manifest with invalid manifest."""
        mock_manifest = Mock()
        mock_manifest.validate.return_value = ['Error 1', 'Error 2']

        from picard.plugin3.manager import PluginManifestInvalidError

        with self.assertRaises(PluginManifestInvalidError) as context:
            PluginValidation.validate_manifest(mock_manifest)

        self.assertIn('Invalid MANIFEST.toml', str(context.exception))

    def test_get_plugin_uuid_missing(self):
        """Test _get_plugin_uuid when UUID is missing."""
        from picard.plugin3.manager import PluginNoUUIDError

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.manifest = None
        mock_plugin.uuid = None

        with self.assertRaises(PluginNoUUIDError) as context:
            PluginValidation.get_plugin_uuid(mock_plugin)

        self.assertIn('has no UUID', str(context.exception))

    def test_get_plugin_uuid_success(self):
        """Test _get_plugin_uuid with valid UUID."""
        mock_plugin = MockPlugin()
        mock_plugin.manifest.uuid = 'test-uuid-123'
        mock_plugin.uuid = 'test-uuid-123'

        result = PluginValidation.get_plugin_uuid(mock_plugin)

        self.assertEqual(result, 'test-uuid-123')

    def test_get_config_value(self):
        """Test _get_config_value helper."""
        with patch('picard.config.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.setting = {'plugins3': {'enabled': ['plugin1']}}
            mock_get_config.return_value = mock_config

    def test_cleanup_temp_directories(self):
        """Test that temp directories are cleaned up."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create some temp directories
            temp1 = plugin_dir / '.tmp-plugin-abc123'
            temp2 = plugin_dir / '.tmp-plugin-def456'
            normal = plugin_dir / 'normal_plugin'

            temp1.mkdir()
            temp2.mkdir()
            normal.mkdir()

            # Create a file in temp1 to ensure recursive cleanup
            (temp1 / 'test.txt').write_text('test')

            manager = PluginManager(None)
            manager._primary_plugin_dir = plugin_dir

            # Run cleanup
            manager._cleanup_temp_directories()

            # Temp directories should be removed
            self.assertFalse(temp1.exists())
            self.assertFalse(temp2.exists())
            # Normal directory should remain
            self.assertTrue(normal.exists())

    def test_cleanup_registers_with_tagger(self):
        """Test that cleanup is registered with tagger."""
        mock_tagger = MockTagger()
        mock_tagger.register_cleanup = Mock()

        manager = PluginManager(mock_tagger)

        # Should have registered cleanup
        mock_tagger.register_cleanup.assert_called_once_with(manager._cleanup_temp_directories)

    def test_add_directory_skips_hidden(self):
        """Test that add_directory skips hidden directories."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Create hidden and normal directories
            hidden = plugin_dir / '.hidden'
            normal = plugin_dir / 'normal'

            hidden.mkdir()
            normal.mkdir()

            # Create minimal MANIFEST.toml in normal dir
            manifest_content = """name = "Test"
authors = ["Test"]
version = "1.0.0"
description = "Test"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
uuid = "3fa397ec-0f2a-47dd-9223-e47ce9f2d692"
"""
            (normal / 'MANIFEST.toml').write_text(manifest_content)

            manager = PluginManager(None)
            manager.add_directory(str(plugin_dir), primary=True)

            # Should only have loaded the normal plugin
            plugin_names = [p.plugin_id for p in manager.plugins]
            self.assertIn('normal', plugin_names)
            self.assertNotIn('.hidden', plugin_names)

    def test_check_dirty_working_dir_clean(self):
        """Test _check_dirty_working_dir with clean repo."""
        from pathlib import Path
        import tempfile

        try:
            from picard.git.factory import has_git_backend

            if not has_git_backend():
                self.skipTest("git backend not available")
        except ImportError:
            self.skipTest("git backend not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            from test.test_plugins3_helpers import backend_init_and_commit

            commit_id = backend_init_and_commit(repo_dir, {'test.txt': 'test'}, 'Initial')

            # Reset to clean state
            from picard.git.factory import git_backend

            backend = git_backend()
            repo = backend.create_repository(repo_dir)
            backend.reset_hard(repo, commit_id)
            repo.free()

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertEqual(changes, [])

    def test_check_dirty_working_dir_dirty(self):
        """Test _check_dirty_working_dir with uncommitted changes."""
        from pathlib import Path
        import tempfile

        try:
            from picard.git.factory import has_git_backend

            if not has_git_backend():
                self.skipTest("git backend not available")
        except ImportError:
            self.skipTest("git backend not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            from test.test_plugins3_helpers import backend_init_and_commit

            backend_init_and_commit(repo_dir, {'test.txt': 'test'}, 'Initial')

            # Modify the file (uncommitted change)
            (repo_dir / 'test.txt').write_text('modified')

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertIn('test.txt', changes)

    def test_update_plugin_dirty_raises_error(self):
        """Test that update_plugin raises PluginDirtyError for dirty repo."""
        from picard.plugin3.manager import PluginDirtyError, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'test-uuid'
        mock_plugin.uuid = 'test-uuid'

        manager = PluginManager(None)

        # Set up metadata so the plugin has a URL
        manager._save_plugin_metadata(
            PluginMetadata(
                name='test-plugin',
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc123',
                uuid='test-uuid',
            )
        )

        with patch('picard.plugin3.manager.GitOperations.check_dirty_working_dir', return_value=['modified.txt']):
            with self.assertRaises(PluginDirtyError) as context:
                manager.update_plugin(mock_plugin)

        self.assertEqual(context.exception.plugin_name, 'test-plugin')
        self.assertIn('modified.txt', context.exception.changes)

    def test_update_plugin_dirty_with_discard(self):
        """Test that update_plugin works with discard_changes=True."""
        from picard.plugin3.manager import PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'test-uuid'
        mock_plugin.manifest.version = '1.0.0'
        mock_plugin.uuid = 'test-uuid'

        manager = PluginManager(None)
        manager._metadata.get_plugin_metadata = Mock(
            return_value=PluginMetadata(url='https://example.com', ref='main', commit='abc123', uuid='test-uuid')
        )
        manager._metadata.check_redirects = Mock(return_value=('https://example.com', 'test-uuid', False))

        # Mock check_ref_type to return branch (not commit)
        with patch('picard.plugin3.manager.update.GitOperations.check_ref_type', return_value=('branch', 'main')):
            # Mock the git update
            with patch('picard.plugin3.manager.update.PluginSourceGit') as mock_source:
                mock_source_instance = Mock()
                mock_source_instance.update = Mock(return_value=('old123', 'new456'))
                mock_source.return_value = mock_source_instance

                # Mock git backend at import location
                with patch('picard.plugin3.manager.update.git_backend') as mock_backend_func:
                    mock_backend = Mock()
                    mock_repo = Mock()
                    mock_commit = Mock()
                    mock_commit.id = 'new456'
                    mock_commit.type = Mock()  # Not a tag
                    mock_repo.revparse_single = Mock(return_value=mock_commit)
                    mock_repo.revparse_to_commit = Mock(return_value=mock_commit)
                    mock_repo.get_commit_date = Mock(return_value=1234567890)
                    mock_repo.free = Mock()
                    # Make mock_repo support context manager protocol
                    mock_repo.__enter__ = Mock(return_value=mock_repo)
                    mock_repo.__exit__ = Mock(return_value=False)
                    mock_backend.create_repository = Mock(return_value=mock_repo)
                    mock_backend_func.return_value = mock_backend

                    # Mock the signal emission to avoid type checking issues
                    with patch.object(manager, 'plugin_ref_switched'):
                        # Mock _with_plugin_repo to avoid git operations
                        with patch.object(manager, '_with_plugin_repo', return_value=('new456', 1234567890)):
                            # Should not raise with discard_changes=True
                            result = manager.update_plugin(mock_plugin, discard_changes=True)

                    self.assertEqual(result.old_commit, 'old123')
                    self.assertEqual(result.new_commit, 'new456')
                    self.assertEqual(result.commit_date, 1234567890)

    def test_switch_ref_dirty_raises_error(self):
        """Test that switch_ref raises PluginDirtyError for dirty repo."""
        from picard.plugin3.manager import PluginDirtyError
        from picard.plugin3.plugin import Plugin

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'test-uuid'

        with patch('picard.git.ops.clean_python_cache'):
            with patch('picard.git.ops.GitOperations.check_dirty_working_dir', return_value=['modified.txt']):
                with self.assertRaises(PluginDirtyError) as context:
                    GitOperations.switch_ref(mock_plugin, 'develop')

        self.assertEqual(context.exception.plugin_name, 'test-plugin')
        self.assertIn('modified.txt', context.exception.changes)

    def test_install_plugin_reinstall_dirty_check(self):
        """Test that install_plugin checks for dirty working dir on reinstall."""
        from pathlib import Path
        import tempfile

        try:
            from picard.git.factory import has_git_backend

            if not has_git_backend():
                self.skipTest("git backend not available")
        except ImportError:
            self.skipTest("git backend not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            manager = PluginManager(None)
            manager._primary_plugin_dir = plugin_dir

            # Create existing plugin with uncommitted changes
            existing = plugin_dir / 'test_plugin_uuid'
            from test.test_plugins3_helpers import backend_init_and_commit

            commit_id = backend_init_and_commit(existing, {'test.txt': 'test'}, 'Initial')

            # Reset to clean state
            from picard.git.factory import git_backend

            backend = git_backend()
            repo = backend.create_repository(existing)
            backend.reset_hard(repo, commit_id)
            repo.free()

            # Modify file (uncommitted change)
            (existing / 'test.txt').write_text('modified')

            # Check that dirty check works
            changes = GitOperations.check_dirty_working_dir(existing)
            self.assertIn('test.txt', changes)

    def test_get_plugin_registry_id_found(self):
        """Test get_plugin_registry_id returns registry ID when plugin is in registry."""
        from test.test_plugins3_helpers import create_test_registry

        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin with manifest and UUID
        mock_plugin = MockPlugin()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'
        mock_plugin.uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

        registry_id = manager._metadata.get_plugin_registry_id(mock_plugin)
        self.assertEqual(registry_id, 'example-plugin')

    def test_get_plugin_registry_id_not_found(self):
        """Test get_plugin_registry_id returns None when plugin not in registry."""
        from test.test_plugins3_helpers import create_test_registry

        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin with manifest and UUID
        mock_plugin = MockPlugin()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'nonexistent-uuid'

        registry_id = manager._metadata.get_plugin_registry_id(mock_plugin)
        self.assertIsNone(registry_id)

    def test_get_plugin_registry_id_no_uuid(self):
        """Test get_plugin_registry_id returns None when plugin has no UUID."""
        from test.test_plugins3_helpers import create_test_registry

        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin without UUID
        mock_plugin = MockPlugin()
        mock_plugin.manifest = None

        registry_id = manager._metadata.get_plugin_registry_id(mock_plugin)
        self.assertIsNone(registry_id)

    def test_get_plugin_metadata_dict_format(self):
        """Test get_plugin_metadata returns PluginMetadata object by UUID."""
        from picard.config import get_config
        from picard.plugin3.manager import PluginMetadata
        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        metadata_manager = PluginMetadataManager(manager._registry)

        test_uuid = 'test-uuid-123'
        test_metadata = {
            'uuid': test_uuid,
            'url': 'https://example.com/plugin.git',
            'ref': 'main',
            'commit': 'abc123',
        }
        config = get_config()
        config.setting['plugins3_metadata'] = {test_uuid: test_metadata}

        result = metadata_manager.get_plugin_metadata(test_uuid)
        self.assertIsInstance(result, PluginMetadata)
        self.assertEqual(result.uuid, test_uuid)
        self.assertEqual(result.url, 'https://example.com/plugin.git')
        self.assertEqual(result.ref, 'main')
        self.assertEqual(result.commit, 'abc123')

    def test_get_plugin_metadata_not_found(self):
        """Test get_plugin_metadata returns None when UUID not found."""
        from picard.config import get_config
        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        metadata_manager = PluginMetadataManager(manager._registry)

        config = get_config()
        config.setting['plugins3_metadata'] = {}

        result = metadata_manager.get_plugin_metadata('nonexistent-uuid')
        self.assertIsNone(result)

    def test_check_uuid_conflict_no_conflict(self):
        """Test _check_uuid_conflict returns False when no conflict exists."""
        from unittest.mock import Mock

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create a mock manifest
        manifest = Mock()
        manifest.uuid = 'test-uuid-123'

        # No existing plugins, should have no conflict
        has_conflict, existing_plugin = manager._check_uuid_conflict(manifest, 'https://example.com/plugin.git')
        self.assertFalse(has_conflict)
        self.assertIsNone(existing_plugin)

    def test_check_uuid_conflict_same_source(self):
        """Test _check_uuid_conflict returns False for same UUID from same source."""
        from unittest.mock import Mock

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create existing plugin with same UUID and source
        existing_plugin = Mock()
        existing_plugin.plugin_id = 'existing_plugin'
        existing_plugin.local_path = '/path/to/plugin'
        existing_plugin.manifest = Mock()
        existing_plugin.manifest.uuid = 'test-uuid-123'

        # Mock metadata to return same source URL
        manager._metadata = Mock()
        manager._metadata.get_plugin_metadata.return_value = Mock(url='https://example.com/plugin.git')

        # Add to plugins list
        manager._plugins = [existing_plugin]

        # Create new manifest with same UUID
        new_manifest = Mock()
        new_manifest.uuid = 'test-uuid-123'

        # Same source should have no conflict
        has_conflict, conflict_plugin = manager._check_uuid_conflict(new_manifest, 'https://example.com/plugin.git')
        self.assertFalse(has_conflict)
        self.assertIsNone(conflict_plugin)

    def test_check_uuid_conflict_different_source(self):
        """Test _check_uuid_conflict returns True for same UUID from different source."""
        from unittest.mock import Mock

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create existing plugin
        existing_plugin = Mock()
        existing_plugin.plugin_id = 'existing_plugin'
        existing_plugin.local_path = '/path/to/plugin'
        existing_plugin.manifest = Mock()
        existing_plugin.manifest.uuid = 'test-uuid-123'
        existing_plugin.uuid = 'test-uuid-123'

        # Mock metadata to return different source URL
        manager._metadata = Mock()
        manager._metadata.get_plugin_metadata.return_value = Mock(url='https://example.com/original.git')

        # Add to plugins list
        manager._plugins = [existing_plugin]

        # Create new manifest with same UUID
        new_manifest = Mock()
        new_manifest.uuid = 'test-uuid-123'

        # Different source should have conflict
        has_conflict, conflict_plugin = manager._check_uuid_conflict(new_manifest, 'https://example.com/different.git')
        self.assertTrue(has_conflict)
        self.assertEqual(conflict_plugin, existing_plugin)

    @patch('picard.plugin3.manager.git_backend')
    def test_rollback_plugin_to_commit(self, mock_git_backend):
        """Test _rollback_plugin_to_commit method."""
        manager = PluginManager(MockTagger())

        # Create mock plugin
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.local_path = '/path/to/plugin'
        plugin.read_manifest = Mock()

        # Mock git backend
        mock_repo = Mock()
        mock_git_backend.return_value.create_repository.return_value.__enter__.return_value = mock_repo

        # Test rollback
        commit_id = 'abc123'
        manager._rollback_plugin_to_commit(plugin, commit_id)

        # Verify git reset was called
        mock_repo.reset_to_commit.assert_called_once_with(commit_id, hard=True)

        # Verify manifest was re-read
        plugin.read_manifest.assert_called_once()

    @patch('picard.plugin3.manager.git_backend')
    def test_validate_manifest_or_rollback_success(self, mock_git_backend):
        """Test _validate_manifest_or_rollback with successful validation."""
        manager = PluginManager(MockTagger())

        # Create mock plugin
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.read_manifest = Mock()

        # Test successful validation
        manager._validate_manifest_or_rollback(plugin, 'old_commit', False)

        # Verify manifest was read
        plugin.read_manifest.assert_called_once()

    @patch('picard.plugin3.manager.git_backend')
    def test_validate_manifest_or_rollback_failure(self, mock_git_backend):
        """Test _validate_manifest_or_rollback with validation failure."""
        manager = PluginManager(MockTagger())

        # Create mock plugin
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.local_path = '/path/to/plugin'

        # Mock git backend
        mock_repo = Mock()
        mock_git_backend.return_value.create_repository.return_value.__enter__.return_value = mock_repo

        with patch.object(manager, 'enable_plugin') as mock_enable:
            # Make read_manifest fail on first call, succeed on second (after rollback)
            plugin.read_manifest = Mock(side_effect=[PluginManifestInvalidError(['Missing UUID']), None])

            # Test validation failure with rollback
            with self.assertRaises(PluginManifestInvalidError):
                manager._validate_manifest_or_rollback(plugin, 'old_commit', True)

            # Verify rollback was attempted
            mock_repo.reset_to_commit.assert_called_once_with('old_commit', hard=True)

            # Verify plugin was re-enabled after rollback
            mock_enable.assert_called_once()

    @patch('picard.plugin3.manager.update.PluginSourceGit')
    @patch('picard.plugin3.manager.update.git_backend')
    def test_update_plugin_rollback_on_manifest_error(self, mock_git_backend, mock_source_git):
        """Test update_plugin rolls back on manifest validation failure."""
        manager = PluginManager(MockTagger())
        manager._registry = Mock()
        manager._metadata = Mock()

        # Create mock plugin
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.local_path = '/path/to/plugin'
        plugin.state = PluginState.ENABLED
        plugin.manifest = Mock()
        plugin.manifest.version = '1.0.0'
        plugin.uuid = 'test-uuid'

        # Mock metadata
        metadata = Mock()
        metadata.url = 'https://example.com/plugin.git'
        metadata.uuid = 'test-uuid'
        metadata.ref = 'v1.0.0'
        manager._metadata.get_plugin_metadata.return_value = metadata
        manager._metadata.check_redirects.return_value = ('https://example.com/plugin.git', 'test-uuid', False)

        # Mock registry - no versioning scheme to avoid complex tag logic
        manager._registry.find_plugin.return_value = None

        # Mock git operations
        mock_source = Mock()
        mock_source.update.return_value = ('old_commit', 'new_commit')
        mock_source.ref = 'v1.1.0'
        mock_source_git.return_value = mock_source

        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.id = 'new_commit'
        mock_repo.revparse_to_commit.return_value = mock_commit
        mock_repo.get_commit_date.return_value = 1234567890
        mock_git_backend.return_value.create_repository.return_value.__enter__.return_value = mock_repo

        # Mock GitOperations
        with (
            patch('picard.plugin3.manager.update.GitOperations.check_dirty_working_dir', return_value=None),
            patch('picard.plugin3.manager.update.GitOperations.check_ref_type', return_value=('tag', 'v1.0.0')),
            patch.object(manager, 'disable_plugin'),
            patch.object(manager, 'enable_plugin'),
            patch.object(manager, '_rollback_plugin_to_commit') as mock_rollback,
            patch.object(manager, '_with_plugin_repo', return_value=('new_commit', 1234567890)),
        ):
            # Make read_manifest fail on first call (after update), succeed on second (after rollback)
            plugin.read_manifest = Mock(side_effect=[PluginManifestInvalidError(['Missing UUID']), None])

            # Test update with manifest failure
            with self.assertRaises(PluginManifestInvalidError):
                manager.update_plugin(plugin)

            # Verify rollback was called
            mock_rollback.assert_called_once_with(plugin, 'old_commit')

            # Verify plugin was re-enabled after rollback
            manager.enable_plugin.assert_called()

    @patch('picard.plugin3.manager.update.GitOperations')
    def test_switch_ref_rollback_on_manifest_error(self, mock_git_ops):
        """Test switch_ref rolls back on manifest validation failure."""
        manager = PluginManager(MockTagger())
        manager._metadata = Mock()

        # Create mock plugin
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.local_path = '/path/to/plugin'
        plugin.state = PluginState.ENABLED
        plugin.uuid = 'test-uuid'

        # Mock metadata
        metadata = Mock()
        metadata.ref = 'v1.0.0'
        metadata.commit = 'old_commit'
        manager._metadata.get_plugin_metadata.return_value = metadata

        # Mock GitOperations.switch_ref
        from picard.git.backend import GitRef, GitRefType

        old_git_ref = GitRef(name='refs/tags/v1.0.0', target='old_commit', ref_type=GitRefType.TAG)
        new_git_ref = GitRef(name='refs/tags/v1.1.0', target='new_commit', ref_type=GitRefType.TAG)
        mock_git_ops.switch_ref.return_value = (old_git_ref, new_git_ref, 'old_commit', 'new_commit')

        with (
            patch.object(manager, 'disable_plugin'),
            patch.object(manager, 'enable_plugin'),
            patch.object(manager, '_rollback_plugin_to_commit') as mock_rollback,
        ):
            # Make read_manifest fail on first call (after switch), succeed on second (after rollback)
            plugin.read_manifest = Mock(side_effect=[PluginManifestInvalidError(['Missing UUID']), None])

            # Test ref switch with manifest failure
            with self.assertRaises(PluginManifestInvalidError):
                manager.switch_ref(plugin, 'v1.1.0')

            # Verify rollback was called
            mock_rollback.assert_called_once_with(plugin, 'old_commit')

            # Verify plugin was re-enabled after rollback
            manager.enable_plugin.assert_called()

    @patch('picard.plugin3.manager.install.PluginSourceGit')
    @patch('picard.plugin3.manager.install.PluginValidation')
    @patch('picard.plugin3.manager.install.shutil')
    def test_install_plugin_cleanup_on_enable_failure(self, mock_shutil, mock_validation, mock_source_git):
        """Test install_plugin cleans up on manifest validation failure during enable."""
        manager = PluginManager(MockTagger())
        manager._registry = Mock()
        manager._metadata = Mock()
        manager._primary_plugin_dir = Path('/plugins')

        # Mock successful manifest validation during install
        mock_manifest = Mock()
        mock_manifest.uuid = 'test-uuid'
        mock_manifest.name = Mock(return_value='Test Plugin')
        mock_validation.read_and_validate_manifest.return_value = mock_manifest

        # Mock source
        mock_source = Mock()
        mock_source.sync.return_value = 'commit123'
        mock_source.resolved_ref = 'v1.0.0'
        mock_source.resolved_ref_type = 'tag'
        mock_source_git.return_value = mock_source

        # Mock no UUID conflicts
        with (
            patch('picard.plugin3.manager.install.UrlInstallablePlugin') as mock_installable,
            patch.object(manager, '_check_uuid_conflict', return_value=(False, None)),
            patch('picard.plugin3.manager.install.get_plugin_directory_name', return_value='test_plugin'),
            patch.object(Path, 'exists', return_value=False),
            patch.object(Path, 'rename'),
            patch.object(manager, 'enable_plugin') as mock_enable,
        ):
            # Mock blacklist check
            mock_plugin = Mock()
            mock_plugin.is_blacklisted.return_value = (False, None)
            mock_installable.return_value = mock_plugin
            # Make enable_plugin fail with manifest error
            mock_enable.side_effect = PluginManifestInvalidError(['Missing UUID'])

            # Test install with enable failure
            with self.assertRaises(PluginManifestInvalidError):
                manager.install_plugin('https://example.com/plugin.git', enable_after_install=True)

            # Verify plugin was not left in plugins list
            self.assertEqual(len(manager._plugins), 0, "Plugin should be removed from plugins list on failure")

    @patch('picard.plugin3.manager.shutil')
    def test_cleanup_failed_plugin_install(self, mock_shutil):
        """Test _cleanup_failed_plugin_install helper method."""
        manager = PluginManager(MockTagger())

        # Create mock plugin and path
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        final_path = Path('/plugins/test_plugin')

        # Add plugin to manager's plugins list
        manager._plugins = [plugin]

        # Mock path exists
        with patch.object(Path, 'exists', return_value=True):
            # Test cleanup
            manager._cleanup_failed_plugin_install(plugin, 'test_plugin', final_path)

        # Verify plugin was removed from list
        self.assertEqual(len(manager._plugins), 0)

        # Verify directory removal was attempted
        mock_shutil.rmtree.assert_called_once_with(final_path)

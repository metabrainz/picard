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
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)
from test.plugins3.helpers import (
    MockPlugin,
    MockTagger,
    backend_init_and_commit,
    create_test_registry,
)

from picard.config import get_config
from picard.git.backend import (
    GitRef,
    GitRefType,
)
from picard.git.factory import (
    git_backend,
    has_git_backend,
)
from picard.git.ops import GitOperations
from picard.plugin3.manager import (
    PluginDirtyError,
    PluginManager,
    PluginManifestInvalidError,
    PluginNoUUIDError,
)
from picard.plugin3.plugin import (
    Plugin,
    PluginState,
)
from picard.plugin3.plugin_metadata import (
    PluginMetadata,
    PluginMetadataManager,
)
from picard.plugin3.registry import RegistryPlugin
from picard.plugin3.validation import PluginValidation
from picard.plugin3.validator import generate_uuid


def _create_manager():
    """Create a PluginManager with a MockTagger."""
    return PluginManager(MockTagger())


class TestPluginManagerHelpers(PicardTestCase):
    def test_validate_manifest_valid(self):
        """Test _validate_manifest with valid manifest does not raise."""
        mock_manifest = Mock()
        mock_manifest.validate.return_value = []

        # Should not raise
        self.assertIsNone(PluginValidation.validate_manifest(mock_manifest))

    def test_validate_manifest_invalid(self):
        """Test _validate_manifest with invalid manifest."""
        mock_manifest = Mock()
        mock_manifest.validate.return_value = ['Error 1', 'Error 2']

        with self.assertRaises(PluginManifestInvalidError) as context:
            PluginValidation.validate_manifest(mock_manifest)

        self.assertIn('Invalid MANIFEST.toml', str(context.exception))

    def test_get_plugin_uuid_missing(self):
        """Test _get_plugin_uuid when UUID is missing."""
        plugin = MockPlugin()
        plugin.plugin_id = 'test-plugin'
        plugin.manifest = None
        plugin.uuid = None

        with self.assertRaises(PluginNoUUIDError) as context:
            PluginValidation.get_plugin_uuid(plugin)

        self.assertIn('has no UUID', str(context.exception))

    def test_get_plugin_uuid_success(self):
        """Test _get_plugin_uuid with valid UUID."""
        plugin = MockPlugin()
        plugin.manifest.uuid = 'test-uuid-123'
        plugin.uuid = 'test-uuid-123'

        result = PluginValidation.get_plugin_uuid(plugin)

        self.assertEqual(result, 'test-uuid-123')

    def test_cleanup_temp_directories(self):
        """Test that temp directories are cleaned up."""
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
        try:
            if not has_git_backend():
                self.skipTest("git backend not available")
        except ImportError:
            self.skipTest("git backend not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            commit_id = backend_init_and_commit(repo_dir, {'test.txt': 'test'}, 'Initial')

            # Reset to clean state
            backend = git_backend()
            repo = backend.create_repository(repo_dir)
            backend.reset_hard(repo, commit_id)
            repo.free()

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertEqual(changes, [])

    def test_check_dirty_working_dir_dirty(self):
        """Test _check_dirty_working_dir with uncommitted changes."""

        try:
            if not has_git_backend():
                self.skipTest("git backend not available")
        except ImportError:
            self.skipTest("git backend not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            backend_init_and_commit(repo_dir, {'test.txt': 'test'}, 'Initial')

            # Modify the file (uncommitted change)
            (repo_dir / 'test.txt').write_text('modified')

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertIn('test.txt', changes)

    def test_update_plugin_dirty_raises_error(self):
        """Test that update_plugin raises PluginDirtyError for dirty repo."""
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
        try:
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
            commit_id = backend_init_and_commit(existing, {'test.txt': 'test'}, 'Initial')

            # Reset to clean state
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
        manager = _create_manager()
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin with manifest and UUID
        plugin = MockPlugin()
        plugin.manifest = Mock()
        plugin.manifest.uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'
        plugin.uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

        registry_id = manager._metadata.get_plugin_registry_id(plugin)
        self.assertEqual(registry_id, 'example-plugin')

    def test_get_plugin_registry_id_uses_id_property(self):
        """Test get_plugin_registry_id uses .id property, not dict-style .get('id')."""
        registry_plugin = RegistryPlugin({'id': 'my-plugin', 'uuid': 'some-uuid', 'name': 'My Plugin'})
        registry = Mock()
        registry.find_plugin.return_value = registry_plugin
        metadata_manager = PluginMetadataManager(registry)

        plugin = MockPlugin(uuid='some-uuid')

        # Verify __getitem__ raises (dict-style access is forbidden)
        with self.assertRaises(TypeError):
            _ = registry_plugin['id']

        result = metadata_manager.get_plugin_registry_id(plugin)
        self.assertEqual(result, 'my-plugin')

    def test_get_plugin_registry_id_not_found(self):
        """Test get_plugin_registry_id returns None when plugin not in registry."""
        manager = _create_manager()
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin with manifest and UUID
        plugin = MockPlugin()
        plugin.manifest = Mock()
        plugin.manifest.uuid = 'nonexistent-uuid'

        registry_id = manager._metadata.get_plugin_registry_id(plugin)
        self.assertIsNone(registry_id)

    def test_get_plugin_registry_id_no_uuid(self):
        """Test get_plugin_registry_id returns None when plugin has no UUID."""
        manager = _create_manager()
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager._registry)

        # Mock plugin without UUID
        plugin = MockPlugin()
        plugin.manifest = None

        registry_id = manager._metadata.get_plugin_registry_id(plugin)
        self.assertIsNone(registry_id)

    def test_get_plugin_metadata_dict_format(self):
        """Test get_plugin_metadata returns PluginMetadata object by UUID."""
        manager = _create_manager()
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
        manager = _create_manager()
        metadata_manager = PluginMetadataManager(manager._registry)

        config = get_config()
        config.setting['plugins3_metadata'] = {}

        result = metadata_manager.get_plugin_metadata('nonexistent-uuid')
        self.assertIsNone(result)

    def test_check_uuid_conflict_no_conflict(self):
        """Test _check_uuid_conflict returns False when no conflict exists."""
        manager = _create_manager()

        # Create a mock manifest
        manifest = Mock()
        manifest.uuid = 'test-uuid-123'

        # No existing plugins, should have no conflict
        has_conflict, existing_plugin = manager._check_uuid_conflict(manifest, 'https://example.com/plugin.git')
        self.assertFalse(has_conflict)
        self.assertIsNone(existing_plugin)

    def test_check_uuid_conflict_same_source(self):
        """Test _check_uuid_conflict returns False for same UUID from same source."""
        manager = _create_manager()

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
        manager = _create_manager()

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
        manager._validate_manifest_or_rollback(plugin, 'old_commit')

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
                manager._validate_manifest_or_rollback(plugin, 'old_commit')

            # Verify rollback was attempted
            mock_repo.reset_to_commit.assert_called_once_with('old_commit', hard=True)

            # Verify plugin was NOT re-enabled here (wrapper handles it)
            mock_enable.assert_not_called()

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
        manager._registry.is_blacklisted.return_value = (False, None)

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
        manager._registry.find_plugin.return_value = None
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

    def test_get_plugin_versioning_scheme_with_uuid(self):
        """Test get_plugin_versioning_scheme returns scheme when plugin has a UUID."""
        manager = PluginManager(MockTagger())
        manager._registry = create_test_registry()
        manager._metadata = PluginMetadataManager(manager._registry)

        plugin = MockPlugin(uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7')

        # Plugin has a UUID, so the registry lookup should proceed and return a scheme
        # (or empty string if not in registry with a scheme, but must NOT short-circuit)
        result = manager.get_plugin_versioning_scheme(plugin)
        # The result should be a string (not prematurely returning "" due to inverted guard)
        self.assertIsInstance(result, str)

    def test_get_plugin_versioning_scheme_no_uuid(self):
        """Test get_plugin_versioning_scheme returns empty string when plugin has no UUID."""
        manager = PluginManager(MockTagger())
        plugin = MockPlugin()
        plugin.uuid = None

        result = manager.get_plugin_versioning_scheme(plugin)
        self.assertEqual(result, '')

    def test_get_plugin_versioning_scheme_registry_lookup(self):
        """Test get_plugin_versioning_scheme queries registry for plugins with UUID and metadata."""
        manager = PluginManager(MockTagger())

        mock_registry_plugin = Mock()
        mock_registry_plugin.versioning_scheme = 'semver'
        manager._registry = Mock()
        manager._registry.find_plugin.return_value = mock_registry_plugin

        plugin = MockPlugin(uuid='some-uuid-1234')

        # Set up metadata so the registry lookup is reached
        manager._metadata = PluginMetadataManager(manager._registry)
        manager._metadata.get_plugin_metadata = Mock(
            return_value=PluginMetadata(
                url='https://example.com/plugin.git', ref='main', commit='abc', uuid='some-uuid-1234'
            )
        )

        result = manager.get_plugin_versioning_scheme(plugin)
        self.assertEqual(result, 'semver')
        manager._registry.find_plugin.assert_called_once_with(uuid='some-uuid-1234')

    def test_plugin_dirs_not_shared_between_instances(self):
        """_plugin_dirs must be per-instance, not shared across PluginManager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager1 = PluginManager(None)
            manager2 = PluginManager(None)

            manager1.add_directory(tmpdir, primary=True)

            self.assertIn(Path(tmpdir), manager1._plugin_dirs)
            self.assertNotIn(Path(tmpdir), manager2._plugin_dirs)

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


class TestPluginManager(PicardTestCase):
    def test_config_persistence(self):
        """Test that enabled plugins are saved to and loaded from config."""
        manager = _create_manager()

        # Initially no plugins enabled
        self.assertEqual(manager._enabled_plugins, set())

        # Create a mock plugin with UUID
        test_uuid = generate_uuid()
        plugin = MockPlugin(uuid=test_uuid)

        # Enable plugin - should save to config
        manager.enable_plugin(plugin)
        self.assertIn(test_uuid, manager._enabled_plugins)

        # Verify it was saved to config
        config = get_config()
        self.assertIn('plugins3_enabled_plugins', config.setting)
        self.assertIn(test_uuid, config.setting['plugins3_enabled_plugins'])

        # Create new manager instance - should load from config
        manager2 = _create_manager()
        self.assertIn(test_uuid, manager2._enabled_plugins)

        # Disable plugin - should remove from config
        manager2.disable_plugin(plugin)
        self.assertNotIn(test_uuid, manager2._enabled_plugins)
        self.assertNotIn(test_uuid, config.setting['plugins3_enabled_plugins'])

    def test_init_plugins_only_loads_enabled(self):
        """Test that init_plugins only loads plugins that are enabled in config."""
        manager = _create_manager()

        # Create mock plugins with UUIDs
        enabled_uuid = 'enabled-uuid-1234'
        enabled_plugin = Mock(spec=Plugin)
        enabled_plugin.plugin_id = 'enabled-plugin'
        enabled_plugin.manifest = Mock()
        enabled_plugin.manifest.uuid = enabled_uuid
        enabled_plugin.uuid = enabled_uuid
        enabled_plugin.load_module = Mock()
        enabled_plugin.enable = Mock()

        disabled_uuid = 'disabled-uuid-5678'
        disabled_plugin = Mock(spec=Plugin)
        disabled_plugin.plugin_id = 'disabled-plugin'
        disabled_plugin.manifest = Mock()
        disabled_plugin.manifest.uuid = disabled_uuid
        disabled_plugin.uuid = disabled_uuid
        disabled_plugin.load_module = Mock()
        disabled_plugin.enable = Mock()

        manager._plugins = [enabled_plugin, disabled_plugin]
        manager._enabled_plugins = {enabled_uuid}

        # Initialize plugins
        manager.init_plugins()

        # Only enabled plugin should be loaded
        enabled_plugin.load_module.assert_called_once()
        enabled_plugin.enable.assert_called_once_with(manager._tagger)
        disabled_plugin.load_module.assert_not_called()
        disabled_plugin.enable.assert_not_called()

    def test_api_version_compatibility_compatible(self):
        """Test that plugins with compatible API versions are loaded."""
        manager = _create_manager()

        # Load compatible plugin (API 3.0, 3.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'example')

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.plugin_id, 'example')
        self.assertEqual(plugin.manifest.name(), 'Example plugin')

    def test_api_version_compatibility_incompatible_old(self):
        """Test that plugins with old incompatible API versions are rejected."""
        manager = _create_manager()

        # Load incompatible plugin (API 2.0, 2.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'incompatible')

        self.assertIsNone(plugin)

    def test_api_version_compatibility_incompatible_new(self):
        """Test that plugins requiring newer API versions are rejected."""
        manager = _create_manager()

        # Load plugin requiring future API (3.5, 3.6)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'newer-api')

        self.assertIsNone(plugin)


class TestPluginErrors(PicardTestCase):
    """Test error handling in plugin system."""

    def test_load_plugin_with_invalid_manifest(self):
        """Test loading plugin with invalid MANIFEST.toml."""
        manager = _create_manager()

        # Try to load plugin with missing manifest
        plugin = manager._load_plugin(Path('/nonexistent'), 'fake-plugin')
        self.assertIsNone(plugin)

    def test_init_plugins_handles_errors(self):
        """Test that init_plugins handles plugin errors gracefully."""
        manager = _create_manager()

        # Create a plugin that will fail to load
        bad_uuid = 'bad-uuid-1234'
        bad_plugin = Mock(spec=Plugin)
        bad_plugin.plugin_id = 'bad-plugin'
        bad_plugin.manifest = Mock()
        bad_plugin.manifest.uuid = bad_uuid
        bad_plugin.uuid = bad_uuid
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        manager._plugins = [bad_plugin]
        manager._enabled_plugins = {bad_uuid}

        # Should not raise, just log error
        manager.init_plugins()

        # Plugin should have been attempted to load
        bad_plugin.load_module.assert_called_once()

    def test_enable_plugin_with_load_error(self):
        """Test enabling plugin that fails to load."""
        manager = _create_manager()

        bad_plugin = Mock(spec=Plugin)
        bad_plugin.plugin_id = 'bad-plugin'
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        with self.assertRaises(Exception):  # noqa: B017
            manager.enable_plugin(bad_plugin)

    def test_manager_add_directory(self):
        """Test adding plugin directory."""
        manager = _create_manager()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Add directory
            manager.add_directory(str(plugin_dir), primary=True)

            # Should be registered
            self.assertIn(plugin_dir, manager._plugin_dirs)
            self.assertEqual(manager._primary_plugin_dir, plugin_dir)

    def test_manager_add_directory_twice(self):
        """Test adding same directory twice is ignored."""
        manager = _create_manager()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Add directory twice
            manager.add_directory(str(plugin_dir))
            initial_count = len(manager._plugin_dirs)

            manager.add_directory(str(plugin_dir))

            # Should not be added twice
            self.assertEqual(len(manager._plugin_dirs), initial_count)

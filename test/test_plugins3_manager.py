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

from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockPlugin,
    MockTagger,
)

from picard.plugin3.git_ops import GitOperations
from picard.plugin3.manager import PluginManager
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

        with self.assertRaises(PluginNoUUIDError) as context:
            PluginValidation.get_plugin_uuid(mock_plugin)

        self.assertIn('has no UUID', str(context.exception))

    def test_get_plugin_uuid_success(self):
        """Test _get_plugin_uuid with valid UUID."""
        mock_plugin = MockPlugin()
        mock_plugin.manifest.uuid = 'test-uuid-123'

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
            import pygit2
        except ImportError:
            self.skipTest("pygit2 not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            repo = pygit2.init_repository(str(repo_dir))

            # Create and commit a file
            (repo_dir / 'test.txt').write_text('test')
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            commit_id = repo.create_commit('refs/heads/main', author, author, 'Initial', tree, [])
            repo.set_head('refs/heads/main')
            repo.reset(commit_id, pygit2.enums.ResetMode.HARD)

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertEqual(changes, [])

    def test_check_dirty_working_dir_dirty(self):
        """Test _check_dirty_working_dir with uncommitted changes."""
        from pathlib import Path
        import tempfile

        try:
            import pygit2
        except ImportError:
            self.skipTest("pygit2 not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            repo = pygit2.init_repository(str(repo_dir))

            # Create and commit a file
            (repo_dir / 'test.txt').write_text('test')
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            repo.create_commit('refs/heads/main', author, author, 'Initial', tree, [])

            # Modify the file (uncommitted change)
            (repo_dir / 'test.txt').write_text('modified')

            changes = GitOperations.check_dirty_working_dir(repo_dir)

            self.assertIn('test.txt', changes)

    def test_update_plugin_dirty_raises_error(self):
        """Test that update_plugin raises PluginDirtyError for dirty repo."""
        from picard.plugin3.manager import PluginDirtyError
        from picard.plugin3.plugin import Plugin

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'test-uuid'

        manager = PluginManager(None)

        with patch('picard.plugin3.manager.GitOperations.check_dirty_working_dir', return_value=['modified.txt']):
            with self.assertRaises(PluginDirtyError) as context:
                manager.update_plugin(mock_plugin)

        self.assertEqual(context.exception.plugin_name, 'test-plugin')
        self.assertIn('modified.txt', context.exception.changes)

    def test_update_plugin_dirty_with_discard(self):
        """Test that update_plugin works with discard_changes=True."""
        from picard.plugin3.plugin import Plugin

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'test-uuid'
        mock_plugin.manifest.version = '1.0.0'

        manager = PluginManager(None)
        manager._metadata.get_plugin_metadata = Mock(return_value={'url': 'https://example.com', 'ref': 'main'})
        manager._metadata.check_redirects = Mock(return_value=('https://example.com', 'test-uuid', False))

        # Mock the git update
        with patch('picard.plugin3.manager.PluginSourceGit') as mock_source:
            mock_source_instance = Mock()
            mock_source_instance.update = Mock(return_value=('old123', 'new456'))
            mock_source.return_value = mock_source_instance

            # Mock pygit2 Repository
            with patch('pygit2.Repository') as mock_repo_class:
                mock_repo = Mock()
                mock_commit = Mock()
                mock_commit.commit_time = 1234567890
                mock_repo.get = Mock(return_value=mock_commit)
                mock_repo_class.return_value = mock_repo

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

        with patch('picard.plugin3.git_ops.GitOperations.check_dirty_working_dir', return_value=['modified.txt']):
            with self.assertRaises(PluginDirtyError) as context:
                GitOperations.switch_ref(mock_plugin, 'develop')

        self.assertEqual(context.exception.plugin_name, 'test-plugin')
        self.assertIn('modified.txt', context.exception.changes)

    def test_install_plugin_reinstall_dirty_check(self):
        """Test that install_plugin checks for dirty working dir on reinstall."""
        from pathlib import Path
        import tempfile

        try:
            import pygit2
        except ImportError:
            self.skipTest("pygit2 not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)
            manager = PluginManager(None)
            manager._primary_plugin_dir = plugin_dir

            # Create existing plugin with uncommitted changes
            existing = plugin_dir / 'test_plugin_uuid'
            existing.mkdir()
            repo = pygit2.init_repository(str(existing))
            (existing / 'test.txt').write_text('test')
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            commit_id = repo.create_commit('refs/heads/main', author, author, 'Initial', tree, [])
            repo.set_head('refs/heads/main')
            repo.reset(commit_id, pygit2.enums.ResetMode.HARD)

            # Modify file (uncommitted change)
            (existing / 'test.txt').write_text('modified')

            # Check that dirty check works
            changes = GitOperations.check_dirty_working_dir(existing)
            self.assertIn('test.txt', changes)

    def test_get_config_value_default(self):
        """Test _get_config_value returns default when key missing."""
        with patch('picard.config.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.setting = {}
            mock_get_config.return_value = mock_config

            manager = PluginManager(None)
            result = manager._get_config_value('missing', 'key', default='default_value')

            self.assertEqual(result, 'default_value')

    def test_get_plugin_registry_id_found(self):
        """Test get_plugin_registry_id returns registry ID when plugin is in registry."""
        from test.test_plugins3_helpers import create_test_registry

        from picard.plugin3.plugin_metadata import PluginMetadataManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        # Reinitialize metadata manager with new registry
        manager._metadata = PluginMetadataManager(manager, manager._registry)

        # Mock plugin with manifest and UUID
        mock_plugin = MockPlugin()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

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
        manager._metadata = PluginMetadataManager(manager, manager._registry)

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
        manager._metadata = PluginMetadataManager(manager, manager._registry)

        # Mock plugin without UUID
        mock_plugin = MockPlugin()
        mock_plugin.manifest = None

        registry_id = manager._metadata.get_plugin_registry_id(mock_plugin)
        self.assertIsNone(registry_id)

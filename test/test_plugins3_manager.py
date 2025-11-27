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

from picard.plugin3.manager import PluginManager


class TestPluginManagerHelpers(PicardTestCase):
    def test_validate_manifest_valid(self):
        """Test _validate_manifest with valid manifest."""
        manager = PluginManager(None)
        mock_manifest = Mock()
        mock_manifest.validate.return_value = []

        # Should not raise
        manager._validate_manifest(mock_manifest)

    def test_validate_manifest_invalid(self):
        """Test _validate_manifest with invalid manifest."""
        manager = PluginManager(None)
        mock_manifest = Mock()
        mock_manifest.validate.return_value = ['Error 1', 'Error 2']

        with self.assertRaises(ValueError) as context:
            manager._validate_manifest(mock_manifest)

        self.assertIn('Invalid MANIFEST.toml', str(context.exception))

    def test_get_plugin_uuid_missing(self):
        """Test _get_plugin_uuid when UUID is missing."""
        manager = PluginManager(None)
        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_plugin.manifest = None

        with self.assertRaises(ValueError) as context:
            manager._get_plugin_uuid(mock_plugin)

        self.assertIn('has no UUID', str(context.exception))

    def test_get_plugin_uuid_success(self):
        """Test _get_plugin_uuid with valid UUID."""
        manager = PluginManager(None)
        mock_plugin = Mock()
        mock_plugin.manifest.uuid = 'test-uuid-123'

        result = manager._get_plugin_uuid(mock_plugin)

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
        mock_tagger = Mock()
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
            plugin_names = [p.name for p in manager.plugins]
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

            manager = PluginManager(None)
            changes = manager._check_dirty_working_dir(repo_dir)

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

            manager = PluginManager(None)
            changes = manager._check_dirty_working_dir(repo_dir)

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

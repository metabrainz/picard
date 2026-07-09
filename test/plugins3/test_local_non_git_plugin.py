# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
import shutil
import tempfile

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    MockTagger,
    create_test_manifest_content,
    run_cli,
)

from picard.config import get_config
from picard.plugin3.manager import (
    PluginManager,
    PluginManifestNotFoundError,
)
from picard.plugin3.validator import generate_uuid


def _create_plugin_dir(base_dir, uuid):
    """Create a local non-git plugin directory."""
    plugin_name = f'test-lng-{uuid[:8]}'
    plugin_dir = Path(base_dir) / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / 'MANIFEST.toml').write_text(create_test_manifest_content(name='Test LNG Plugin', uuid=uuid))
    (plugin_dir / '__init__.py').write_text('def enable(api): pass\ndef disable(): pass\n')
    return plugin_dir, plugin_name


def _create_manager(plugins_dir):
    """Create a PluginManager without triggering _load_local_plugins."""
    manager = PluginManager(MockTagger())
    manager._primary_plugin_dir = Path(plugins_dir)
    manager._plugin_dirs.append(manager._primary_plugin_dir)
    return manager


class TestLocalNonGitPlugin(PicardTestCase):
    """Tests for non-git local plugin lifecycle."""

    def test_install_and_metadata(self):
        """Install a local non-git plugin and verify metadata."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            manager = _create_manager(plugins_dir)

            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False)
            plugin = manager.plugin_id_to_plugin(plugin_id)

            self.assertIsNotNone(plugin)
            self.assertEqual(plugin.local_path, plugin_dir)
            self.assertEqual(plugin_id, plugin_name)

            metadata = manager._get_plugin_metadata(plugin.uuid)
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata.ref_type, 'local')
            self.assertEqual(metadata.url, str(plugin_dir))
            self.assertEqual(metadata.commit, '')

    def test_install_no_manifest_fails(self):
        """Installing a dir without MANIFEST.toml raises error."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            empty_dir = Path(tmp_dir) / 'empty-plugin'
            empty_dir.mkdir()
            (empty_dir / '__init__.py').write_text('')
            manager = _create_manager(plugins_dir)

            with self.assertRaises(PluginManifestNotFoundError):
                manager.install_plugin(str(empty_dir), enable_after_install=False)

    def test_reinstall(self):
        """Reinstalling a local non-git plugin replaces the existing one."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            manager = _create_manager(plugins_dir)

            manager.install_plugin(str(plugin_dir), enable_after_install=False)
            manager.install_plugin(str(plugin_dir), reinstall=True, enable_after_install=False)

            count = sum(1 for p in manager.plugins if p.plugin_id == plugin_name)
            self.assertEqual(count, 1)

    def test_remove_keeps_files(self):
        """Removing a local non-git plugin unregisters it but keeps files."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            manager = _create_manager(plugins_dir)

            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False)
            plugin = manager.plugin_id_to_plugin(plugin_id)
            manager.uninstall_plugin(plugin)

            self.assertIsNone(manager.plugin_id_to_plugin(plugin_id))
            self.assertIsNone(manager._get_plugin_metadata(uuid))
            self.assertTrue(plugin_dir.exists())
            self.assertTrue((plugin_dir / 'MANIFEST.toml').exists())

    def test_update_reloads(self):
        """Updating a local non-git plugin reloads it and re-reads manifest."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            manager = _create_manager(plugins_dir)

            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False)
            plugin = manager.plugin_id_to_plugin(plugin_id)

            (plugin_dir / 'MANIFEST.toml').write_text(create_test_manifest_content(name='Updated Name', uuid=uuid))

            result = manager.update_plugin(plugin)
            self.assertEqual(result.old_commit, '')
            self.assertEqual(result.new_commit, '')
            self.assertEqual(plugin.manifest.name(), 'Updated Name')

    def test_stale_path_cleanup(self):
        """Local plugin with missing path is auto-removed on startup."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)

            manager = _create_manager(plugins_dir)
            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False)
            plugin = manager.plugin_id_to_plugin(plugin_id)
            actual_uuid = plugin.uuid
            self.assertIsNotNone(manager._get_plugin_metadata(actual_uuid))

            # Delete plugin directory
            shutil.rmtree(plugin_dir)

            # New manager simulates restart — _load_local_plugins should clean up
            manager2 = PluginManager(MockTagger())
            manager2.add_directory(plugins_dir, primary=True)

            self.assertIsNone(manager2.plugin_id_to_plugin(plugin_name))
            self.assertIsNone(manager2._get_plugin_metadata(actual_uuid))


class TestNoGitInstall(PicardTestCase):
    """Tests for installing a git-tracked plugin with no_git=True."""

    def test_install_with_no_git_sets_local_dev_ref_type(self):
        """Install with no_git=True on a .git directory sets ref_type to local-dev."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            # Create a fake .git directory
            (plugin_dir / '.git').mkdir()

            manager = _create_manager(plugins_dir)
            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False, no_git=True)

            plugin = manager.plugin_id_to_plugin(plugin_id)
            metadata = manager._get_plugin_metadata(plugin.uuid)
            self.assertEqual(metadata.ref_type, 'local-dev')
            self.assertEqual(plugin.local_path, plugin_dir)

    def test_install_without_no_git_has_local_ref_type(self):
        """Normal local install (no .git) has ref_type='local'."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)

            manager = _create_manager(plugins_dir)
            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False)

            plugin = manager.plugin_id_to_plugin(plugin_id)
            metadata = manager._get_plugin_metadata(plugin.uuid)
            self.assertEqual(metadata.ref_type, 'local')

    def test_no_git_on_dir_without_git_still_works(self):
        """no_git=True on a dir without .git installs normally as local."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)

            manager = _create_manager(plugins_dir)
            plugin_id = manager.install_plugin(str(plugin_dir), enable_after_install=False, no_git=True)

            plugin = manager.plugin_id_to_plugin(plugin_id)
            metadata = manager._get_plugin_metadata(plugin.uuid)
            self.assertEqual(metadata.ref_type, 'local')

    def test_local_dev_ref_type_persists_in_metadata_dict(self):
        """ref_type='local-dev' is stored in the config dict."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            (plugin_dir / '.git').mkdir()

            manager = _create_manager(plugins_dir)
            manager.install_plugin(str(plugin_dir), enable_after_install=False, no_git=True)

            config = get_config()
            raw = config.setting['plugins3_metadata']
            # Find the entry by looking for our path
            entry = next(v for v in raw.values() if v.get('url') == str(plugin_dir))
            self.assertEqual(entry.get('ref_type'), 'local-dev')

    def test_local_ref_type_has_no_has_git_field(self):
        """Local install has no has_git field and ref_type='local' in config dict."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)

            manager = _create_manager(plugins_dir)
            manager.install_plugin(str(plugin_dir), enable_after_install=False)

            config = get_config()
            raw = config.setting['plugins3_metadata']
            entry = next(v for v in raw.values() if v.get('url') == str(plugin_dir))
            self.assertNotIn('has_git', entry)
            self.assertEqual(entry.get('ref_type'), 'local')


class TestLocalNonGitPluginCLI(PicardTestCase):
    """Tests for CLI behavior with local non-git plugins."""

    def test_cli_list_info_update_refs(self):
        """CLI shows [local] marker, reloads on update, blocks list-refs."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            manager = _create_manager(plugins_dir)
            manager.install_plugin(str(plugin_dir), enable_after_install=False)

            # list shows [local]
            exit_code, stdout, _ = run_cli(manager, verb='list')
            self.assertEqual(exit_code, 0)
            self.assertIn('[local]', stdout)

            # info shows [local]
            exit_code, stdout, _ = run_cli(manager, verb='info', plugin=plugin_name)
            self.assertEqual(exit_code, 0)
            self.assertIn('[local]', stdout)

            # update shows 'Plugin reloaded'
            exit_code, stdout, _ = run_cli(manager, verb='update', plugin=[plugin_name])
            self.assertEqual(exit_code, 0)
            self.assertIn('Plugin reloaded', stdout)

            # list-refs is blocked
            exit_code, _, stderr = run_cli(manager, verb='refs', plugin=plugin_name)
            self.assertNotEqual(exit_code, 0)
            self.assertIn('not managed by git', stderr)

    def test_cli_list_shows_local_dev_marker(self):
        """CLI --list shows [local-dev] for plugins installed with --no-git."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            (plugin_dir / '.git').mkdir()

            manager = _create_manager(plugins_dir)
            manager.install_plugin(str(plugin_dir), enable_after_install=False, no_git=True)

            exit_code, stdout, _ = run_cli(manager, verb='list')
            self.assertEqual(exit_code, 0)
            self.assertIn('[local-dev]', stdout)

    def test_cli_info_shows_local_dev_marker(self):
        """CLI --info shows [local-dev] for plugins installed with --no-git."""
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as plugins_dir:
            uuid = generate_uuid()
            plugin_dir, plugin_name = _create_plugin_dir(tmp_dir, uuid)
            (plugin_dir / '.git').mkdir()

            manager = _create_manager(plugins_dir)
            manager.install_plugin(str(plugin_dir), enable_after_install=False, no_git=True)

            exit_code, stdout, _ = run_cli(manager, verb='info', plugin=plugin_name)
            self.assertEqual(exit_code, 0)
            self.assertIn('[local-dev]', stdout)

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

from unittest.mock import Mock

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockCliArgs,
    MockPlugin,
    MockPluginManager,
    MockTagger,
    run_cli,
)

from picard.git.backend import GitRef, GitRefType
from picard.plugin3.manager.update import UpdateResult
from picard.plugin3.ref_item import RefItem


class TestPluginInstall(PicardTestCase):
    def test_plugin_metadata_storage(self):
        """Test that plugin metadata is stored and retrieved correctly."""
        from picard.plugin3.manager import PluginManager, PluginMetadata

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        from test.test_plugins3_helpers import generate_unique_uuid

        test_uuid = generate_unique_uuid()

        # Save metadata
        manager._save_plugin_metadata(
            PluginMetadata(
                name='test-plugin',
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc123',
                uuid=test_uuid,
            )
        )

        # Retrieve metadata by UUID
        metadata = manager._get_plugin_metadata(test_uuid)
        self.assertEqual(metadata.name, 'test-plugin')
        self.assertEqual(metadata.url, 'https://example.com/plugin.git')
        self.assertEqual(metadata.ref, 'main')
        self.assertEqual(metadata.commit, 'abc123')

        # Non-existent plugin returns None
        empty_metadata = manager._get_plugin_metadata('nonexistent')
        self.assertIsNone(empty_metadata)

    def test_update_plugin_no_metadata(self):
        """Test that updating plugin without metadata raises error."""
        from picard.plugin3.manager import PluginManager, PluginNoSourceError
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.uuid = 'test-uuid-123'

        # Should raise PluginNoSourceError when no metadata
        with self.assertRaises(PluginNoSourceError) as context:
            manager.update_plugin(mock_plugin)

        self.assertIn('no stored URL', str(context.exception))

    def test_install_with_ref(self):
        """Test installing plugin with specific git ref."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Mock the install to capture ref parameter
        captured_ref = None

        def mock_install(url, ref=None):
            nonlocal captured_ref
            captured_ref = ref

        manager.install_plugin = mock_install

        # Test with ref
        manager.install_plugin('https://example.com/plugin.git', ref='v1.0.0')
        self.assertEqual(captured_ref, 'v1.0.0')

        # Test without ref (should default to None)
        manager.install_plugin('https://example.com/plugin.git')
        self.assertIsNone(captured_ref)

    def test_switch_ref(self):
        """Test switching plugin to different git ref."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        test_uuid = 'test-uuid-5678'

        # Setup plugin with metadata
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')
        mock_plugin.read_manifest = Mock()
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid
        mock_plugin.uuid = test_uuid

        manager._save_plugin_metadata(
            PluginMetadata(
                name='test-plugin',
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc123',
                uuid=test_uuid,
            )
        )

        # Mock GitOperations.switch_ref to return ref changes
        from unittest.mock import patch

        with (
            patch('picard.git.ops.GitOperations.switch_ref') as mock_switch,
            patch.object(manager, 'plugin_ref_switched'),
        ):
            # Create mock GitRef objects (switch_ref still returns GitRef for git operations)
            old_git_ref = GitRef('refs/heads/main', target='abc123', ref_type=GitRefType.BRANCH)
            new_git_ref = GitRef('refs/tags/v1.0.0', target='def456', ref_type=GitRefType.TAG)
            mock_switch.return_value = (old_git_ref, new_git_ref, 'abc123', 'def456')

            old_git_ref_result, new_git_ref_result, old_commit, new_commit = manager.switch_ref(mock_plugin, 'v1.0.0')

            self.assertEqual(old_git_ref_result.shortname, 'main')
            self.assertEqual(new_git_ref_result.shortname, 'v1.0.0')
            self.assertEqual(old_commit, 'abc123')
            self.assertEqual(new_commit, 'def456')

    def test_switch_ref_no_metadata(self):
        """Test switching ref for plugin without metadata raises error."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager, PluginNoSourceError
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')
        mock_plugin.uuid = 'test-uuid-456'

        with self.assertRaises(PluginNoSourceError) as context:
            manager.switch_ref(mock_plugin, 'v1.0.0')

        self.assertIn('no stored URL', str(context.exception))

    def test_switch_ref_cli(self):
        """Test switch-ref CLI command."""
        mock_plugin = MockPlugin()
        mock_manager = MockPluginManager(plugins=[mock_plugin])
        mock_manager.find_plugin = Mock(return_value=mock_plugin)

        # Create mock GitRef objects
        old_git_ref = GitRef('refs/heads/main', ref_type=GitRefType.BRANCH)
        new_git_ref = GitRef('refs/tags/v1.0.0', ref_type=GitRefType.TAG)
        mock_manager.switch_ref = Mock(return_value=(old_git_ref, new_git_ref, 'abc1234', 'def5678'))

        exit_code, stdout, _ = run_cli(mock_manager, switch_ref=['test-plugin', 'v1.0.0'])

        self.assertEqual(exit_code, 0)
        mock_manager.switch_ref.assert_called_once_with(mock_plugin, 'v1.0.0')
        self.assertIn('main', stdout)
        self.assertIn('v1.0.0', stdout)
        self.assertIn('abc1234', stdout)
        self.assertIn('def5678', stdout)

    def test_switch_ref_plugin_not_found(self):
        """Test switch-ref for non-existent plugin."""
        mock_manager = MockPluginManager(plugins=[])
        mock_manager.find_plugin = Mock(return_value=None)
        exit_code, _, stderr = run_cli(mock_manager, switch_ref=['nonexistent', 'v1.0.0'])

        self.assertEqual(exit_code, 2)
        self.assertIn('not found', stderr)

    def test_install_validates_manifest(self):
        """Test that install validates MANIFEST.toml exists."""
        from pathlib import Path
        import tempfile
        from unittest.mock import patch

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Mock PluginSourceGit to create temp dir without MANIFEST
            with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path, **kwargs):
                    path.mkdir(parents=True, exist_ok=True)
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                from picard.plugin3.manager import PluginManifestNotFoundError

                with self.assertRaises(PluginManifestNotFoundError) as context:
                    manager.install_plugin('https://example.com/no-manifest.git')

                self.assertIn('No MANIFEST.toml', str(context.exception))

    def test_install_prevents_duplicate(self):
        """Test that install prevents duplicate installations."""
        from pathlib import Path
        import tempfile
        from unittest.mock import (
            mock_open,
            patch,
        )

        from test.test_plugins3_helpers import generate_unique_uuid

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        test_uuid = generate_unique_uuid()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Create a fake existing plugin directory with UUID-based name
            plugin_dir = manager._primary_plugin_dir / f'test_plugin_{test_uuid}'
            plugin_dir.mkdir(parents=True, exist_ok=True)

            with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path, **kwargs):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test-plugin"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.module_name = 'test-plugin'
                        mock_manifest.name.return_value = 'test-plugin'
                        mock_manifest.uuid = test_uuid
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        from picard.plugin3.manager import PluginAlreadyInstalledError

                        with self.assertRaises(PluginAlreadyInstalledError) as context:
                            manager.install_plugin('https://example.com/plugin.git')

                        self.assertIn('already installed', str(context.exception))

    def test_install_with_reinstall_flag(self):
        """Test that --reinstall allows overwriting existing plugin."""
        from pathlib import Path
        import tempfile
        from unittest.mock import (
            mock_open,
            patch,
        )

        from test.test_plugins3_helpers import generate_unique_uuid

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        test_uuid = generate_unique_uuid()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Create a fake existing plugin directory with UUID-based name
            plugin_dir = manager._primary_plugin_dir / f'test_plugin_{test_uuid}'
            plugin_dir.mkdir(parents=True, exist_ok=True)

            with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path, **kwargs):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test-plugin"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.module_name = 'test-plugin'
                        mock_manifest.name.return_value = 'test-plugin'
                        mock_manifest.uuid = test_uuid
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with patch('shutil.move'):
                            with patch('picard.git.ops.GitOperations.check_dirty_working_dir') as mock_check:
                                mock_check.return_value = []  # No uncommitted changes

                                # Should not raise with reinstall=True
                                plugin_id = manager.install_plugin('https://example.com/plugin.git', reinstall=True)
                            self.assertTrue(plugin_id.startswith('test_plugin_'))

    def test_uninstall_with_purge(self):
        """Test uninstall with purge removes configuration."""
        from pathlib import Path
        from unittest.mock import patch

        from PyQt6.QtCore import QSettings

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create a temporary plugin directory and config file
        import tempfile

        test_uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / 'test-plugin'
            plugin_path.mkdir()

            # Create a real temporary config
            config_file = Path(tmpdir) / 'test_config.ini'
            test_config = QSettings(str(config_file), QSettings.Format.IniFormat)
            test_config.beginGroup(f'plugin.{test_uuid}')
            test_config.setValue('some_setting', 'value1')
            test_config.setValue('another_setting', 'value2')
            test_config.endGroup()
            test_config.sync()

            # Verify settings exist
            test_config.beginGroup(f'plugin.{test_uuid}')
            self.assertEqual(len(test_config.childKeys()), 2)
            test_config.endGroup()

            mock_plugin = MockPlugin(name='test-plugin', uuid=test_uuid, local_path=plugin_path)

            # Set manager's plugin dir to temp dir
            manager._primary_plugin_dir = Path(tmpdir)

            # Mock only the metadata part of config
            test_config.setting = {'plugins3_metadata': {}, 'plugins3_enabled_plugins': []}

            with (
                patch('picard.plugin3.manager.lifecycle.get_config', return_value=test_config),
                patch('picard.plugin3.manager.clean.get_config', return_value=test_config),
            ):
                # Uninstall with purge
                manager.uninstall_plugin(mock_plugin, purge=True)

            # Verify all settings were removed
            test_config.beginGroup(f'plugin.{test_uuid}')
            self.assertEqual(len(test_config.childKeys()), 0)
            test_config.endGroup()

    def test_plugin_has_saved_options(self):
        """Test checking if plugin has saved options."""
        from unittest.mock import Mock, patch

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        test_uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid
        mock_plugin.uuid = test_uuid

        # Mock config with no options
        mock_config_empty = Mock()
        mock_config_empty.childKeys = Mock(return_value=[])
        mock_config_empty.beginGroup = Mock()
        mock_config_empty.endGroup = Mock()

        with patch('picard.plugin3.manager.lifecycle.get_config', return_value=mock_config_empty):
            self.assertFalse(manager.plugin_has_saved_options(mock_plugin))

        # Mock config with options
        mock_config_with_options = Mock()
        mock_config_with_options.childKeys = Mock(return_value=['setting1', 'setting2'])
        mock_config_with_options.beginGroup = Mock()
        mock_config_with_options.endGroup = Mock()

        with patch('picard.plugin3.manager.lifecycle.get_config', return_value=mock_config_with_options):
            self.assertTrue(manager.plugin_has_saved_options(mock_plugin))

        # Test plugin without manifest/UUID
        mock_plugin_no_uuid = Mock(spec=Plugin)
        mock_plugin_no_uuid.manifest = None
        mock_plugin_no_uuid.uuid = None
        self.assertFalse(manager.plugin_has_saved_options(mock_plugin_no_uuid))

    def test_install_command_execution(self):
        """Test install command execution path."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()
        mock_manager.plugins = []
        mock_manager.install_plugin = Mock(return_value='test-plugin')
        mock_manager._find_plugin_by_url = Mock(return_value=None)
        mock_manager._registry = Mock()
        mock_manager._registry.find_plugin = Mock(return_value=None)
        mock_manager._registry.is_blacklisted = Mock(return_value=(False, None))
        mock_manager._registry.get_trust_level = Mock(return_value='unregistered')
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = ['https://example.com/plugin.git']
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None
        args.ref = None
        args.reinstall = False
        args.force_blacklisted = False
        args.yes = True

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.install_plugin.assert_called_once()

    def test_install_command_with_error(self):
        """Test install command handles errors."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()
        mock_manager.plugins = []
        mock_manager.install_plugin = Mock(side_effect=Exception('Install failed'))
        mock_manager._find_plugin_by_url = Mock(return_value=None)
        mock_manager._registry = Mock()
        mock_manager._registry.find_plugin = Mock(return_value=None)
        mock_manager._registry.is_blacklisted = Mock(return_value=(False, None))
        mock_manager._registry.get_trust_level = Mock(return_value='unregistered')
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = ['https://example.com/plugin.git']
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None
        args.ref = None
        args.reinstall = False
        args.force_blacklisted = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 1)
        self.assertIn('failed', stderr.getvalue().lower())

    def test_remove_command_with_yes_flag(self):
        """Test remove command with --yes flag."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.uninstall_plugin = Mock()
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.remove = ['test-plugin']
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None
        args.yes = True
        args.purge = False

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.uninstall_plugin.assert_called_once()

    def test_update_command_execution(self):
        """Test update command execution path."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.find_plugin = Mock(return_value=mock_plugin)
        # Create RefItem objects for UpdateResult
        old_ref_item = RefItem('v1.0.0', RefItem.Type.TAG, 'abc1234')
        new_ref_item = RefItem('v1.1.0', RefItem.Type.TAG, 'def5678')
        mock_manager.update_plugin = Mock(
            return_value=UpdateResult('1.0.0', '1.1.0', 'abc1234', 'def5678', old_ref_item, new_ref_item, 1234567890)
        )
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = ['test-plugin']
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.update_plugin.assert_called_once_with(mock_plugin)

    def test_update_command_already_up_to_date(self):
        """Test update command when already up to date."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        # Same commit = already up to date - use empty RefItems
        empty_ref_item = RefItem('abc1234', RefItem.Type.COMMIT, 'abc1234')
        mock_manager.update_plugin = Mock(
            return_value=UpdateResult(
                '1.0.0', '1.0.0', 'abc1234', 'abc1234', empty_ref_item, empty_ref_item, 1234567890
            )
        )
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = ['test-plugin']
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        self.assertIn('up to date', stdout.getvalue().lower())

    def test_update_all_with_results(self):
        """Test update-all command with mixed results."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.manager.update import UpdateAllResult, UpdateResult
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        # Return mixed results: updated, unchanged, failed
        ref_item1_old = RefItem('abc', RefItem.Type.COMMIT, 'abc')
        ref_item1_new = RefItem('def', RefItem.Type.COMMIT, 'def')
        ref_item2 = RefItem('ghi', RefItem.Type.COMMIT, 'ghi')
        mock_manager.update_all_plugins = Mock(
            return_value=[
                UpdateAllResult(
                    'plugin1',
                    True,
                    UpdateResult('1.0', '1.1', 'abc', 'def', ref_item1_old, ref_item1_new, 1234567890),
                    None,
                ),
                UpdateAllResult(
                    'plugin2', True, UpdateResult('2.0', '2.0', 'ghi', 'ghi', ref_item2, ref_item2, 1234567890), None
                ),
                UpdateAllResult('plugin3', False, None, 'Error'),
            ]
        )
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs()
        args.ref = None
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = True
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger._pluginmanager3, args, output)

        result = cli.run()

        self.assertEqual(result, 1)  # Failed because one plugin failed
        output_text = stdout.getvalue()
        self.assertIn('1 updated', output_text)
        self.assertIn('1 unchanged', output_text)
        self.assertIn('1 failed', output_text)

    def test_install_multiple_plugins_with_ref_requires_confirmation(self):
        """Test that installing multiple plugins with --ref requires confirmation."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = MockTagger()
        mock_manager = MockPluginManager()
        mock_tagger._pluginmanager3 = mock_manager

        args = MockCliArgs(install=['plugin1', 'plugin2'], ref='v1.0.0', yes=False)

        stdout = StringIO()
        stderr = StringIO()
        output = PluginOutput(stdout=stdout, stderr=stderr, color=False)
        # Mock yesno to return False (cancel)
        output.yesno = Mock(return_value=False)
        cli = PluginCLI(mock_manager, args, output)

        result = cli.run()

        self.assertEqual(result, 0)  # Success (cancelled)
        stderr_text = stderr.getvalue()
        self.assertIn('Using ref "v1.0.0" for all 2 plugins', stderr_text)
        stdout_text = stdout.getvalue()
        self.assertIn('Installation cancelled', stdout_text)

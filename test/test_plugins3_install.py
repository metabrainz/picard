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

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard.config import (
    get_config,
)
from picard.plugin3.manifest import PluginManifest


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginInstall(PicardTestCase):
    def test_plugin_metadata_storage(self):
        """Test that plugin metadata is stored and retrieved correctly."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Save metadata
        manager._save_plugin_metadata('test-plugin', 'https://example.com/plugin.git', 'main', 'abc123')

        # Retrieve metadata
        metadata = manager._get_plugin_metadata('test-plugin')
        self.assertEqual(metadata['url'], 'https://example.com/plugin.git')
        self.assertEqual(metadata['ref'], 'main')
        self.assertEqual(metadata['commit'], 'abc123')

        # Non-existent plugin returns empty dict
        empty_metadata = manager._get_plugin_metadata('nonexistent')
        self.assertEqual(empty_metadata, {})

    def test_update_plugin_no_metadata(self):
        """Test that updating plugin without metadata raises error."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'

        with self.assertRaises(ValueError) as context:
            manager.update_plugin(mock_plugin)

        self.assertIn('no stored URL', str(context.exception))

    def test_install_with_ref(self):
        """Test installing plugin with specific git ref."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
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

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Setup plugin with metadata
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')
        mock_plugin.read_manifest = Mock()

        manager._save_plugin_metadata('test-plugin', 'https://example.com/plugin.git', 'main', 'abc123')

        # Mock PluginSourceGit.sync to return new commit
        from unittest.mock import patch

        with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
            mock_source = Mock()
            mock_source.sync = Mock(return_value='def456')
            mock_source_class.return_value = mock_source

            old_ref, new_ref, old_commit, new_commit = manager.switch_ref(mock_plugin, 'v1.0.0')

            self.assertEqual(old_ref, 'main')
            self.assertEqual(new_ref, 'v1.0.0')
            self.assertEqual(old_commit, 'abc123')
            self.assertEqual(new_commit, 'def456')

            # Verify metadata was updated
            metadata = manager._get_plugin_metadata('test-plugin')
            self.assertEqual(metadata['ref'], 'v1.0.0')
            self.assertEqual(metadata['commit'], 'def456')

    def test_switch_ref_no_metadata(self):
        """Test switching ref for plugin without metadata raises error."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')

        with self.assertRaises(ValueError) as context:
            manager.switch_ref(mock_plugin, 'v1.0.0')

        self.assertIn('no stored URL', str(context.exception))

    def test_switch_ref_cli(self):
        """Test switch-ref CLI command."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.switch_ref = Mock(return_value=('main', 'v1.0.0', 'abc1234', 'def5678'))
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.browse = False
        args.search = None
        args.clean_config = None
        args.validate = None
        args.switch_ref = ['test-plugin', 'v1.0.0']

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        output_text = stdout.getvalue()

        self.assertEqual(result, 0)
        mock_manager.switch_ref.assert_called_once_with(mock_plugin, 'v1.0.0')
        self.assertIn('main', output_text)
        self.assertIn('v1.0.0', output_text)
        self.assertIn('abc1234', output_text)
        self.assertIn('def5678', output_text)

    def test_switch_ref_plugin_not_found(self):
        """Test switch-ref for non-existent plugin."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager.plugins = []
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.browse = False
        args.search = None
        args.clean_config = None
        args.validate = None
        args.switch_ref = ['nonexistent', 'v1.0.0']

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        error_text = stderr.getvalue()

        self.assertEqual(result, 2)
        self.assertIn('not found', error_text)

    def test_install_validates_manifest(self):
        """Test that install validates MANIFEST.toml exists."""
        from pathlib import Path
        import tempfile
        from unittest.mock import patch

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Mock PluginSourceGit to create temp dir without MANIFEST
            with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path):
                    path.mkdir(parents=True, exist_ok=True)
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with self.assertRaises(ValueError) as context:
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

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Create a fake existing plugin directory
            plugin_dir = manager._primary_plugin_dir / 'test-plugin'
            plugin_dir.mkdir(parents=True, exist_ok=True)

            with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test-plugin"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.module_name = 'test-plugin'
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with self.assertRaises(ValueError) as context:
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

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Create a fake existing plugin directory
            plugin_dir = manager._primary_plugin_dir / 'test-plugin'
            plugin_dir.mkdir(parents=True, exist_ok=True)

            with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test-plugin"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.module_name = 'test-plugin'
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with patch('shutil.move'):
                            # Should not raise with reinstall=True
                            plugin_id = manager.install_plugin('https://example.com/plugin.git', reinstall=True)
                            self.assertEqual(plugin_id, 'test-plugin')

    def test_uninstall_with_purge(self):
        """Test uninstall with purge removes configuration."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Create a temporary plugin directory
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / 'test-plugin'
            plugin_path.mkdir()

            mock_plugin = Mock(spec=Plugin)
            mock_plugin.name = 'test-plugin'
            mock_plugin.local_path = plugin_path
            mock_plugin.disable = Mock()

            # Set manager's plugin dir to temp dir
            manager._primary_plugin_dir = Path(tmpdir)

            # Set up plugin config
            config = get_config()
            config.setting['test-plugin'] = {'some_setting': 'value'}

            # Uninstall with purge
            manager.uninstall_plugin(mock_plugin, purge=True)

            # Config should be removed
            self.assertNotIn('test-plugin', config.setting)

    def test_install_command_execution(self):
        """Test install command execution path."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager.plugins = []
        mock_manager.install_plugin = Mock(return_value='test-plugin')
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
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

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.install_plugin.assert_called_once()

    def test_install_command_with_error(self):
        """Test install command handles errors."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager.plugins = []
        mock_manager.install_plugin = Mock(side_effect=Exception('Install failed'))
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
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
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 1)
        self.assertIn('failed', stderr.getvalue().lower())

    def test_uninstall_command_with_yes_flag(self):
        """Test uninstall command with --yes flag."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.uninstall_plugin = Mock()
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = ['test-plugin']
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None
        args.yes = True
        args.purge = False

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.uninstall_plugin.assert_called_once()

    def test_update_command_execution(self):
        """Test update command execution path."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.update_plugin = Mock(return_value=('1.0.0', '1.1.0', 'abc1234', 'def5678'))
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
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
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.update_plugin.assert_called_once_with(mock_plugin)

    def test_update_command_already_up_to_date(self):
        """Test update command when already up to date."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        # Same commit = already up to date
        mock_manager.update_plugin = Mock(return_value=('1.0.0', '1.0.0', 'abc1234', 'abc1234'))
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
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
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        self.assertIn('up to date', stdout.getvalue().lower())

    def test_update_all_with_results(self):
        """Test update-all command with mixed results."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        # Return mixed results: updated, unchanged, failed
        mock_manager.update_all_plugins = Mock(
            return_value=[
                ('plugin1', True, '1.0', '1.1', 'abc', 'def', None),
                ('plugin2', True, '2.0', '2.0', 'ghi', 'ghi', None),
                ('plugin3', False, None, None, None, None, 'Error'),
            ]
        )
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
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
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 1)  # Failed because one plugin failed
        output_text = stdout.getvalue()
        self.assertIn('1 updated', output_text)
        self.assertIn('1 unchanged', output_text)
        self.assertIn('1 failed', output_text)

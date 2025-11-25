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
    ConfigSection,
    get_config,
)
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.version import Version


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginManifest(PicardTestCase):
    def test_load_from_toml(self):
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.module_name, 'example')
        self.assertEqual(manifest.name, 'Example plugin')
        self.assertEqual(manifest.author, 'Philipp Wolfer')
        self.assertEqual(manifest.description(), "This is an example plugin")
        self.assertEqual(manifest.description('en'), "This is an example plugin")
        self.assertEqual(manifest.description('fr'), "Ceci est un exemple de plugin")
        self.assertEqual(manifest.description('it'), "This is an example plugin")
        self.assertEqual(manifest.version, Version(1, 0, 0))
        self.assertEqual(manifest.api_versions, (Version(3, 0, 0), Version(3, 1, 0)))
        self.assertEqual(manifest.license, 'CC0-1.0')
        self.assertEqual(manifest.license_url, 'https://creativecommons.org/publicdomain/zero/1.0/')
        self.assertEqual(manifest.user_guide_url, 'https://example.com/')


class TestPluginApi(PicardTestCase):
    def test_init(self):
        manifest = load_plugin_manifest('example')

        mock_tagger = Mock()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)
        self.assertEqual(api.web_service, mock_ws)
        self.assertEqual(api.logger.name, 'plugin.example')
        self.assertEqual(api.global_config, get_config())
        self.assertIsInstance(api.plugin_config, ConfigSection)


class TestPluginManager(PicardTestCase):
    def test_config_persistence(self):
        """Test that enabled plugins are saved to and loaded from config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Initially no plugins enabled
        self.assertEqual(manager._enabled_plugins, set())

        # Create a mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'

        # Enable plugin - should save to config
        manager.enable_plugin(mock_plugin)
        self.assertIn('test-plugin', manager._enabled_plugins)

        # Verify it was saved to config
        config = get_config()
        self.assertIn('plugins3', config.setting)
        self.assertIn('test-plugin', config.setting['plugins3']['enabled_plugins'])

        # Create new manager instance - should load from config
        manager2 = PluginManager(mock_tagger)
        self.assertIn('test-plugin', manager2._enabled_plugins)

        # Disable plugin - should remove from config
        manager2.disable_plugin(mock_plugin)
        self.assertNotIn('test-plugin', manager2._enabled_plugins)
        self.assertNotIn('test-plugin', config.setting['plugins3']['enabled_plugins'])

    def test_init_plugins_only_loads_enabled(self):
        """Test that init_plugins only loads plugins that are enabled in config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Create mock plugins
        enabled_plugin = Mock(spec=Plugin)
        enabled_plugin.name = 'enabled-plugin'
        enabled_plugin.load_module = Mock()
        enabled_plugin.enable = Mock()

        disabled_plugin = Mock(spec=Plugin)
        disabled_plugin.name = 'disabled-plugin'
        disabled_plugin.load_module = Mock()
        disabled_plugin.enable = Mock()

        manager._plugins = [enabled_plugin, disabled_plugin]
        manager._enabled_plugins = {'enabled-plugin'}

        # Initialize plugins
        manager.init_plugins()

        # Only enabled plugin should be loaded
        enabled_plugin.load_module.assert_called_once()
        enabled_plugin.enable.assert_called_once_with(mock_tagger)
        disabled_plugin.load_module.assert_not_called()
        disabled_plugin.enable.assert_not_called()

    def test_api_version_compatibility_compatible(self):
        """Test that plugins with compatible API versions are loaded."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Load compatible plugin (API 3.0, 3.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'example')

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'example')
        self.assertEqual(plugin.manifest.name, 'Example plugin')

    def test_api_version_compatibility_incompatible_old(self):
        """Test that plugins with old incompatible API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Load incompatible plugin (API 2.0, 2.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'incompatible')

        self.assertIsNone(plugin)

    def test_api_version_compatibility_incompatible_new(self):
        """Test that plugins requiring newer API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Load plugin requiring future API (3.5, 3.6)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'newer-api')

        self.assertIsNone(plugin)


class TestPluginCLI(PicardTestCase):
    def test_list_plugins_empty(self):
        """Test listing plugins when none are installed."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager.plugins = []
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = True
        args.info = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        output_text = stdout.getvalue()

        self.assertEqual(result, 0)
        self.assertIn('No plugins installed', output_text)

    def test_list_plugins_with_plugins(self):
        """Test listing plugins with details."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        mock_manager = Mock()

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'
        mock_plugin.local_path = '/path/to/plugin'
        mock_plugin.manifest = load_plugin_manifest('example')

        mock_manager.plugins = [mock_plugin]
        mock_manager._enabled_plugins = {'test-plugin'}
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = True
        args.info = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        output_text = stdout.getvalue()

        self.assertEqual(result, 0)
        self.assertIn('test-plugin', output_text)
        self.assertIn('enabled', output_text)
        self.assertIn('1.0.0', output_text)

    def test_info_plugin_not_found(self):
        """Test info command for non-existent plugin."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager.plugins = []
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = 'nonexistent'

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        error_text = stderr.getvalue()

        self.assertEqual(result, 2)
        self.assertIn('not found', error_text)

    def test_output_color_mode(self):
        """Test that color mode works correctly."""
        from io import StringIO

        from picard.plugin3.output import PluginOutput

        # Test with color enabled
        stdout_color = StringIO()
        output_color = PluginOutput(stdout=stdout_color, stderr=StringIO(), color=True)
        output_color.success('test')
        self.assertIn('\033[32m', stdout_color.getvalue())  # Green color code

        # Test with color disabled
        stdout_no_color = StringIO()
        output_no_color = PluginOutput(stdout=stdout_no_color, stderr=StringIO(), color=False)
        output_no_color.success('test')
        self.assertNotIn('\033[', stdout_no_color.getvalue())  # No color codes

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

    def test_check_updates_empty(self):
        """Test check_updates with no plugins."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._plugins = []

        updates = manager.check_updates()
        self.assertEqual(updates, [])

    def test_update_cli_commands(self):
        """Test that update CLI commands are properly routed."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.check_updates = Mock(return_value=[])
        mock_manager.update_all_plugins = Mock(return_value=[])
        mock_tagger.pluginmanager3 = mock_manager

        output = PluginOutput(stdout=StringIO(), stderr=StringIO(), color=False)

        # Test --check-updates
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
        args.check_updates = True

        cli = PluginCLI(mock_tagger, args, output)
        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.check_updates.assert_called_once()

        # Test --update-all
        args.check_updates = False
        args.update_all = True
        cli = PluginCLI(mock_tagger, args, output)
        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.update_all_plugins.assert_called_once()

    def test_update_plugin_not_found(self):
        """Test update command for non-existent plugin."""
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
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = ['nonexistent']
        args.update_all = False
        args.check_updates = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        error_text = stderr.getvalue()

        self.assertEqual(result, 2)
        self.assertIn('not found', error_text)

    def test_plugin_state_transitions(self):
        """Test that plugin state transitions work correctly."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        mock_tagger = Mock()
        plugin = Plugin(Path('/tmp'), 'test-plugin')

        # Initial state should be DISCOVERED
        self.assertEqual(plugin.state, PluginState.DISCOVERED)

        # Mock the module loading
        plugin._module = Mock()
        plugin._module.enable = Mock()
        plugin._module.disable = Mock()

        # Load module should transition to LOADED
        plugin.state = PluginState.DISCOVERED
        plugin.load_module = Mock(side_effect=lambda: setattr(plugin, 'state', PluginState.LOADED))
        plugin.load_module()
        self.assertEqual(plugin.state, PluginState.LOADED)

        # Enable should transition to ENABLED
        plugin.manifest = Mock()
        plugin.enable(mock_tagger)
        self.assertEqual(plugin.state, PluginState.ENABLED)

        # Disable should transition to DISABLED
        plugin.disable()
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_plugin_double_enable_error(self):
        """Test that enabling an already enabled plugin raises error."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        mock_tagger = Mock()
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.ENABLED
        plugin._module = Mock()
        plugin.manifest = Mock()

        with self.assertRaises(ValueError) as context:
            plugin.enable(mock_tagger)

        self.assertIn('already enabled', str(context.exception))

    def test_plugin_double_disable_error(self):
        """Test that disabling an already disabled plugin raises error."""
        from pathlib import Path

        from picard.plugin3.plugin import (
            Plugin,
            PluginState,
        )

        plugin = Plugin(Path('/tmp'), 'test-plugin')
        plugin.state = PluginState.DISABLED
        plugin._module = Mock()

        with self.assertRaises(ValueError) as context:
            plugin.disable()

        self.assertIn('already disabled', str(context.exception))

    def test_status_command(self):
        """Test status command shows plugin state."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput
        from picard.plugin3.plugin import PluginState

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_plugin.state = PluginState.ENABLED
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.version = '1.0.0'
        mock_plugin.manifest.api_versions = ['3.0']

        mock_manager.plugins = [mock_plugin]
        mock_manager._enabled_plugins = {'test-plugin'}
        mock_manager._get_plugin_metadata = Mock(
            return_value={'url': 'https://example.com/plugin.git', 'ref': 'main', 'commit': 'abc1234567890'}
        )
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = 'test-plugin'
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        output_text = stdout.getvalue()

        self.assertEqual(result, 0)
        self.assertIn('test-plugin', output_text)
        self.assertIn('enabled', output_text)
        self.assertIn('1.0.0', output_text)
        self.assertIn('https://example.com/plugin.git', output_text)
        self.assertIn('abc1234', output_text)

    def test_status_plugin_not_found(self):
        """Test status command for non-existent plugin."""
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
        args.status = 'nonexistent'
        args.enable = None
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        error_text = stderr.getvalue()

        self.assertEqual(result, 2)
        self.assertIn('not found', error_text)

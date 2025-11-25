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

from picard.plugin3.manifest import PluginManifest


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


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

    def test_check_updates_empty(self):
        """Test check_updates with no plugins."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._plugins = []

        updates = manager.check_updates()
        self.assertEqual(updates, [])

    def test_clean_config_command(self):
        """Test --clean-config command."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_manager._clean_plugin_config = Mock()
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
        args.switch_ref = None
        args.clean_config = 'test-plugin'
        args.yes = True

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()
        output_text = stdout.getvalue()

        self.assertEqual(result, 0)
        mock_manager._clean_plugin_config.assert_called_once_with('test-plugin')
        self.assertIn('deleted', output_text.lower())

    def test_enable_plugins_command(self):
        """Test enable command."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.enable_plugin = Mock()
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = None
        args.enable = ['test-plugin']
        args.disable = None
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.enable_plugin.assert_called_once_with(mock_plugin)

    def test_disable_plugins_command(self):
        """Test disable command."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.disable_plugin = Mock()
        mock_tagger.pluginmanager3 = mock_manager

        args = Mock()
        args.list = False
        args.info = None
        args.status = None
        args.enable = None
        args.disable = ['test-plugin']
        args.install = None
        args.uninstall = None
        args.update = None
        args.update_all = False
        args.check_updates = False
        args.switch_ref = None
        args.clean_config = None

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 0)
        mock_manager.disable_plugin.assert_called_once_with(mock_plugin)

    def test_cli_keyboard_interrupt(self):
        """Test CLI handles KeyboardInterrupt."""
        from io import StringIO

        from picard.plugin3.cli import PluginCLI
        from picard.plugin3.output import PluginOutput

        mock_tagger = Mock()
        mock_manager = Mock()
        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        mock_manager.plugins = [mock_plugin]
        mock_manager.check_updates = Mock(side_effect=KeyboardInterrupt())
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
        args.check_updates = True
        args.switch_ref = None
        args.clean_config = None

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(mock_tagger, args, output)

        result = cli.run()

        self.assertEqual(result, 130)  # CANCELLED
        self.assertIn('cancelled', stderr.getvalue().lower())

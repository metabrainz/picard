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

from unittest.mock import Mock, PropertyMock

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockPlugin,
    MockPluginManager,
    load_plugin_manifest,
    run_cli,
)

from picard.git.factory import has_git_backend
from picard.plugin3.manager.update import UpdateResult
from picard.plugin3.ref_item import RefItem


def create_mock_registry_plugin(data):
    """Create a mock RegistryPlugin object from dict data."""
    mock_plugin = Mock()
    mock_plugin.id = data.get('id', '')
    mock_plugin.name = data.get('name', '')
    mock_plugin.description = data.get('description', '')  # Add description as string
    mock_plugin.git_url = data.get('git_url', '')
    mock_plugin.trust_level = data.get('trust_level', 'community')
    mock_plugin.categories = data.get('categories', [])
    mock_plugin.versioning_scheme = data.get('versioning_scheme')
    mock_plugin.refs = data.get('refs', [])

    # Add i18n methods that return the base values
    mock_plugin.name_i18n = Mock(return_value=data.get('name', ''))
    mock_plugin.description_i18n = Mock(return_value=data.get('description', ''))

    # Add _data for backward compatibility with helper functions
    mock_plugin._data = data

    return mock_plugin


class TestPluginCLI(PicardTestCase):
    def test_list_plugins_empty(self):
        """Test listing plugins when none are installed."""
        mock_manager = MockPluginManager(plugins=[])
        exit_code, stdout, _ = run_cli(mock_manager, list=True)

        self.assertEqual(exit_code, 0)
        self.assertIn('No plugins installed', stdout)

    def test_list_plugins_with_plugins(self):
        """Test listing plugins with details."""
        from test.test_plugins3_helpers import generate_unique_uuid

        test_uuid = generate_unique_uuid()
        manifest = load_plugin_manifest('example')
        type(manifest).uuid = PropertyMock(return_value=test_uuid)

        mock_plugin = MockPlugin(name='test-plugin', uuid=test_uuid, manifest=manifest)
        mock_manager = MockPluginManager(plugins=[mock_plugin], _enabled_plugins={test_uuid})
        mock_manager._get_plugin_metadata = Mock(return_value={})

        exit_code, stdout, _ = run_cli(mock_manager, list=True)

        self.assertEqual(exit_code, 0)
        self.assertIn('Example plugin', stdout)
        self.assertIn('enabled', stdout)
        self.assertIn('1.0.0', stdout)

    def test_list_plugins_sorted_by_name(self):
        """Test that plugins are listed in alphabetical order."""
        plugin1 = MockPlugin(name='zebra-plugin', uuid='uuid-1')
        plugin1.manifest.name = Mock(return_value='Zebra Plugin')

        plugin2 = MockPlugin(name='alpha-plugin', uuid='uuid-2')
        plugin2.manifest.name = Mock(return_value='Alpha Plugin')

        plugin3 = MockPlugin(name='middle-plugin', uuid='uuid-3')
        plugin3.manifest.name = Mock(return_value='Middle Plugin')

        mock_manager = MockPluginManager(plugins=[plugin1, plugin2, plugin3])
        mock_manager._get_plugin_metadata = Mock(return_value={})

        exit_code, stdout, _ = run_cli(mock_manager, list=True)

        self.assertEqual(exit_code, 0)
        # Check that plugins appear in alphabetical order
        alpha_pos = stdout.find('Alpha Plugin')
        middle_pos = stdout.find('Middle Plugin')
        zebra_pos = stdout.find('Zebra Plugin')

        self.assertLess(alpha_pos, middle_pos)
        self.assertLess(middle_pos, zebra_pos)

    def test_info_plugin_not_found(self):
        """Test info command for non-existent plugin."""
        mock_manager = MockPluginManager(plugins=[])
        mock_manager.find_plugin = Mock(return_value=None)
        exit_code, _, stderr = run_cli(mock_manager, info='nonexistent')

        self.assertEqual(exit_code, 2)
        self.assertIn('not found', stderr)

    def test_find_plugin_by_prefix(self):
        """Test finding plugin by Plugin ID prefix."""
        from test.test_plugins3_helpers import generate_unique_uuid

        # Create plugin with full Plugin ID
        test_uuid = generate_unique_uuid()
        mock_plugin = MockPlugin(name=f'example_plugin_{test_uuid}', display_name='Example Plugin')
        mock_manager = MockPluginManager(plugins=[mock_plugin])

        # Mock find_plugin to return the plugin for this test
        mock_manager.find_plugin = Mock(return_value=mock_plugin)

        result = mock_manager.find_plugin('example_plugin')

        self.assertEqual(result, mock_plugin)

    def test_validate_git_url(self):
        """Test validate command with git URL."""
        import tempfile

        if not has_git_backend():
            self.skipTest("git backend not available")

        # Create a temporary git repository
        with tempfile.TemporaryDirectory() as tmpdir:
            from test.test_plugins3_helpers import (
                create_mock_manager_with_manifest_validation,
                create_test_manifest_content,
                create_test_plugin_dir,
            )

            manifest_content = create_test_manifest_content(
                name='Test Plugin',
                authors=['Test'],
                description='Test',
                uuid='3fa397ec-0f2a-47dd-9223-e47ce9f2d692',
            )

            plugin_dir = create_test_plugin_dir(tmpdir, 'test-plugin', manifest_content, add_git=True)

            mock_manager = create_mock_manager_with_manifest_validation()
            exit_code, stdout, stderr = run_cli(mock_manager, validate=str(plugin_dir))

            if exit_code != 0:
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
            self.assertEqual(exit_code, 0)
            self.assertIn('Validation passed', stdout)
            self.assertIn('Test Plugin', stdout)

    def test_output_color_mode(self):
        """Test that color mode works correctly."""
        from io import StringIO

        from picard.plugin3.output import PluginOutput

        # Test with color enabled
        stdout_color = StringIO()
        output_color = PluginOutput(stdout=stdout_color, stderr=StringIO(), color=True)
        output_color.success('test')
        self.assertIn('\033[32m', stdout_color.getvalue())

        # Test with color disabled
        stdout_no_color = StringIO()
        output_no_color = PluginOutput(stdout=stdout_no_color, stderr=StringIO(), color=False)
        output_no_color.success('test')
        self.assertNotIn('\033[', stdout_no_color.getvalue())

    def test_update_cli_commands(self):
        """Test that update CLI commands are properly routed."""
        mock_plugin = MockPlugin()
        mock_manager = MockPluginManager(plugins=[mock_plugin])
        mock_manager.check_updates = Mock(return_value={})
        mock_manager.update_all_plugins = Mock(return_value=[])

        # Test --check-updates
        exit_code, _, _ = run_cli(mock_manager, check_updates=True)
        self.assertEqual(exit_code, 0)
        mock_manager.check_updates.assert_called_once()

        # Test --update-all
        exit_code, _, _ = run_cli(mock_manager, update_all=True)
        self.assertEqual(exit_code, 0)
        mock_manager.update_all_plugins.assert_called_once()

    def test_update_plugin_not_found(self):
        """Test update command for non-existent plugin."""
        mock_manager = MockPluginManager(plugins=[])
        mock_manager.find_plugin = Mock(return_value=None)
        exit_code, _, stderr = run_cli(mock_manager, update=['nonexistent'])

        self.assertEqual(exit_code, 2)
        self.assertIn('not found', stderr)

    def test_update_plugin_with_version_object(self):
        """Test update command properly handles Version objects."""

        manifest = load_plugin_manifest('example')
        mock_plugin = MockPlugin(manifest=manifest)
        mock_manager = MockPluginManager(plugins=[mock_plugin])

        # Simulate update_plugin returning Version objects (the bug scenario)
        mock_manager.update_plugin = Mock(
            return_value=UpdateResult(
                old_version='1.0.0',
                new_version='1.1.0',
                old_commit='abc1234567890',
                new_commit='def9876543210',
                old_ref_item=RefItem('v1.0.0', RefItem.Type.TAG, 'abc1234567890'),
                new_ref_item=RefItem('v1.1.0', RefItem.Type.TAG, 'def9876543210'),
                commit_date=1234567890,
            )
        )

        exit_code, stdout, _ = run_cli(mock_manager, update=['test-plugin'])

        self.assertEqual(exit_code, 0)
        self.assertIn('1.0.0', stdout)
        self.assertIn('1.1.0', stdout)
        mock_manager.update_plugin.assert_called_once()

    def test_check_updates_empty(self):
        """Test check_updates with no plugins."""
        from picard.plugin3.manager import PluginManager

        manager = PluginManager(Mock())
        manager._plugins = []

        updates = manager.check_updates()
        self.assertEqual(updates, {})

    def test_clean_config_command(self):
        """Test --clean-config command."""
        from pathlib import Path
        import tempfile
        from unittest.mock import patch

        from PyQt6.QtCore import QSettings

        from picard.plugin3.manager import PluginManager

        test_uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

        # Create a real temporary config
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / 'test_config.ini'
            test_config = QSettings(str(config_file), QSettings.Format.IniFormat)
            test_config.beginGroup(f'plugin.{test_uuid}')
            test_config.setValue('setting1', 'value1')
            test_config.setValue('setting2', 'value2')
            test_config.endGroup()
            test_config.sync()

            # Verify settings exist
            test_config.beginGroup(f'plugin.{test_uuid}')
            self.assertEqual(len(test_config.childKeys()), 2)
            test_config.endGroup()

            mock_manager = PluginManager(Mock())
            with (
                patch('picard.plugin3.manager.lifecycle.get_config', return_value=test_config),
                patch('picard.plugin3.manager.clean.get_config', return_value=test_config),
                patch('picard.plugin3.cli.get_config', return_value=test_config),
            ):
                exit_code, stdout, _ = run_cli(mock_manager, clean_config=test_uuid, yes=True)

            self.assertEqual(exit_code, 0)
            self.assertIn('deleted', stdout.lower())

            # Verify settings were removed
            test_config.beginGroup(f'plugin.{test_uuid}')
            self.assertEqual(len(test_config.childKeys()), 0)
            test_config.endGroup()

    def test_enable_plugins_command(self):
        """Test enable command."""
        mock_plugin = MockPlugin()
        mock_manager = MockPluginManager(plugins=[mock_plugin], enable_plugin=Mock())
        mock_manager.find_plugin = Mock(return_value=mock_plugin)

        exit_code, _, _ = run_cli(mock_manager, enable=['test-plugin'])

        self.assertEqual(exit_code, 0)
        mock_manager.enable_plugin.assert_called_once_with(mock_plugin)

    def test_disable_plugins_command(self):
        """Test disable command."""
        mock_plugin = MockPlugin()
        mock_manager = MockPluginManager(plugins=[mock_plugin], disable_plugin=Mock())
        mock_manager.find_plugin = Mock(return_value=mock_plugin)

        exit_code, _, _ = run_cli(mock_manager, disable=['test-plugin'])

        self.assertEqual(exit_code, 0)
        mock_manager.disable_plugin.assert_called_once_with(mock_plugin)

    def test_cli_keyboard_interrupt(self):
        """Test CLI handles KeyboardInterrupt."""
        mock_plugin = MockPlugin()
        mock_manager = MockPluginManager(plugins=[mock_plugin])
        mock_manager.check_updates = Mock(side_effect=KeyboardInterrupt())

        exit_code, _, stderr = run_cli(mock_manager, check_updates=True)

        self.assertEqual(exit_code, 130)
        self.assertIn('cancelled', stderr.lower())

    def test_browse_plugins_command(self):
        """Test --browse command."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = [
            create_mock_registry_plugin(
                {
                    'id': 'plugin1',
                    'name': 'Plugin 1',
                    'description': 'Test plugin 1',
                    'trust_level': 'official',
                    'categories': ['metadata'],
                }
            ),
            create_mock_registry_plugin(
                {
                    'id': 'plugin2',
                    'name': 'Plugin 2',
                    'description': 'Test plugin 2',
                    'trust_level': 'trusted',
                    'categories': ['coverart'],
                }
            ),
        ]

        exit_code, _, _ = run_cli(mock_manager, browse=True)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.list_plugins.assert_called_once_with(category=None, trust_level=None)

    def test_browse_plugins_with_filters(self):
        """Test --browse with category and trust filters."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = [
            create_mock_registry_plugin(
                {
                    'id': 'plugin1',
                    'name': 'Plugin 1',
                    'description': 'Test',
                    'trust_level': 'official',
                    'categories': ['metadata'],
                }
            ),
        ]

        exit_code, _, _ = run_cli(mock_manager, browse=True, category='metadata', trust='official')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.list_plugins.assert_called_once_with(category='metadata', trust_level='official')

    def test_search_plugins_command(self):
        """Test --search command."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = [
            create_mock_registry_plugin(
                {
                    'id': 'listenbrainz',
                    'name': 'ListenBrainz',
                    'description': 'Submit to ListenBrainz',
                    'trust_level': 'official',
                }
            ),
            create_mock_registry_plugin(
                {'id': 'discogs', 'name': 'Discogs', 'description': 'Discogs metadata', 'trust_level': 'trusted'}
            ),
        ]

        exit_code, _, _ = run_cli(mock_manager, search='listen')

        self.assertEqual(exit_code, ExitCode.SUCCESS)

    def test_install_by_plugin_id(self):
        """Test installing plugin by ID from registry."""
        from unittest.mock import Mock

        from picard.plugin3.cli import ExitCode

        mock_plugin = Mock()
        mock_plugin.id = 'test-plugin'
        mock_plugin.name = 'Test Plugin'
        mock_plugin.git_url = 'https://github.com/test/plugin'
        mock_plugin.versioning_scheme = None  # No versioning scheme
        mock_plugin.refs = []  # No explicit refs

        mock_manager = MockPluginManager()
        mock_manager._registry.find_plugin.return_value = mock_plugin
        mock_manager._find_plugin_by_url.return_value = None  # Not already installed
        mock_manager.install_plugin.return_value = 'test-plugin'

        exit_code, _, _ = run_cli(mock_manager, install=['test-plugin'])

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.find_plugin.assert_called_once_with(plugin_id='test-plugin')
        mock_manager.install_plugin.assert_called_once()

    def test_check_blacklist_not_blacklisted(self):
        """Test --check-blacklist with non-blacklisted URL."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (False, None)

        exit_code, stdout, _ = run_cli(mock_manager, check_blacklist='https://github.com/test/plugin')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('not blacklisted', stdout)
        mock_manager._registry.is_blacklisted.assert_called_once_with('https://github.com/test/plugin', None)

    def test_check_blacklist_is_blacklisted(self):
        """Test --check-blacklist with blacklisted URL."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (True, 'Security vulnerability')

        exit_code, stdout, stderr = run_cli(mock_manager, check_blacklist='https://github.com/bad/plugin')

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('blacklisted', stderr)
        self.assertIn('Security vulnerability', stderr)

    def test_search_with_category_filter(self):
        """Test --search with --category filter."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = [
            create_mock_registry_plugin(
                {
                    'id': 'metadata-plugin',
                    'name': 'Metadata Plugin',
                    'description': 'Test metadata',
                    'trust_level': 'official',
                    'categories': ['metadata'],
                }
            ),
        ]

        exit_code, _, _ = run_cli(mock_manager, search='test', category='metadata')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.list_plugins.assert_called_once_with(category='metadata', trust_level=None)

    def test_search_with_trust_filter(self):
        """Test --search with --trust filter."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = []

        exit_code, _, _ = run_cli(mock_manager, search='test', trust='official')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.list_plugins.assert_called_once_with(category=None, trust_level='official')

    def test_refresh_registry_command(self):
        """Test --refresh-registry command."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager.refresh_registry_and_caches = Mock()
        mock_manager._registry.get_registry_info.return_value = {
            'plugin_count': 42,
            'api_version': '3.0',
            'registry_url': 'https://test.example.com/registry.toml',
        }

        exit_code, stdout, _ = run_cli(mock_manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager.refresh_registry_and_caches.assert_called_once()
        mock_manager._registry.get_registry_info.assert_called_once()
        self.assertIn('Registry refreshed successfully', stdout)
        self.assertIn('Plugins available: 42', stdout)

    def test_refresh_registry_error(self):
        """Test --refresh-registry command with error."""
        from picard.plugin3.cli import ExitCode

        mock_manager = MockPluginManager()
        mock_manager.refresh_registry_and_caches.side_effect = Exception('Network error')

        exit_code, _, stderr = run_cli(mock_manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to refresh registry', stderr)
        self.assertIn('Network error', stderr)

    def test_refresh_registry_fetch_error(self):
        """Test --refresh-registry with RegistryFetchError."""
        from picard.plugin3.cli import ExitCode
        from picard.plugin3.registry import RegistryFetchError

        mock_manager = MockPluginManager()
        mock_manager.refresh_registry_and_caches.side_effect = RegistryFetchError(
            'https://test.example.com/registry.toml', Exception('Connection timeout')
        )

        exit_code, _, stderr = run_cli(mock_manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to fetch registry', stderr)
        self.assertIn('https://test.example.com/registry.toml', stderr)
        self.assertIn('Connection timeout', stderr)

    def test_refresh_registry_parse_error(self):
        """Test --refresh-registry with RegistryParseError."""
        from picard.plugin3.cli import ExitCode
        from picard.plugin3.registry import RegistryParseError

        mock_manager = MockPluginManager()
        mock_manager.refresh_registry_and_caches.side_effect = RegistryParseError(
            'https://test.example.com/registry.toml', Exception('Invalid JSON')
        )

        exit_code, _, stderr = run_cli(mock_manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to parse registry', stderr)
        self.assertIn('https://test.example.com/registry.toml', stderr)
        self.assertIn('Invalid JSON', stderr)

    def test_update_commit_pinned_plugin(self):
        """Test update command shows warning for commit-pinned plugins."""
        from unittest.mock import PropertyMock

        from test.test_plugins3_helpers import generate_unique_uuid

        from picard.plugin3.manager import PluginCommitPinnedError

        test_uuid = generate_unique_uuid()
        manifest = load_plugin_manifest('example')
        type(manifest).uuid = PropertyMock(return_value=test_uuid)

        mock_plugin = MockPlugin(name='test-plugin', uuid=test_uuid, manifest=manifest)
        mock_manager = MockPluginManager(plugins=[mock_plugin])

        # Mock update_plugin to raise PluginCommitPinnedError
        mock_manager.update_plugin.side_effect = PluginCommitPinnedError('test-plugin', 'abc1234')

        exit_code, stdout, stderr = run_cli(mock_manager, update=['test-plugin'])

        self.assertEqual(exit_code, 0)
        self.assertIn('pinned to commit', stderr)
        self.assertIn('switch-ref', stdout)
        # Should have called update_plugin (which raised the exception)
        mock_manager.update_plugin.assert_called_once()

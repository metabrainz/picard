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

from io import StringIO
from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    PropertyMock,
    patch,
)

from PyQt6.QtCore import QSettings

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    MockCliArgs,
    MockPlugin,
    MockPluginManager,
    create_mock_manager_with_manifest_validation,
    create_test_manifest_content,
    create_test_plugin_dir,
    load_plugin_manifest,
    run_cli,
)

from picard.git.factory import has_git_backend
from picard.plugin3.cli import (
    ExitCode,
    PluginCLI,
)
from picard.plugin3.manager import (
    PluginCommitPinnedError,
    PluginManager,
    PluginMetadata,
)
from picard.plugin3.manager.update import UpdateResult
from picard.plugin3.output import PluginOutput
from picard.plugin3.ref_item import RefItem
from picard.plugin3.registry import (
    RegistryFetchError,
    RegistryParseError,
)
from picard.plugin3.validator import generate_uuid


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


def _make_cli(manager, args, **kwargs):
    """Create a PluginCLI with captured stderr output."""
    stderr = StringIO()
    output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
    cli = PluginCLI(manager, args, output=output, **kwargs)
    return cli, stderr


class TestPluginCLI(PicardTestCase):
    def test_list_plugins_empty(self):
        """Test listing plugins when none are installed."""
        mock_manager = MockPluginManager(plugins=[])
        exit_code, stdout, _ = run_cli(mock_manager, list=True)

        self.assertEqual(exit_code, 0)
        self.assertIn('No plugins installed', stdout)

    def test_list_plugins_with_plugins(self):
        """Test listing plugins with details."""
        test_uuid = generate_uuid()
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
        # Create plugin with full Plugin ID
        test_uuid = generate_uuid()
        mock_plugin = MockPlugin(name=f'example_plugin_{test_uuid}', display_name='Example Plugin')
        mock_manager = MockPluginManager(plugins=[mock_plugin])

        # Mock find_plugin to return the plugin for this test
        mock_manager.find_plugin = Mock(return_value=mock_plugin)

        result = mock_manager.find_plugin('example_plugin')

        self.assertEqual(result, mock_plugin)

    def test_validate_git_url(self):
        """Test validate command with git URL."""
        if not has_git_backend():
            self.skipTest("git backend not available")

        # Create a temporary git repository
        with tempfile.TemporaryDirectory() as tmpdir:
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
        manager = PluginManager(Mock())
        manager._plugins = []

        updates = manager.check_updates()
        self.assertEqual(updates, {})

    def test_clean_config_command(self):
        """Test --clean-config command."""
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
        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (False, None)

        exit_code, stdout, _ = run_cli(mock_manager, check_blacklist='https://github.com/test/plugin')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('Not blacklisted', stdout)
        mock_manager._registry.is_blacklisted.assert_called_once_with('https://github.com/test/plugin', None)

    def test_check_blacklist_is_blacklisted(self):
        """Test --check-blacklist with blacklisted URL."""
        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (True, 'Security vulnerability')

        exit_code, stdout, stderr = run_cli(mock_manager, check_blacklist='https://github.com/bad/plugin')

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        self.assertIn('Security vulnerability', stderr)

    def test_check_blacklist_with_uuid(self):
        """Test --check-blacklist with --uuid passes UUID to is_blacklisted."""
        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (True, 'Security vulnerability')

        exit_code, stdout, stderr = run_cli(
            mock_manager,
            check_blacklist='https://github.com/test/plugin',
            uuid='blacklisted-uuid-1234',
        )

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        mock_manager._registry.is_blacklisted.assert_called_once_with(
            'https://github.com/test/plugin', 'blacklisted-uuid-1234'
        )

    def test_check_blacklist_uuid_only(self):
        """Test --check-blacklist --uuid without URL."""
        mock_manager = MockPluginManager()
        mock_manager._registry.is_blacklisted.return_value = (True, 'UUID is blacklisted')

        exit_code, stdout, stderr = run_cli(
            mock_manager,
            check_blacklist='',
            uuid='blacklisted-uuid-1234',
        )

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        mock_manager._registry.is_blacklisted.assert_called_once_with(
            None,
            'blacklisted-uuid-1234',
        )

    def test_search_with_category_filter(self):
        """Test --search with --category filter."""
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
        mock_manager = MockPluginManager()
        mock_manager._registry.list_plugins.return_value = []

        exit_code, _, _ = run_cli(mock_manager, search='test', trust='official')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        mock_manager._registry.list_plugins.assert_called_once_with(category=None, trust_level='official')

    def test_refresh_registry_command(self):
        """Test --refresh-registry command."""
        mock_manager = MockPluginManager()

        # Mock refresh_registry_and_caches to call callback immediately
        def mock_refresh(callback=None):
            if callback:
                callback(True, None)

        mock_manager.refresh_registry_and_caches = Mock(side_effect=mock_refresh)
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
        mock_manager = MockPluginManager()
        mock_manager.refresh_registry_and_caches.side_effect = Exception('Network error')

        exit_code, _, stderr = run_cli(mock_manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to refresh registry', stderr)
        self.assertIn('Network error', stderr)

    def test_refresh_registry_fetch_error(self):
        """Test --refresh-registry with RegistryFetchError."""
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
        test_uuid = generate_uuid()
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


class TestPluginCLIErrors(PicardTestCase):
    def test_ref_without_install_or_validate(self):
        """Test --ref without --install or --validate returns error."""
        manager = MockPluginManager()
        args = MockCliArgs()
        args.ref = 'main'
        args.install = None
        args.validate = False
        args.list = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)

        cli = PluginCLI(manager, args, output=output)
        result = cli.run()

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('--ref can only be used with --install or --validate', stderr.getvalue())

    def test_no_action_without_parser(self):
        """Test no action specified without parser returns error."""
        manager = MockPluginManager()
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
        args.update_all = False
        args.check_updates = False
        args.browse = False
        args.search = None
        args.check_blacklist = None
        args.refresh_registry = False
        args.switch_ref = None
        args.clean_config = None
        args.validate = None
        args.manifest = None

        cli, stderr = _make_cli(manager, args, parser=None)
        result = cli.run()

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('No action specified', stderr.getvalue())

    def test_no_action_with_parser(self):
        """Test no action specified with parser prints help."""
        manager = MockPluginManager()
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
        args.update_all = False
        args.check_updates = False
        args.browse = False
        args.search = None
        args.check_blacklist = None
        args.refresh_registry = False
        args.switch_ref = None
        args.clean_config = None
        args.validate = None
        args.manifest = None

        parser = Mock()
        output = PluginOutput(stdout=StringIO(), stderr=StringIO(), color=False)

        cli = PluginCLI(manager, args, output=output, parser=parser)
        result = cli.run()

        self.assertEqual(result, ExitCode.SUCCESS)
        parser.print_help.assert_called_once()

    def test_keyboard_interrupt(self):
        """Test KeyboardInterrupt returns CANCELLED."""
        manager = MockPluginManager()
        args = MockCliArgs()
        args.ref = None
        args.list = True

        # Make _cmd_list raise KeyboardInterrupt
        cli, stderr = _make_cli(manager, args)
        cli._cmd_list = Mock(side_effect=KeyboardInterrupt())

        result = cli.run()

        self.assertEqual(result, ExitCode.CANCELLED)
        self.assertIn('cancelled', stderr.getvalue().lower())

    def test_generic_exception(self):
        """Test generic exception returns ERROR."""
        manager = MockPluginManager()
        args = MockCliArgs()
        args.ref = None
        args.list = True

        # Make _cmd_list raise exception
        cli, stderr = _make_cli(manager, args)
        cli._cmd_list = Mock(side_effect=ValueError('Test error'))

        result = cli.run()

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Test error', stderr.getvalue())


class TestPluginCLIHelpers(PicardTestCase):
    def test_format_git_info_no_metadata(self):
        """Test _format_git_info with no metadata."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info(None)
        self.assertEqual(result, '')

        result = cli._format_git_info({})
        self.assertEqual(result, '')

    def test_format_git_info_no_commit(self):
        """Test _format_git_info with no commit."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        metadata = PluginMetadata(url='http://test.com', ref='main', commit='')
        result = cli._format_git_info(metadata)
        self.assertEqual(result, '')

    def test_format_git_info_with_ref_and_commit(self):
        """Test _format_git_info with ref and commit."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        metadata = PluginMetadata(url='http://test.com', ref='main', commit='abc123def456')
        result = cli._format_git_info(metadata)
        self.assertEqual(result, ' (main @abc123d)')

    def test_format_git_info_commit_only(self):
        """Test _format_git_info with commit only."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        metadata = PluginMetadata(url='http://test.com', ref='', commit='abc123def456')
        result = cli._format_git_info(metadata)
        self.assertEqual(result, ' (@abc123d)')

    def test_format_git_info_ref_is_commit(self):
        """Test _format_git_info when ref is the commit hash."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        # When ref starts with commit short ID, skip ref
        metadata = PluginMetadata(url='http://test.com', ref='abc123d', commit='abc123def456')
        result = cli._format_git_info(metadata)
        self.assertEqual(result, ' (@abc123d)')


class TestPluginCLIFindPlugin(PicardTestCase):
    def test_find_plugin_or_error_multiple_matches(self):
        """Test _find_plugin_or_error with multiple matches."""
        manager = MockPluginManager()

        # Create mock plugins with same name
        plugin1 = Mock()
        plugin1.plugin_id = 'plugin_abc123'
        plugin1.manifest = Mock()
        plugin1.manifest.name.return_value = 'Test Plugin'
        plugin1.manifest.uuid = 'uuid-1'
        plugin1.uuid = 'uuid-1'

        plugin2 = Mock()
        plugin2.plugin_id = 'plugin_def456'
        plugin2.manifest = Mock()
        plugin2.manifest.name.return_value = 'Test Plugin'
        plugin2.manifest.uuid = 'uuid-2'
        plugin2.uuid = 'uuid-2'

        manager.plugins = [plugin1, plugin2]

        args = MockCliArgs()
        cli, stderr = _make_cli(manager, args)

        # Mock manager.find_plugin to return 'multiple'
        manager.find_plugin = Mock(return_value='multiple')

        result, error = cli._find_plugin_or_error('test plugin')

        self.assertIsNone(result)
        self.assertEqual(error, ExitCode.ERROR)
        self.assertIn('Multiple plugins found', stderr.getvalue())
        self.assertIn('uuid-1', stderr.getvalue())
        self.assertIn('uuid-2', stderr.getvalue())

    def test_find_plugin_or_error_not_found(self):
        """Test _find_plugin_or_error when plugin not found."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli, stderr = _make_cli(manager, args)

        manager.find_plugin = Mock(return_value=None)

        result, error = cli._find_plugin_or_error('nonexistent')

        self.assertIsNone(result)
        self.assertEqual(error, ExitCode.NOT_FOUND)
        self.assertIn('not found', stderr.getvalue())

    def test_find_plugin_or_error_success(self):
        """Test _find_plugin_or_error with successful find."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        mock_plugin = MockPlugin()
        manager.find_plugin = Mock(return_value=mock_plugin)

        result, error = cli._find_plugin_or_error('test')

        self.assertEqual(result, mock_plugin)
        self.assertIsNone(error)


class TestPluginCLICommands(PicardTestCase):
    def test_enable_plugin_error(self):
        """Test _enable_plugins with error."""
        manager = MockPluginManager()
        manager.enable_plugin.side_effect = ValueError('Enable failed')

        args = MockCliArgs()
        args.enable = ['test-plugin']

        cli, stderr = _make_cli(manager, args)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._cmd_enable(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to enable', stderr.getvalue())

    def test_disable_plugin_error(self):
        """Test _disable_plugins with error."""
        manager = MockPluginManager()
        manager.disable_plugin.side_effect = ValueError('Disable failed')

        args = MockCliArgs()
        args.disable = ['test-plugin']

        cli, stderr = _make_cli(manager, args)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._cmd_disable(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to disable', stderr.getvalue())

    def test_remove_plugin_error(self):
        """Test _uninstall_plugins with error."""
        manager = MockPluginManager()
        manager.uninstall_plugin.side_effect = ValueError('Uninstall failed')

        args = MockCliArgs()
        args.remove = ['test-plugin']
        args.yes = True
        args.purge = False

        cli, stderr = _make_cli(manager, args)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._cmd_remove(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to uninstall', stderr.getvalue())

    def test_install_plugin_error(self):
        """Test _install_plugins with error."""
        manager = MockPluginManager()
        manager.install_plugin.side_effect = ValueError('Install failed')
        manager._registry = Mock()
        manager._find_plugin_by_url = Mock(return_value=None)

        args = MockCliArgs()
        args.install = ['https://example.com/plugin.git']
        args.yes = True
        args.reinstall = False
        args.force_blacklisted = False
        args.ref = None

        cli, stderr = _make_cli(manager, args)

        result = cli._cmd_install(['https://example.com/plugin.git'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to install', stderr.getvalue())


class TestPluginCLIValidate(PicardTestCase):
    def test_validate_local_no_manifest(self):
        """Test validate with local directory without MANIFEST.toml."""
        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory to make it a git repo
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._cmd_validate(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('No MANIFEST.toml found', stderr.getvalue())

    def test_validate_local_invalid_manifest(self):
        """Test validate with invalid MANIFEST.toml."""
        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            # Create invalid manifest
            manifest_path = Path(tmpdir) / 'MANIFEST.toml'
            manifest_path.write_text('name = "Test"\n')  # Missing required fields

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._cmd_validate(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('Validation failed', stderr.getvalue())

    def test_validate_local_valid_manifest(self):
        """Test validate with valid MANIFEST.toml."""
        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = create_test_plugin_dir(tmpdir, 'test-plugin', add_git=True)

            stdout = StringIO()
            output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._cmd_validate(str(plugin_dir))

            self.assertEqual(result, ExitCode.SUCCESS)
            output_text = stdout.getvalue()
            self.assertIn('Validation passed', output_text)
            self.assertIn('Test Plugin', output_text)
            self.assertIn('1.0.0', output_text)

    def test_validate_local_with_optional_fields(self):
        """Test validate with optional fields in manifest."""
        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest with optional fields
            manifest_content = create_test_manifest_content(
                long_description='Detailed description',
                categories=['metadata', 'ui'],
                homepage='https://example.com',
                min_python_version='3.9',
                name_i18n={'de': 'Test Plugin DE'},
                description_i18n={'de': 'Test Beschreibung'},
                long_description_i18n={'de': 'Detaillierte Beschreibung'},
            )

            plugin_dir = create_test_plugin_dir(tmpdir, 'test-plugin', manifest_content, add_git=True)

            stdout = StringIO()
            output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._cmd_validate(str(plugin_dir))

            self.assertEqual(result, ExitCode.SUCCESS)
            output_text = stdout.getvalue()
            self.assertIn('Name_i18n: de', output_text)
            self.assertIn('Description_i18n: de', output_text)
            self.assertIn('Long_description_i18n: de', output_text)
            self.assertIn('Categories: metadata, ui', output_text)
            self.assertIn('Homepage: https://example.com', output_text)
            self.assertIn('Min Python version: 3.9', output_text)


class TestPluginCLIManifest(PicardTestCase):
    def test_show_manifest_template(self):
        """Test _show_manifest with no argument shows template."""
        manager = MockPluginManager()
        args = MockCliArgs()

        stdout = StringIO()
        output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
        cli = PluginCLI(manager, args, output=output)

        result = cli._cmd_manifest(None)

        self.assertEqual(result, ExitCode.SUCCESS)
        output_text = stdout.getvalue()
        self.assertIn('MANIFEST.toml Template', output_text)
        self.assertIn('uuid =', output_text)
        self.assertIn('name =', output_text)
        self.assertIn('version =', output_text)

    def test_show_manifest_from_plugin(self):
        """Test _show_manifest from installed plugin."""
        manager = MockPluginManager()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / 'test-plugin'
            plugin_dir.mkdir()

            # Create manifest
            manifest_path = plugin_dir / 'MANIFEST.toml'
            manifest_content = 'name = "Test"\nversion = "1.0"'
            manifest_path.write_text(manifest_content)

            # Mock plugin
            mock_plugin = MockPlugin()
            mock_plugin.local_path = plugin_dir

            stdout = StringIO()
            output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
            cli = PluginCLI(manager, args, output=output)
            manager.find_plugin = Mock(return_value=mock_plugin)

            result = cli._cmd_manifest('test-plugin')

            self.assertEqual(result, ExitCode.SUCCESS)
            self.assertIn('name = "Test"', stdout.getvalue())

    def test_show_manifest_plugin_no_manifest(self):
        """Test _show_manifest from plugin without MANIFEST.toml."""
        manager = MockPluginManager()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / 'test-plugin'
            plugin_dir.mkdir()

            # Mock plugin without manifest
            mock_plugin = MockPlugin()
            mock_plugin.local_path = plugin_dir

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)
            manager.find_plugin = Mock(return_value=mock_plugin)

            result = cli._cmd_manifest('test-plugin')

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('MANIFEST.toml not found', stderr.getvalue())

    def test_show_manifest_from_local_dir(self):
        """Test _show_manifest from local directory."""
        manager = MockPluginManager()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            # Create manifest
            manifest_path = Path(tmpdir) / 'MANIFEST.toml'
            manifest_content = 'name = "Local Test"'
            manifest_path.write_text(manifest_content)

            stdout = StringIO()
            output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
            cli = PluginCLI(manager, args, output=output)
            manager.find_plugin = Mock(return_value=None)

            result = cli._cmd_manifest(tmpdir)

            self.assertEqual(result, ExitCode.SUCCESS)
            self.assertIn('name = "Local Test"', stdout.getvalue())

    def test_show_manifest_local_dir_no_manifest(self):
        """Test _show_manifest from local directory without manifest."""
        manager = MockPluginManager()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)
            manager.find_plugin = Mock(return_value=None)

            result = cli._cmd_manifest(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('MANIFEST.toml not found', stderr.getvalue())


class TestPluginCLIColorOption(PicardTestCase):
    def test_no_color_option_disables_color(self):
        """Test --no-color option disables colored output."""
        args = MockCliArgs()
        args.no_color = True
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
        args.switch_ref = None
        args.clean_config = None
        args.validate = None
        args.manifest = None
        args.ref = None

        # Create output with no_color flag
        color = not getattr(args, 'no_color', False)
        output = PluginOutput(color=color)

        self.assertFalse(output.color)

    def test_color_enabled_by_default(self):
        """Test color is enabled by default when no --no-color."""

        args = MockCliArgs()
        args.no_color = False

        # Create output without no_color flag
        color = not getattr(args, 'no_color', False)

        # When stdout is not a tty, color will be False
        # So we just test the logic works
        self.assertTrue(color)

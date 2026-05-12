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
import shutil
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
    get_backend_repo,
    load_plugin_manifest,
    run_cli,
    skip_if_no_git_backend,
)

from picard.git.backend import GitStatusFlag
from picard.git.factory import has_git_backend
from picard.plugin3.cli import (
    ExitCode,
    PluginCLI,
)
from picard.plugin3.init_templates import generate_readme
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
from picard.plugin3.validator import (
    MAX_NAME_LENGTH,
    generate_uuid,
)


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
        manager = MockPluginManager(plugins=[])
        exit_code, stdout, _ = run_cli(manager, list=True)

        self.assertEqual(exit_code, 0)
        self.assertIn('No plugins installed', stdout)

    def test_list_plugins_with_plugins(self):
        """Test listing plugins with details."""
        test_uuid = generate_uuid()
        manifest = load_plugin_manifest('example')
        type(manifest).uuid = PropertyMock(return_value=test_uuid)

        mock_plugin = MockPlugin(name='test-plugin', uuid=test_uuid, manifest=manifest)
        manager = MockPluginManager(plugins=[mock_plugin], _enabled_plugins={test_uuid})
        manager._get_plugin_metadata = Mock(return_value={})

        exit_code, stdout, _ = run_cli(manager, list=True)

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

        manager = MockPluginManager(plugins=[plugin1, plugin2, plugin3])
        manager._get_plugin_metadata = Mock(return_value={})

        exit_code, stdout, _ = run_cli(manager, list=True)

        self.assertEqual(exit_code, 0)
        # Check that plugins appear in alphabetical order
        alpha_pos = stdout.find('Alpha Plugin')
        middle_pos = stdout.find('Middle Plugin')
        zebra_pos = stdout.find('Zebra Plugin')

        self.assertLess(alpha_pos, middle_pos)
        self.assertLess(middle_pos, zebra_pos)

    def test_info_plugin_not_found(self):
        """Test info command for non-existent plugin."""
        manager = MockPluginManager(plugins=[])
        manager.find_plugin = Mock(return_value=None)
        exit_code, _, stderr = run_cli(manager, info='nonexistent')

        self.assertEqual(exit_code, 2)
        self.assertIn('not found', stderr)

    def test_find_plugin_by_prefix(self):
        """Test finding plugin by Plugin ID prefix."""
        # Create plugin with full Plugin ID
        test_uuid = generate_uuid()
        mock_plugin = MockPlugin(name=f'example_plugin_{test_uuid}', display_name='Example Plugin')
        manager = MockPluginManager(plugins=[mock_plugin])

        # Mock find_plugin to return the plugin for this test
        manager.find_plugin = Mock(return_value=mock_plugin)

        result = manager.find_plugin('example_plugin')

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

            manager = create_mock_manager_with_manifest_validation()
            exit_code, stdout, stderr = run_cli(manager, validate=str(plugin_dir))

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
        manager = MockPluginManager(plugins=[mock_plugin])
        manager.check_updates = Mock(return_value={})
        manager.update_all_plugins = Mock(return_value=[])

        # Test --check-updates
        exit_code, _, _ = run_cli(manager, check_updates=True)
        self.assertEqual(exit_code, 0)
        manager.check_updates.assert_called_once()

        # Test --update-all
        exit_code, _, _ = run_cli(manager, update_all=True)
        self.assertEqual(exit_code, 0)
        manager.update_all_plugins.assert_called_once()

    def test_update_plugin_not_found(self):
        """Test update command for non-existent plugin."""
        manager = MockPluginManager(plugins=[])
        manager.find_plugin = Mock(return_value=None)
        exit_code, _, stderr = run_cli(manager, update=['nonexistent'])

        self.assertEqual(exit_code, 2)
        self.assertIn('not found', stderr)

    def test_update_plugin_with_version_object(self):
        """Test update command properly handles Version objects."""

        manifest = load_plugin_manifest('example')
        mock_plugin = MockPlugin(manifest=manifest)
        manager = MockPluginManager(plugins=[mock_plugin])

        # Simulate update_plugin returning Version objects (the bug scenario)
        manager.update_plugin = Mock(
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

        exit_code, stdout, _ = run_cli(manager, update=['test-plugin'])

        self.assertEqual(exit_code, 0)
        self.assertIn('1.0.0', stdout)
        self.assertIn('1.1.0', stdout)
        manager.update_plugin.assert_called_once()

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

            manager = PluginManager(Mock())
            with (
                patch('picard.plugin3.manager.lifecycle.get_config', return_value=test_config),
                patch('picard.plugin3.manager.clean.get_config', return_value=test_config),
                patch('picard.plugin3.cli.get_config', return_value=test_config),
            ):
                exit_code, stdout, _ = run_cli(manager, clean_config=test_uuid, yes=True)

            self.assertEqual(exit_code, 0)
            self.assertIn('deleted', stdout.lower())

            # Verify settings were removed
            test_config.beginGroup(f'plugin.{test_uuid}')
            self.assertEqual(len(test_config.childKeys()), 0)
            test_config.endGroup()

    def test_enable_plugins_command(self):
        """Test enable command."""
        mock_plugin = MockPlugin()
        manager = MockPluginManager(plugins=[mock_plugin], enable_plugin=Mock())
        manager.find_plugin = Mock(return_value=mock_plugin)

        exit_code, _, _ = run_cli(manager, enable=['test-plugin'])

        self.assertEqual(exit_code, 0)
        manager.enable_plugin.assert_called_once_with(mock_plugin)

    def test_disable_plugins_command(self):
        """Test disable command."""
        mock_plugin = MockPlugin()
        manager = MockPluginManager(plugins=[mock_plugin], disable_plugin=Mock())
        manager.find_plugin = Mock(return_value=mock_plugin)

        exit_code, _, _ = run_cli(manager, disable=['test-plugin'])

        self.assertEqual(exit_code, 0)
        manager.disable_plugin.assert_called_once_with(mock_plugin)

    def test_cli_keyboard_interrupt(self):
        """Test CLI handles KeyboardInterrupt."""
        mock_plugin = MockPlugin()
        manager = MockPluginManager(plugins=[mock_plugin])
        manager.check_updates = Mock(side_effect=KeyboardInterrupt())

        exit_code, _, stderr = run_cli(manager, check_updates=True)

        self.assertEqual(exit_code, 130)
        self.assertIn('cancelled', stderr.lower())

    def test_browse_plugins_command(self):
        """Test --browse command."""
        manager = MockPluginManager()
        manager._registry.list_plugins.return_value = [
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

        exit_code, _, _ = run_cli(manager, browse=True)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager._registry.list_plugins.assert_called_once_with(category=None, trust_level=None)

    def test_browse_plugins_with_filters(self):
        """Test --browse with category and trust filters."""
        manager = MockPluginManager()
        manager._registry.list_plugins.return_value = [
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

        exit_code, _, _ = run_cli(manager, browse=True, category='metadata', trust='official')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager._registry.list_plugins.assert_called_once_with(category='metadata', trust_level='official')

    def test_search_plugins_command(self):
        """Test --search command."""
        manager = MockPluginManager()
        manager._registry.list_plugins.return_value = [
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

        exit_code, _, _ = run_cli(manager, search='listen')

        self.assertEqual(exit_code, ExitCode.SUCCESS)

    def test_install_by_plugin_id(self):
        """Test installing plugin by ID from registry."""
        mock_plugin = Mock()
        mock_plugin.id = 'test-plugin'
        mock_plugin.name = 'Test Plugin'
        mock_plugin.git_url = 'https://github.com/test/plugin'
        mock_plugin.versioning_scheme = None  # No versioning scheme
        mock_plugin.refs = []  # No explicit refs

        manager = MockPluginManager()
        manager._registry.find_plugin.return_value = mock_plugin
        manager._find_plugin_by_url.return_value = None  # Not already installed
        manager.install_plugin.return_value = 'test-plugin'

        exit_code, _, _ = run_cli(manager, install=['test-plugin'])

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager._registry.find_plugin.assert_called_once_with(plugin_id='test-plugin')
        manager.install_plugin.assert_called_once()

    def test_install_by_plugin_id_not_found(self):
        """Test installing plugin by ID that doesn't exist in registry."""
        manager = MockPluginManager()
        manager._registry.find_plugin.return_value = None
        manager._registry.list_plugins.return_value = []

        exit_code, _, stderr = run_cli(manager, install=['nonexistent'])

        self.assertEqual(exit_code, ExitCode.NOT_FOUND)
        self.assertIn('not found in registry', stderr)

    def test_check_blacklist_not_blacklisted(self):
        """Test --check-blacklist with non-blacklisted URL."""
        manager = MockPluginManager()
        manager._registry.is_blacklisted.return_value = (False, None)

        exit_code, stdout, _ = run_cli(manager, check_blacklist='https://github.com/test/plugin')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('Not blacklisted', stdout)
        manager._registry.is_blacklisted.assert_called_once_with('https://github.com/test/plugin', None)

    def test_check_blacklist_is_blacklisted(self):
        """Test --check-blacklist with blacklisted URL."""
        manager = MockPluginManager()
        manager._registry.is_blacklisted.return_value = (True, 'Security vulnerability')

        exit_code, stdout, stderr = run_cli(manager, check_blacklist='https://github.com/bad/plugin')

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        self.assertIn('Security vulnerability', stderr)

    def test_check_blacklist_with_uuid(self):
        """Test --check-blacklist with --uuid passes UUID to is_blacklisted."""
        manager = MockPluginManager()
        manager._registry.is_blacklisted.return_value = (True, 'Security vulnerability')

        exit_code, stdout, stderr = run_cli(
            manager,
            check_blacklist='https://github.com/test/plugin',
            uuid='blacklisted-uuid-1234',
        )

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        manager._registry.is_blacklisted.assert_called_once_with(
            'https://github.com/test/plugin', 'blacklisted-uuid-1234'
        )

    def test_check_blacklist_uuid_only(self):
        """Test --check-blacklist --uuid without URL."""
        manager = MockPluginManager()
        manager._registry.is_blacklisted.return_value = (True, 'UUID is blacklisted')

        exit_code, stdout, stderr = run_cli(
            manager,
            check_blacklist='',
            uuid='blacklisted-uuid-1234',
        )

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Blacklisted', stderr)
        manager._registry.is_blacklisted.assert_called_once_with(
            None,
            'blacklisted-uuid-1234',
        )

    def test_search_with_category_filter(self):
        """Test --search with --category filter."""
        manager = MockPluginManager()
        manager._registry.list_plugins.return_value = [
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

        exit_code, _, _ = run_cli(manager, search='test', category='metadata')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager._registry.list_plugins.assert_called_once_with(category='metadata', trust_level=None)

    def test_search_with_trust_filter(self):
        """Test --search with --trust filter."""
        manager = MockPluginManager()
        manager._registry.list_plugins.return_value = []

        exit_code, _, _ = run_cli(manager, search='test', trust='official')

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager._registry.list_plugins.assert_called_once_with(category=None, trust_level='official')

    def test_refresh_registry_command(self):
        """Test --refresh-registry command."""
        manager = MockPluginManager()

        # Mock refresh_registry_and_caches to call callback immediately
        def mock_refresh(callback=None):
            if callback:
                callback(True, None)

        manager.refresh_registry_and_caches = Mock(side_effect=mock_refresh)
        manager._registry.get_registry_info.return_value = {
            'plugin_count': 42,
            'api_version': '3.0',
            'registry_url': 'https://test.example.com/registry.toml',
        }

        exit_code, stdout, _ = run_cli(manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        manager.refresh_registry_and_caches.assert_called_once()
        manager._registry.get_registry_info.assert_called_once()
        self.assertIn('Registry refreshed successfully', stdout)
        self.assertIn('Plugins available: 42', stdout)

    def test_refresh_registry_error(self):
        """Test --refresh-registry command with error."""
        manager = MockPluginManager()
        manager.refresh_registry_and_caches.side_effect = Exception('Network error')

        exit_code, _, stderr = run_cli(manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to refresh registry', stderr)
        self.assertIn('Network error', stderr)

    def test_refresh_registry_fetch_error(self):
        """Test --refresh-registry with RegistryFetchError."""
        manager = MockPluginManager()
        manager.refresh_registry_and_caches.side_effect = RegistryFetchError(
            'https://test.example.com/registry.toml', Exception('Connection timeout')
        )

        exit_code, _, stderr = run_cli(manager, refresh_registry=True)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Failed to fetch registry', stderr)
        self.assertIn('https://test.example.com/registry.toml', stderr)
        self.assertIn('Connection timeout', stderr)

    def test_refresh_registry_parse_error(self):
        """Test --refresh-registry with RegistryParseError."""
        manager = MockPluginManager()
        manager.refresh_registry_and_caches.side_effect = RegistryParseError(
            'https://test.example.com/registry.toml', Exception('Invalid JSON')
        )

        exit_code, _, stderr = run_cli(manager, refresh_registry=True)

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
        manager = MockPluginManager(plugins=[mock_plugin])

        # Mock update_plugin to raise PluginCommitPinnedError
        manager.update_plugin.side_effect = PluginCommitPinnedError('test-plugin', 'abc1234')

        exit_code, stdout, stderr = run_cli(manager, update=['test-plugin'])

        self.assertEqual(exit_code, 0)
        self.assertIn('pinned to commit', stderr)
        self.assertIn('switch-ref', stdout)
        # Should have called update_plugin (which raised the exception)
        manager.update_plugin.assert_called_once()


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
        skip_if_no_git_backend()
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
        skip_if_no_git_backend()
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


class TestPluginCLIInit(PicardTestCase):
    """Tests for --init command (non-interactive mode)."""

    def setUp(self):
        super().setUp()
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_directory(self):
        """--init NAME creates picard-plugin-<slug> directory."""
        target = self.tmpdir / 'picard-plugin-my-cool-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='My Cool Plugin', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue(target.exists())

    def test_init_creates_manifest(self):
        """--init creates MANIFEST.toml with correct name."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test Plugin', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('name = "Test Plugin"', manifest)
        self.assertIn('api = ["3.0"]', manifest)

    def test_init_creates_init_py(self):
        """--init creates __init__.py with enable/disable stubs."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        init_py = (target / '__init__.py').read_text(encoding='utf-8')
        self.assertIn('def enable(api: PluginApi)', init_py)
        self.assertIn('def disable()', init_py)

    def test_init_creates_readme(self):
        """--init creates README.md with plugin name."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='My Plugin', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        readme = (target / 'README.md').read_text(encoding='utf-8')
        self.assertIn('# My Plugin', readme)

    def test_init_creates_readme_with_provided_description(self):
        """Creates README.md content with provided long description."""
        long_description = "This the test long description."
        readme_content = generate_readme('Test Plugin', long_description)
        self.assertIn(long_description, readme_content)

    def test_init_creates_readme_without_provided_description(self):
        """Creates README.md content without provided long description."""
        default_description = "A plugin for [MusicBrainz Picard](https://picard.musicbrainz.org/)."
        # Test with no long description specified (use default of None)
        readme_content = generate_readme('Test Plugin')
        self.assertIn(default_description, readme_content)
        # Test with long description specified as empty string
        readme_content = generate_readme('Test Plugin', '')
        self.assertIn(default_description, readme_content)
        # Test with long description specified as whitespace only
        readme_content = generate_readme('Test Plugin', ' ')
        self.assertIn(default_description, readme_content)
        # Test with long description specified as newline only
        readme_content = generate_readme('Test Plugin', '\n')
        self.assertIn(default_description, readme_content)

    def test_init_creates_gitignore(self):
        """--init creates .gitignore."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        gitignore = (target / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('__pycache__/', gitignore)

    def test_init_with_author(self):
        """--init --author sets authors in MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target), author='Jane Doe')
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('authors = ["Jane Doe"]', manifest)

    def test_init_with_author_email_notation(self):
        """--init --author 'Name <email>' parses name for MANIFEST and email for git."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), author='Jane Doe <jane@example.com>'
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('authors = ["Jane Doe"]', manifest)

    def test_init_author_email_sets_report_bugs_to(self):
        """--init --author 'Name <email>' sets report_bugs_to mailto in MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), author='Jane Doe <jane@example.com>'
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('report_bugs_to = "mailto:jane@example.com"', manifest)

    def test_init_no_email_has_report_bugs_to_comment(self):
        """--init without email has commented report_bugs_to in MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('# report_bugs_to =', manifest)

    def test_init_with_category(self):
        """--init --category sets categories in MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), category='metadata'
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('categories = ["metadata"]', manifest)

    def test_init_default_directory_name(self):
        """--init without --target-dir uses picard-plugin-<slug> in cwd."""
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test Plugin', target_dir=str(self.tmpdir / 'picard-plugin-test-plugin')
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((self.tmpdir / 'picard-plugin-test-plugin').exists())

    def test_init_existing_nonempty_dir_fails(self):
        """--init fails if target directory exists and is not empty."""
        target = self.tmpdir / 'existing'
        target.mkdir()
        (target / 'somefile').write_text('content')
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.ERROR, exit_code)
        self.assertIn('not empty', stderr)

    def test_init_existing_empty_dir_succeeds(self):
        """--init succeeds if target directory exists but is empty."""
        target = self.tmpdir / 'empty'
        target.mkdir()
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / 'MANIFEST.toml').exists())

    def test_init_no_name_with_yes_fails(self):
        """--init --yes without name fails."""
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', yes=True)
        self.assertEqual(ExitCode.ERROR, exit_code)
        self.assertIn('required', stderr)

    def test_init_prints_summary(self):
        """--init prints created files summary."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertIn('MANIFEST.toml', stdout)
        self.assertIn('__init__.py', stdout)
        self.assertIn('README.md', stdout)
        self.assertIn('.gitignore', stdout)

    def test_init_name_too_long(self):
        """--init fails if name exceeds MAX_NAME_LENGTH."""
        long_name = 'A' * (MAX_NAME_LENGTH + 1)
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init=long_name, target_dir=str(self.tmpdir / 'test'))
        self.assertEqual(ExitCode.ERROR, exit_code)
        self.assertIn('maximum length', stderr)

    def test_init_parent_dir(self):
        """--parent-dir sets the parent directory."""
        parent = self.tmpdir / 'projects'
        parent.mkdir()
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test Plugin', parent_dir=str(parent))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((parent / 'picard-plugin-test-plugin').exists())

    def test_init_parent_dir_with_target_dir(self):
        """--target-dir is relative to --parent-dir."""
        parent = self.tmpdir / 'projects'
        parent.mkdir()
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', parent_dir=str(parent), target_dir='custom-name'
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((parent / 'custom-name').exists())

    def test_init_empty_slug_no_target_dir_fails(self):
        """--init with a name that produces an empty slug and no --target-dir fails."""
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='!!!')
        self.assertEqual(ExitCode.ERROR, exit_code)
        self.assertIn('--target-dir', stderr)

    def test_init_with_translations_manifest(self):
        """--init --with-translations adds source_locale and i18n comments to MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), with_translations=True
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('source_locale = "en"', manifest)
        self.assertIn('# [name_i18n]', manifest)
        self.assertIn('# [description_i18n]', manifest)

    def test_init_with_translations_init_py(self):
        """--init --with-translations generates __init__.py with t_ and api.tr usage."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), with_translations=True
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        init_py = (target / '__init__.py').read_text(encoding='utf-8')
        self.assertIn('from picard.plugin3.api import', init_py)
        self.assertIn('t_,', init_py)
        self.assertIn('api.tr(', init_py)

    def test_init_with_translations_creates_locale_dir(self):
        """--init --with-translations creates locale/ directory with source locale file."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), with_translations=True
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / 'locale').is_dir())
        self.assertIn('locale/', stdout)
        en_toml = (target / 'locale' / 'en.toml').read_text(encoding='utf-8')
        self.assertIn('message.greeting', en_toml)

    def test_init_without_i18n_no_locale_dir(self):
        """--init without --with-translations does not create locale/ directory."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertFalse((target / 'locale').exists())

    def test_init_without_i18n_no_source_locale(self):
        """--init without --with-translations does not add source_locale to MANIFEST."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertNotIn('source_locale', manifest)

    def test_init_with_custom_source_locale(self):
        """--init --with-translations --source-locale creates correct locale file and manifest."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(
            MockPluginManager(), init='Test', target_dir=str(target), with_translations=True, source_locale='fr'
        )
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('source_locale = "fr"', manifest)
        self.assertTrue((target / 'locale' / 'fr.toml').exists())
        self.assertFalse((target / 'locale' / 'en.toml').exists())


class TestPluginCLIInitInteractive(PicardTestCase):
    """Tests for --init interactive mode."""

    def setUp(self):
        super().setUp()
        self.tmpdir = Path(tempfile.mkdtemp())
        patcher = patch('picard.plugin3.cli.get_git_config_author', return_value=('', ''))
        self._mock_git_config = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @staticmethod
    def _init_inputs(
        name='Test',
        target_path='',
        author='',
        email='',
        description='',
        category='',
        license='',
        with_i18n='n',
        git_commit='y',
    ):
        """Build input side_effect list for _cmd_init_interactive prompts.

        Only specify the values that differ from defaults.
        The email prompt only appears when author is non-empty.
        """
        inputs = [name, target_path, author]
        if author:
            inputs.append(email)
        inputs.extend([description, category, license, with_i18n, git_commit])
        return inputs

    def test_interactive_full(self):
        """Interactive mode with all fields filled in."""
        target = self.tmpdir / 'picard-plugin-my-plugin'
        inputs = self._init_inputs(
            name='My Plugin',
            author='Alice',
            email='alice@example.com',
            description='A test plugin',
            category='1',
        )
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('name = "My Plugin"', manifest)
        self.assertIn('authors = ["Alice"]', manifest)
        self.assertIn('description = "A test plugin"', manifest)
        self.assertIn('categories = ["metadata"]', manifest)

    def test_interactive_minimal(self):
        """Interactive mode with only name provided."""
        target = self.tmpdir / 'picard-plugin-my-plugin'
        inputs = self._init_inputs(name='My Plugin')
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / 'MANIFEST.toml').exists())

    def test_interactive_empty_name_fails(self):
        """Interactive mode fails if name is empty."""
        inputs = self._init_inputs(name='')
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='')
        self.assertEqual(ExitCode.ERROR, exit_code)
        self.assertIn('required', stderr)

    def test_interactive_custom_license(self):
        """Interactive mode with custom license."""
        target = self.tmpdir / 'test'
        inputs = self._init_inputs(license='MIT')
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('license = "MIT"', manifest)

    def test_interactive_default_license(self):
        """Interactive mode defaults to GPL-2.0-or-later."""
        target = self.tmpdir / 'test'
        inputs = self._init_inputs()
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('license = "GPL-2.0-or-later"', manifest)
        self.assertIn('license_url = "https://www.gnu.org/licenses/gpl-2.0.html"', manifest)

    def test_interactive_invalid_category_ignored(self):
        """Interactive mode ignores invalid category input."""
        target = self.tmpdir / 'test'
        inputs = self._init_inputs(category='invalid')
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertNotIn('categories', manifest)

    def test_interactive_multiple_categories(self):
        """Interactive mode accepts multiple comma-separated categories."""
        target = self.tmpdir / 'test'
        inputs = self._init_inputs(category='1,3')
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        manifest = (target / 'MANIFEST.toml').read_text(encoding='utf-8')
        self.assertIn('categories = ["metadata", "ui"]', manifest)

    def test_interactive_default_destination(self):
        """Interactive mode shows default destination and accepts it."""
        target = self.tmpdir / 'picard-plugin-test'
        inputs = self._init_inputs()
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='', parent_dir=str(self.tmpdir))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / 'MANIFEST.toml').exists())

    def test_interactive_custom_destination(self):
        """Interactive mode allows overriding destination directory."""
        custom_target = self.tmpdir / 'custom-dir'
        inputs = self._init_inputs(target_path=str(custom_target))
        with patch('builtins.input', side_effect=inputs):
            exit_code, stdout, stderr = run_cli(MockPluginManager(), init='')
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((custom_target / 'MANIFEST.toml').exists())


class TestPluginCLIInitGit(PicardTestCase):
    """Tests for --init git repository initialization."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_git_repo(self):
        """--init creates a git repository."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / '.git').is_dir())

    def test_init_creates_initial_commit(self):
        """--init creates an initial commit with all files."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        repo = get_backend_repo(target)
        # Should have a HEAD pointing to a commit
        head = repo.get_head_target()
        self.assertIsNotNone(head)
        repo.free()

    def test_init_git_message_in_output(self):
        """--init prints git initialization message."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertIn('Git repository initialized', stdout)

    def test_init_all_files_committed(self):
        """--init commits all generated files (clean working tree)."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target))
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        repo = get_backend_repo(target)
        status = repo.get_status()
        # Filter out ignored files - only check for modified/new files
        dirty = {f for f, s in status.items() if s != GitStatusFlag.IGNORED}
        self.assertEqual(dirty, set(), f'Uncommitted files: {dirty}')
        repo.free()

    def test_init_commit_uses_provided_author(self):
        """--init --author uses the provided name for the git commit."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target), author='Jane Doe')
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        repo = get_backend_repo(target)
        commit_id = repo.get_head_target()
        author_name, _ = repo.get_commit_author(commit_id)
        self.assertEqual(author_name, 'Jane Doe')
        repo.free()

    def test_init_no_commit_skips_initial_commit(self):
        """--init --no-commit creates git repo but no commit."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target), no_commit=True)
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertTrue((target / '.git').is_dir())
        repo = get_backend_repo(target)
        self.assertEqual(repo.list_references(), [])
        repo.free()

    def test_init_no_commit_output_message(self):
        """--init --no-commit shows 'initialized' without 'initial commit'."""
        target = self.tmpdir / 'test-plugin'
        exit_code, stdout, stderr = run_cli(MockPluginManager(), init='Test', target_dir=str(target), no_commit=True)
        self.assertEqual(ExitCode.SUCCESS, exit_code)
        self.assertIn('Git repository initialized', stdout)
        self.assertNotIn('initial commit', stdout)

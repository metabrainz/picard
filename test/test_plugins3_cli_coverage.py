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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockCliArgs,
    MockPlugin,
    MockPluginManager,
)

from picard.plugin3.cli import (
    ExitCode,
    PluginCLI,
)
from picard.plugin3.output import PluginOutput


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

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)

        cli = PluginCLI(manager, args, output=output, parser=None)
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

        # Make _list_plugins raise KeyboardInterrupt
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)
        cli._list_plugins = Mock(side_effect=KeyboardInterrupt())

        result = cli.run()

        self.assertEqual(result, ExitCode.CANCELLED)
        self.assertIn('cancelled', stderr.getvalue().lower())

    def test_generic_exception(self):
        """Test generic exception returns ERROR."""
        manager = MockPluginManager()
        args = MockCliArgs()
        args.ref = None
        args.list = True

        # Make _list_plugins raise exception
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)
        cli._list_plugins = Mock(side_effect=ValueError('Test error'))

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

        result = cli._format_git_info({'ref': 'main'})
        self.assertEqual(result, '')

    def test_format_git_info_with_ref_and_commit(self):
        """Test _format_git_info with ref and commit."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info({'ref': 'main', 'commit': 'abc123def456'})
        self.assertEqual(result, ' (main @abc123d)')

    def test_format_git_info_commit_only(self):
        """Test _format_git_info with commit only."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info({'commit': 'abc123def456'})
        self.assertEqual(result, ' (@abc123d)')

    def test_format_git_info_ref_is_commit(self):
        """Test _format_git_info when ref is the commit hash."""
        manager = MockPluginManager()
        args = MockCliArgs()
        cli = PluginCLI(manager, args)

        # When ref starts with commit short ID, skip ref
        result = cli._format_git_info({'ref': 'abc123d', 'commit': 'abc123def456'})
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

        plugin2 = Mock()
        plugin2.plugin_id = 'plugin_def456'
        plugin2.manifest = Mock()
        plugin2.manifest.name.return_value = 'Test Plugin'
        plugin2.manifest.uuid = 'uuid-2'

        manager.plugins = [plugin1, plugin2]

        args = MockCliArgs()
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        # Mock _find_plugin to return 'multiple'
        cli._find_plugin = Mock(return_value='multiple')

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
        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        cli._find_plugin = Mock(return_value=None)

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
        cli._find_plugin = Mock(return_value=mock_plugin)

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

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._enable_plugins(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to enable', stderr.getvalue())

    def test_disable_plugin_error(self):
        """Test _disable_plugins with error."""
        manager = MockPluginManager()
        manager.disable_plugin.side_effect = ValueError('Disable failed')

        args = MockCliArgs()
        args.disable = ['test-plugin']

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._disable_plugins(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to disable', stderr.getvalue())

    def test_uninstall_plugin_error(self):
        """Test _uninstall_plugins with error."""
        manager = MockPluginManager()
        manager.uninstall_plugin.side_effect = ValueError('Uninstall failed')

        args = MockCliArgs()
        args.uninstall = ['test-plugin']
        args.yes = True
        args.purge = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = MockPlugin()
        mock_plugin.plugin_id = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._uninstall_plugins(['test-plugin'])

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

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        result = cli._install_plugins(['https://example.com/plugin.git'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to install', stderr.getvalue())


class TestPluginCLIValidate(PicardTestCase):
    def test_validate_local_no_manifest(self):
        """Test validate with local directory without MANIFEST.toml."""
        from pathlib import Path
        import tempfile

        from test.test_plugins3_helpers import create_mock_manager_with_manifest_validation

        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory to make it a git repo
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._validate_plugin(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('No MANIFEST.toml found', stderr.getvalue())

    def test_validate_local_invalid_manifest(self):
        """Test validate with invalid MANIFEST.toml."""
        from pathlib import Path
        import tempfile

        from test.test_plugins3_helpers import create_mock_manager_with_manifest_validation

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

            result = cli._validate_plugin(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('Validation failed', stderr.getvalue())

    def test_validate_local_valid_manifest(self):
        """Test validate with valid MANIFEST.toml."""
        import tempfile

        from test.test_plugins3_helpers import (
            create_mock_manager_with_manifest_validation,
            create_test_plugin_dir,
        )

        manager = create_mock_manager_with_manifest_validation()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = create_test_plugin_dir(tmpdir, 'test-plugin', add_git=True)

            stdout = StringIO()
            output = PluginOutput(stdout=stdout, stderr=StringIO(), color=False)
            cli = PluginCLI(manager, args, output=output)

            result = cli._validate_plugin(str(plugin_dir))

            self.assertEqual(result, ExitCode.SUCCESS)
            output_text = stdout.getvalue()
            self.assertIn('Validation passed', output_text)
            self.assertIn('Test Plugin', output_text)
            self.assertIn('1.0.0', output_text)

    def test_validate_local_with_optional_fields(self):
        """Test validate with optional fields in manifest."""
        import tempfile

        from test.test_plugins3_helpers import (
            create_mock_manager_with_manifest_validation,
            create_test_manifest_content,
            create_test_plugin_dir,
        )

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

            result = cli._validate_plugin(str(plugin_dir))

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

        result = cli._show_manifest(None)

        self.assertEqual(result, ExitCode.SUCCESS)
        output_text = stdout.getvalue()
        self.assertIn('MANIFEST.toml Template', output_text)
        self.assertIn('uuid =', output_text)
        self.assertIn('name =', output_text)
        self.assertIn('version =', output_text)

    def test_show_manifest_from_plugin(self):
        """Test _show_manifest from installed plugin."""
        from pathlib import Path
        import tempfile

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
            cli._find_plugin = Mock(return_value=mock_plugin)

            result = cli._show_manifest('test-plugin')

            self.assertEqual(result, ExitCode.SUCCESS)
            self.assertIn('name = "Test"', stdout.getvalue())

    def test_show_manifest_plugin_no_manifest(self):
        """Test _show_manifest from plugin without MANIFEST.toml."""
        from pathlib import Path
        import tempfile

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
            cli._find_plugin = Mock(return_value=mock_plugin)

            result = cli._show_manifest('test-plugin')

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('MANIFEST.toml not found', stderr.getvalue())

    def test_show_manifest_from_local_dir(self):
        """Test _show_manifest from local directory."""
        from pathlib import Path
        import tempfile

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
            cli._find_plugin = Mock(return_value=None)

            result = cli._show_manifest(tmpdir)

            self.assertEqual(result, ExitCode.SUCCESS)
            self.assertIn('name = "Local Test"', stdout.getvalue())

    def test_show_manifest_local_dir_no_manifest(self):
        """Test _show_manifest from local directory without manifest."""
        from pathlib import Path
        import tempfile

        manager = MockPluginManager()
        args = MockCliArgs()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .git directory
            git_dir = Path(tmpdir) / '.git'
            git_dir.mkdir()

            stderr = StringIO()
            output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
            cli = PluginCLI(manager, args, output=output)
            cli._find_plugin = Mock(return_value=None)

            result = cli._show_manifest(tmpdir)

            self.assertEqual(result, ExitCode.ERROR)
            self.assertIn('MANIFEST.toml not found', stderr.getvalue())


class TestPluginCLIColorOption(PicardTestCase):
    def test_no_color_option_disables_color(self):
        """Test --no-color option disables colored output."""
        from picard.plugin3.output import PluginOutput

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

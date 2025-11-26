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

from picard.plugin3.cli import (
    ExitCode,
    PluginCLI,
)
from picard.plugin3.output import PluginOutput


class TestPluginCLIErrors(PicardTestCase):
    def test_ref_without_install_or_validate(self):
        """Test --ref without --install or --validate returns error."""
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info(None)
        self.assertEqual(result, '')

        result = cli._format_git_info({})
        self.assertEqual(result, '')

    def test_format_git_info_no_commit(self):
        """Test _format_git_info with no commit."""
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info({'ref': 'main'})
        self.assertEqual(result, '')

    def test_format_git_info_with_ref_and_commit(self):
        """Test _format_git_info with ref and commit."""
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info({'ref': 'main', 'commit': 'abc123def456'})
        self.assertEqual(result, ' (main @abc123d)')

    def test_format_git_info_commit_only(self):
        """Test _format_git_info with commit only."""
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        result = cli._format_git_info({'commit': 'abc123def456'})
        self.assertEqual(result, ' (@abc123d)')

    def test_format_git_info_ref_is_commit(self):
        """Test _format_git_info when ref is the commit hash."""
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        # When ref starts with commit short ID, skip ref
        result = cli._format_git_info({'ref': 'abc123d', 'commit': 'abc123def456'})
        self.assertEqual(result, ' (@abc123d)')


class TestPluginCLIFindPlugin(PicardTestCase):
    def test_find_plugin_or_error_multiple_matches(self):
        """Test _find_plugin_or_error with multiple matches."""
        manager = Mock()

        # Create mock plugins with same name
        plugin1 = Mock()
        plugin1.name = 'plugin_abc123'
        plugin1.manifest = Mock()
        plugin1.manifest.name.return_value = 'Test Plugin'
        plugin1.manifest.uuid = 'uuid-1'

        plugin2 = Mock()
        plugin2.name = 'plugin_def456'
        plugin2.manifest = Mock()
        plugin2.manifest.name.return_value = 'Test Plugin'
        plugin2.manifest.uuid = 'uuid-2'

        manager.plugins = [plugin1, plugin2]

        args = Mock()
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
        manager = Mock()
        args = Mock()
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
        manager = Mock()
        args = Mock()
        cli = PluginCLI(manager, args)

        mock_plugin = Mock()
        cli._find_plugin = Mock(return_value=mock_plugin)

        result, error = cli._find_plugin_or_error('test')

        self.assertEqual(result, mock_plugin)
        self.assertIsNone(error)


class TestPluginCLICommands(PicardTestCase):
    def test_enable_plugin_error(self):
        """Test _enable_plugins with error."""
        manager = Mock()
        manager.enable_plugin.side_effect = ValueError('Enable failed')

        args = Mock()
        args.enable = ['test-plugin']

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._enable_plugins(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to enable', stderr.getvalue())

    def test_disable_plugin_error(self):
        """Test _disable_plugins with error."""
        manager = Mock()
        manager.disable_plugin.side_effect = ValueError('Disable failed')

        args = Mock()
        args.disable = ['test-plugin']

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._disable_plugins(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to disable', stderr.getvalue())

    def test_uninstall_plugin_error(self):
        """Test _uninstall_plugins with error."""
        manager = Mock()
        manager.uninstall_plugin.side_effect = ValueError('Uninstall failed')

        args = Mock()
        args.uninstall = ['test-plugin']
        args.yes = True
        args.purge = False

        stderr = StringIO()
        output = PluginOutput(stdout=StringIO(), stderr=stderr, color=False)
        cli = PluginCLI(manager, args, output=output)

        mock_plugin = Mock()
        mock_plugin.name = 'test-plugin'
        cli._find_plugin_or_error = Mock(return_value=(mock_plugin, None))

        result = cli._uninstall_plugins(['test-plugin'])

        self.assertEqual(result, ExitCode.ERROR)
        self.assertIn('Failed to uninstall', stderr.getvalue())

    def test_install_plugin_error(self):
        """Test _install_plugins with error."""
        manager = Mock()
        manager.install_plugin.side_effect = ValueError('Install failed')
        manager._registry = Mock()

        args = Mock()
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

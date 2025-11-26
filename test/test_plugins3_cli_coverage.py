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

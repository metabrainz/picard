# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
import os
from types import SimpleNamespace
from unittest.mock import patch

from test.test_config import TestPicardConfigCommon

from picard.cli.base import ExitCode
from picard.cli.output import CliOutput
from picard.config import (
    BoolOption,
    ListOption,
    Option,
    TextOption,
)
from picard.profiles.cli import (
    cmd_export,
    cmd_import,
    cmd_list,
)


def _make_output():
    """Create a CliOutput with StringIO streams for testing."""
    stdout = StringIO()
    stderr = StringIO()
    return CliOutput(stdout=stdout, stderr=stderr, color=False), stdout, stderr


class TestProfileCLI(TestPicardConfigCommon):
    def setUp(self):
        super().setUp()
        ListOption.add_if_missing('profiles', 'user_profiles', [])
        Option.add_if_missing('profiles', 'user_profile_settings', {})
        Option('setting', 'file_renaming_scripts', {})

    def _setup_profiles(self):
        """Set up some test profiles."""
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)
        self.config.profiles['user_profiles'] = [
            {'id': 'p1', 'title': 'My Rock Profile', 'enabled': True, 'position': 0},
            {'id': 'p2', 'title': 'Classical', 'enabled': False, 'position': 1},
        ]
        self.config.profiles['user_profile_settings'] = {
            'p1': {'rename_files': True},
            'p2': {'rename_files': False},
        }

    @patch('picard.profiles.cli.get_config')
    def test_cmd_list_no_profiles(self, mock_get_config):
        mock_get_config.return_value = self.config
        self.config.profiles['user_profiles'] = []

        output, stdout, stderr = _make_output()
        exit_code = cmd_list(output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('No profiles', stdout.getvalue())

    @patch('picard.profiles.cli.get_config')
    def test_cmd_list_with_profiles(self, mock_get_config):
        mock_get_config.return_value = self.config
        self._setup_profiles()

        output, stdout, stderr = _make_output()
        exit_code = cmd_list(output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        out = stdout.getvalue()
        self.assertIn('My Rock Profile', out)
        self.assertIn('enabled', out)
        self.assertIn('Classical', out)
        self.assertIn('disabled', out)

    @patch('picard.profiles.cli.get_config')
    def test_cmd_export_to_stdout(self, mock_get_config):
        mock_get_config.return_value = self.config
        self._setup_profiles()

        args = SimpleNamespace(profile='My Rock Profile', output=None, mode='share')
        output, stdout, stderr = _make_output()
        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            exit_code = cmd_export(args, output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        # When output=None, export prints to sys.stdout directly
        out = mock_out.getvalue()
        self.assertIn('[profile]', out)
        self.assertIn('My Rock Profile', out)
        self.assertIn('rename_files', out)

    @patch('picard.profiles.cli.get_config')
    def test_cmd_export_to_file(self, mock_get_config):
        mock_get_config.return_value = self.config
        self._setup_profiles()

        output_file = os.path.join(self.tmp_directory, 'test-export.toml')
        args = SimpleNamespace(profile='My Rock Profile', output=output_file, mode='share')
        output, stdout, stderr = _make_output()
        exit_code = cmd_export(args, output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('[profile]', content)
        self.assertIn('My Rock Profile', content)

    @patch('picard.profiles.cli.get_config')
    def test_cmd_export_profile_not_found(self, mock_get_config):
        mock_get_config.return_value = self.config
        self._setup_profiles()

        args = SimpleNamespace(profile='Nonexistent', output=None, mode='share')
        output, stdout, stderr = _make_output()
        exit_code = cmd_export(args, output)

        self.assertEqual(exit_code, ExitCode.NOT_FOUND)
        self.assertIn('No profile found', stderr.getvalue())

    @patch('picard.profiles.cli.get_config')
    def test_cmd_import_from_file(self, mock_get_config):
        mock_get_config.return_value = self.config
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)

        # Write a TOML file to import
        toml_file = os.path.join(self.tmp_directory, 'import-test.toml')
        with open(toml_file, 'w', encoding='utf-8') as f:
            f.write('[profile]\ntitle = "Imported"\npicard_version = "3.0.0"\n\n[settings]\nrename_files = true\n')

        args = SimpleNamespace(file=toml_file, enable=False, replace=None)
        output, stdout, stderr = _make_output()
        exit_code = cmd_import(args, output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('Imported', stdout.getvalue())

        # Verify profile was created
        profiles = self.config.profiles['user_profiles']
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]['title'], 'Imported')
        self.assertFalse(profiles[0]['enabled'])

    @patch('picard.profiles.cli.get_config')
    def test_cmd_import_with_enable(self, mock_get_config):
        mock_get_config.return_value = self.config

        toml_file = os.path.join(self.tmp_directory, 'import-test.toml')
        with open(toml_file, 'w', encoding='utf-8') as f:
            f.write('[profile]\ntitle = "Enabled"\npicard_version = "3.0.0"\n')

        args = SimpleNamespace(file=toml_file, enable=True, replace=None)
        output, stdout, stderr = _make_output()
        exit_code = cmd_import(args, output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        profiles = self.config.profiles['user_profiles']
        self.assertTrue(profiles[0]['enabled'])

    @patch('picard.profiles.cli.get_config')
    def test_cmd_import_file_not_found(self, mock_get_config):
        mock_get_config.return_value = self.config

        args = SimpleNamespace(file='/nonexistent/path.toml', enable=False, replace=None)
        output, stdout, stderr = _make_output()
        exit_code = cmd_import(args, output)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Cannot read file', stderr.getvalue())

    @patch('picard.profiles.cli.get_config')
    def test_cmd_import_invalid_toml(self, mock_get_config):
        mock_get_config.return_value = self.config

        toml_file = os.path.join(self.tmp_directory, 'bad.toml')
        with open(toml_file, 'w', encoding='utf-8') as f:
            f.write('not valid [[ toml')

        args = SimpleNamespace(file=toml_file, enable=False, replace=None)
        output, stdout, stderr = _make_output()
        exit_code = cmd_import(args, output)

        self.assertEqual(exit_code, ExitCode.ERROR)
        self.assertIn('Invalid TOML', stderr.getvalue())

    @patch('picard.profiles.cli.get_config')
    def test_cmd_export_backup_mode(self, mock_get_config):
        mock_get_config.return_value = self.config
        TextOption('setting', 'proxy_password', '', title="Password", in_profile=True, shareable=False)
        self.config.profiles['user_profiles'] = [
            {'id': 'p1', 'title': 'Backup Test', 'enabled': True, 'position': 0},
        ]
        self.config.profiles['user_profile_settings'] = {
            'p1': {'proxy_password': 'secret'},
        }

        args = SimpleNamespace(profile='Backup Test', output=None, mode='backup')
        output, stdout, stderr = _make_output()
        with patch('sys.stdout', new_callable=StringIO) as mock_out:
            exit_code = cmd_export(args, output)

        self.assertEqual(exit_code, ExitCode.SUCCESS)
        self.assertIn('secret', mock_out.getvalue())

    @patch('picard.profiles.cli.get_config')
    def test_cmd_import_round_trip(self, mock_get_config):
        """Test that export → import produces a valid profile."""
        mock_get_config.return_value = self.config
        BoolOption('setting', 'rename_files', False, title="Rename", in_profile=True)
        self.config.profiles['user_profiles'] = [
            {'id': 'p1', 'title': 'Original', 'enabled': True, 'position': 0},
        ]
        self.config.profiles['user_profile_settings'] = {
            'p1': {'rename_files': True},
        }

        # Export
        output_file = os.path.join(self.tmp_directory, 'roundtrip.toml')
        export_args = SimpleNamespace(profile='Original', output=output_file, mode='share')
        output, stdout, stderr = _make_output()
        cmd_export(export_args, output)

        # Import
        import_args = SimpleNamespace(file=output_file, enable=False, replace=None)
        output2, stdout2, stderr2 = _make_output()
        cmd_import(import_args, output2)

        # Verify round-trip
        profiles = self.config.profiles['user_profiles']
        self.assertEqual(len(profiles), 2)
        imported = profiles[0]  # New profile inserted at top
        self.assertEqual(imported['title'], 'Original (2)')
        settings = self.config.profiles['user_profile_settings'][imported['id']]
        self.assertTrue(settings['rename_files'])

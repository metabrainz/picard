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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


import argparse
from unittest import TestCase

from picard.cli import (
    SUBCOMMANDS,
    build_root_parser,
)
from picard.cli.subcommand import Subcommand


class TestSubcommandRegistry(TestCase):
    """The CLI subcommand registry must stay explicitly importable.

    PICARD-3478: subcommands used to be referenced by module path strings and
    loaded via importlib, which PyInstaller could not follow, so the packaged
    picard-cli was missing them. They are now Subcommand instances imported
    explicitly. These tests lock in that contract so the registry stays usable
    and discoverable by static tooling.
    """

    def test_registry_is_not_empty(self):
        self.assertTrue(SUBCOMMANDS)

    def test_all_entries_are_subcommand_instances(self):
        for cmd in SUBCOMMANDS:
            self.assertIsInstance(cmd, Subcommand)

    def test_entries_have_unique_names(self):
        names = [cmd.name for cmd in SUBCOMMANDS]
        self.assertEqual(len(names), len(set(names)))

    def test_entries_expose_required_metadata(self):
        for cmd in SUBCOMMANDS:
            with self.subTest(subcommand=cmd.name):
                self.assertTrue(cmd.name)
                self.assertTrue(cmd.help)
                self.assertIsInstance(cmd.examples, tuple)

    def test_setup_parser_does_not_raise(self):
        # Each subcommand must configure its parser without raising. Subcommands
        # with verbs set run_command on their verb subparsers; the top-level
        # fallback run_command is applied later by _register_subcommand().
        for cmd in SUBCOMMANDS:
            with self.subTest(subcommand=cmd.name):
                parser = argparse.ArgumentParser(prog=cmd.name)
                cmd.setup_parser(parser)

    def test_build_root_parser_registers_all_subcommands(self):
        # The root parser must accept every registered subcommand name, and
        # each must have a run_command default so dispatch always has a handler.
        parser = build_root_parser()
        subparser_actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
        self.assertEqual(len(subparser_actions), 1)
        choices = subparser_actions[0].choices
        for cmd in SUBCOMMANDS:
            with self.subTest(subcommand=cmd.name):
                self.assertIn(cmd.name, choices)
                self.assertTrue(callable(choices[cmd.name].get_default('run_command')))

    def test_subcommand_is_abstract(self):
        with self.assertRaises(TypeError):
            Subcommand(name='x', help='x', examples=())  # type: ignore[abstract]

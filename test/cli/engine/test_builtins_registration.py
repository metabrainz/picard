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


"""The built-in commands declared by the modules of picard.cli.engine.builtins."""

from test.picardtestcase import PicardTestCase

from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import EngineCommandRegistry


EXPECTED = {
    'album load',
    'cluster',
    'cluster lookup',
    'disc read',
    'disc read-log',
    'disc read-tags',
    'file add',
    'help',
    'ls',
    'lookup',
    'match',
    'metadata add',
    'metadata rm',
    'metadata rm-value',
    'metadata set',
    'metadata show',
    'move',
    'option get',
    'option ls',
    'option save',
    'option set',
    'option unset',
    'remove',
    'save',
    'scan',
    'trash',
    'tree',
}

DESTRUCTIVE = {'option save', 'trash'}


class BuiltinCommandsTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)

    def test_all_the_commands_are_declared(self):
        self.assertEqual(EXPECTED, set(self.reg.names()))

    def test_each_command_has_help_and_one_completion_kind_per_argument(self):
        for command in self.reg:
            with self.subTest(command=command.name):
                self.assertTrue(command.help)
                self.assertLessEqual(len(command.arg_kinds), len(command.args))

    def test_each_command_explains_how_to_use_it(self):
        for command in self.reg:
            with self.subTest(command=command.name):
                self.assertTrue(command.usage.startswith(command.name), command.usage)
                self.assertTrue(command.description)
                # The description is for the user: no markup of the documentation.
                self.assertNotIn('``', command.description)
                self.assertNotIn(':mod:', command.description)

    def test_the_arguments_of_the_usage_are_those_the_command_declares(self):
        for command in self.reg:
            with self.subTest(command=command.name):
                # A command with arguments says so in its usage, and one without does not.
                self.assertEqual(bool(command.args), command.usage != command.name, command.usage)

    def test_only_commands_that_are_hard_to_undo_are_destructive(self):
        self.assertEqual(DESTRUCTIVE, {command.name for command in self.reg if command.destructive})

    def test_each_registry_gets_its_own_copy_of_the_commands(self):
        other = EngineCommandRegistry()
        register_builtins(other)
        self.assertEqual(self.reg.names(), other.names())
        # Registering twice into the same registry is a mistake, as for any command.
        with self.assertRaises(ValueError):
            register_builtins(other)

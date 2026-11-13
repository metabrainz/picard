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

from test.picardtestcase import PicardTestCase

from picard.cli.engine.commands import (
    EngineCommand,
    EngineCommandRegistry,
)
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)


class EngineResultTest(PicardTestCase):
    def test_defaults(self):
        r = EngineResult()
        self.assertTrue(r.ok)
        self.assertEqual([], r.items)
        self.assertEqual([], r.unresolved)

    def test_failure_factory(self):
        r = EngineResult.failure('boom', unresolved=['a9'])
        self.assertFalse(r.ok)
        self.assertEqual('boom', r.error)
        self.assertEqual(['a9'], r.unresolved)

    def test_to_dict_is_plain_serializable(self):
        r = EngineResult(
            items=[EngineItemResult('a1', 'saved', {'files': 12})],
            resolved=['a1'],
            mints=['a1'],
            message='done',
        )
        d = r.to_dict()
        self.assertEqual(
            d,
            {
                'ok': True,
                'items': [{'handle': 'a1', 'path': '', 'status': 'saved', 'data': {'files': 12}}],
                'resolved': ['a1'],
                'unresolved': [],
                'mints': ['a1'],
                'message': 'done',
                'error': '',
            },
        )
        # Must be JSON-serializable (cross-process / MCP).
        import json

        json.dumps(d)


class EngineCommandTest(PicardTestCase):
    def test_noun_verb_split(self):
        cmd = EngineCommand(name='album save', run=lambda s, a: EngineResult())
        self.assertEqual('album', cmd.noun)
        self.assertEqual('save', cmd.verb)

    def test_single_word_name(self):
        cmd = EngineCommand(name='ls', run=lambda s, a: EngineResult())
        self.assertEqual('ls', cmd.noun)
        self.assertEqual('', cmd.verb)


class EngineCommandRegistryTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()

    def _cmd(self, name):
        return EngineCommand(name=name, run=lambda s, a: EngineResult())

    def test_register_and_get(self):
        cmd = self.reg.register(self._cmd('file add'))
        self.assertIs(self.reg.get('file add'), cmd)
        self.assertIn('file add', self.reg)
        self.assertEqual(1, len(self.reg))

    def test_duplicate_registration_raises(self):
        self.reg.register(self._cmd('file add'))
        with self.assertRaises(ValueError):
            self.reg.register(self._cmd('file add'))

    def test_get_unknown_is_none(self):
        self.assertIsNone(self.reg.get('nope'))

    def test_names_sorted(self):
        self.reg.register(self._cmd('file add'))
        self.reg.register(self._cmd('album save'))
        self.assertEqual(['album save', 'file add'], self.reg.names())

    def test_iterates_over_the_commands_in_registration_order(self):
        first = self.reg.register(self._cmd('file add'))
        second = self.reg.register(self._cmd('album save'))
        self.assertEqual([first, second], list(self.reg))


class CommandDecoratorTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()

    def test_the_command_is_registered_with_what_was_declared(self):
        @self.reg.command(
            'file add',
            help="Load files.",
            args=('paths',),
            arg_kinds=('path',),
            destructive=True,
        )
        def run(session, args):
            return EngineResult()

        cmd = self.reg.get('file add')
        self.assertIs(run, cmd.run)
        self.assertEqual(
            ('Load files.', ('paths',), ('path',), True),
            (cmd.help, cmd.args, cmd.arg_kinds, cmd.destructive),
        )

    def test_defaults_are_those_of_a_command(self):
        @self.reg.command('ls')
        def run(session, args):
            return EngineResult()

        cmd = self.reg.get('ls')
        self.assertEqual(
            ('', (), (), False),
            (cmd.help, cmd.args, cmd.arg_kinds, cmd.destructive),
        )

    def test_usage_and_description_come_from_the_declaration_and_the_docstring(self):
        @self.reg.command('file add', usage='file add <path>...')
        def run(session, args):
            """Load files.

            Directories are walked.
            """
            return EngineResult()

        cmd = self.reg.get('file add')
        self.assertEqual('file add <path>...', cmd.usage)
        self.assertEqual('Load files.\n\nDirectories are walked.', cmd.description)

    def test_usage_defaults_to_the_name_and_description_to_nothing(self):
        @self.reg.command('ls')
        def run(session, args):
            return EngineResult()

        cmd = self.reg.get('ls')
        self.assertEqual(('ls', ''), (cmd.usage, cmd.description))

    def test_the_function_is_returned_unchanged_and_still_callable(self):
        result = EngineResult(message="ran")

        @self.reg.command('ls')
        def run(session, args):
            return result

        self.assertIs(result, run(None, {}))

    def test_a_duplicate_name_raises(self):
        @self.reg.command('ls')
        def first(session, args):
            return EngineResult()

        with self.assertRaises(ValueError):

            @self.reg.command('ls')
            def second(session, args):
                return EngineResult()

        self.assertIs(first, self.reg.get('ls').run)

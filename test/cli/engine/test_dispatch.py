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
    UsageError,
)
from picard.cli.engine.dispatch import (
    _bind_args,
    dispatch,
    find_command,
    split_command_name,
    split_line,
)
from picard.cli.engine.result import EngineResult


class _Session:
    """Minimal EngineSession stand-in for dispatch tests."""

    def __init__(self):
        self.calls = []

    def resolve(self, selector):
        return [], []

    def handle_for(self, entity):
        return 'x1'

    def mint_mark(self):
        return 0

    def minted_since(self, mark):
        return []

    def path_of(self, handle):
        return None

    def path_segments(self, base):
        return []

    def enumerate_prefix(self, prefix):
        return []

    def run_until_idle(self, timeout=None):
        return True


class SplitCommandNameTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        self.reg.register(EngineCommand(name='album save', run=lambda s, a: EngineResult()))
        self.reg.register(EngineCommand(name='ls', run=lambda s, a: EngineResult()))

    def test_two_word_name(self):
        self.assertEqual(('album save', ['a1']), split_command_name(['album', 'save', 'a1'], self.reg))

    def test_one_word_name(self):
        self.assertEqual(('ls', ['a*']), split_command_name(['ls', 'a*'], self.reg))

    def test_unknown_prefers_two_word(self):
        self.assertEqual(('foo bar', []), split_command_name(['foo', 'bar'], self.reg))


class DispatchTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        self.session = _Session()

    def test_unknown_command_is_failure(self):
        r = dispatch(self.session, self.reg, 'bogus thing')
        self.assertFalse(r.ok)
        self.assertIn('unknown command', r.error)

    def test_group_alone_lists_its_commands(self):
        for name in ('album load', 'album versions'):
            self.reg.register(EngineCommand(name=name, run=lambda session, args: EngineResult()))
        r = dispatch(self.session, self.reg, 'album')
        self.assertFalse(r.ok)
        self.assertEqual("album: needs a command: load, versions (see 'help album')", r.error)
        # With something after it, it is still an unknown command.
        self.assertIn('unknown command', dispatch(self.session, self.reg, 'album bogus').error)

    def test_empty_line_is_failure(self):
        self.assertFalse(dispatch(self.session, self.reg, '   ').ok)

    def test_command_exception_becomes_failure(self):
        def boom(session, args):
            raise RuntimeError('kaboom')

        self.reg.register(EngineCommand(name='boom', run=boom))
        r = dispatch(self.session, self.reg, 'boom')
        self.assertFalse(r.ok)
        self.assertIn('kaboom', r.error)

    def test_missing_arguments_are_reported_with_the_usage_of_the_command(self):
        def run(session, args):
            raise UsageError

        self.reg.register(EngineCommand(name='album save', run=run, usage='album save <selector>'))
        result = dispatch(self.session, self.reg, 'album save')
        self.assertFalse(result.ok)
        self.assertEqual("album save: usage: album save <selector> (see 'help album save')", result.error)

    def test_args_bound_and_passed(self):
        captured = {}

        def grab(session, args):
            captured.update(args)
            return EngineResult()

        self.reg.register(EngineCommand(name='file add', run=grab, args=('paths',)))
        dispatch(self.session, self.reg, 'file add a.flac b.flac')
        self.assertEqual(['a.flac', 'b.flac'], captured['paths'])

    def test_single_arg_bound_as_scalar(self):
        captured = {}

        def grab(session, args):
            captured.update(args)
            return EngineResult()

        self.reg.register(EngineCommand(name='ls', run=grab, args=('selector',)))
        dispatch(self.session, self.reg, 'ls a1')
        self.assertEqual('a1', captured['selector'])


class BindArgsTest(PicardTestCase):
    def test_each_value_goes_to_its_arg(self):
        self.assertEqual({'a': 'x', 'b': 'y'}, _bind_args(('a', 'b'), ['x', 'y']))

    def test_missing_values_are_none(self):
        self.assertEqual({'a': 'x', 'b': None}, _bind_args(('a', 'b'), ['x']))
        self.assertEqual({'a': None}, _bind_args(('a',), []))

    def test_the_last_arg_takes_what_is_left(self):
        self.assertEqual({'a': 'x', 'rest': ['y', 'z']}, _bind_args(('a', 'rest'), ['x', 'y', 'z']))
        self.assertEqual({'rest': ['x', 'y']}, _bind_args(('rest',), ['x', 'y']))

    def test_a_single_value_is_not_wrapped_in_a_list(self):
        self.assertEqual({'rest': 'x'}, _bind_args(('rest',), ['x']))

    def test_no_declared_args_binds_nothing(self):
        self.assertEqual({}, _bind_args((), ['x']))


class FindCommandTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        self.album_save = self.reg.register(EngineCommand(name='album save', run=lambda s, a: EngineResult()))
        self.ls = self.reg.register(EngineCommand(name='ls', run=lambda s, a: EngineResult()))

    def test_two_word_and_one_word_commands(self):
        self.assertIs(self.album_save, find_command(self.reg, 'album save a1'))
        self.assertIs(self.ls, find_command(self.reg, 'ls a*'))

    def test_quotes_are_handled_as_by_dispatch(self):
        self.assertIs(self.ls, find_command(self.reg, '"ls" a*'))

    def test_nothing_to_find(self):
        for line in ('', '   ', 'bogus thing', 'ls "unterminated'):
            with self.subTest(line=line):
                self.assertIsNone(find_command(self.reg, line))


class SplitLineTest(PicardTestCase):
    def test_posix_quotes_and_escapes(self):
        self.assertEqual(['file', 'add', 'a b', 'c d'], split_line('file add "a b" c\\ d', posix=True))

    def test_windows_keeps_backslashes_of_paths(self):
        # A backslash is the path separator there, not an escape character.
        self.assertEqual(
            ['file', 'add', 'C:\\Music\\a.flac'],
            split_line('file add C:\\Music\\a.flac', posix=False),
        )

    def test_windows_quotes_group_words_and_are_removed(self):
        self.assertEqual(
            ['file', 'add', 'D:\\My Music\\b.flac', "E:\\x y"],
            split_line('file add "D:\\My Music\\b.flac" \'E:\\x y\'', posix=False),
        )

    def test_windows_unc_path_and_apostrophe_are_literal(self):
        self.assertEqual(
            ['file', 'add', '\\\\server\\share\\a.flac', "C:\\Don't\\b.flac"],
            split_line('file add \\\\server\\share\\a.flac C:\\Don\'t\\b.flac', posix=False),
        )

    def test_windows_backslash_before_a_double_quote_is_a_literal_quote(self):
        self.assertEqual(['t', 'He said "it\'s"'], split_line('t "He said \\"it\'s\\""', posix=False))

    def test_windows_backslashes_before_a_quote_are_halved(self):
        # An even number: half of them, and the quote ends the group. An odd one: a literal quote too.
        self.assertEqual(['t', 'C:\\a b\\'], split_line('t "C:\\a b\\\\"', posix=False))
        self.assertEqual(['t', 'a\\"b'], split_line('t a\\\\\\"b', posix=False))

    def test_windows_single_quotes_group_only_at_the_start_of_a_word(self):
        self.assertEqual(['t', 'Say "hi"', 'a b'], split_line('t \'Say "hi"\' a" "b', posix=False))

    def test_windows_empty_group_is_an_empty_word(self):
        self.assertEqual(['t', ''], split_line('t ""', posix=False))

    def test_windows_adjacent_groups_are_one_word(self):
        self.assertEqual(['t', 'ab c'], split_line('t "a"b" c"', posix=False))

    def test_unbalanced_quote_is_an_error(self):
        for posix in (True, False):
            for line in ('file add "oops', "file add 'oops"):
                with self.subTest(posix=posix, line=line), self.assertRaises(ValueError):
                    split_line(line, posix=posix)

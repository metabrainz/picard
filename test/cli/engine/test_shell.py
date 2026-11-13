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

import io
import os
from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.test_render import _output
from test.picardtestcase import PicardTestCase

from picard import log
from picard.album import Album
from picard.cli.engine.builtins import register_builtins
from picard.cli.engine.commands import (
    EngineCommand,
    EngineCommandRegistry,
)
from picard.cli.engine.dispatch import dispatch
from picard.cli.engine.render import render_result
from picard.cli.engine.result import (
    EngineResult,
)
from picard.cli.engine.session import LocalEngineSession
from picard.cli.output import CliOutput
from picard.cli.shell import (
    History,
    _history_size,
    _prompt,
    run_repl,
    run_system_command,
)
from picard.cli.status import ShellStatus
from picard.const.sys import IS_WIN
from picard.workspace import workspace


class RunReplTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.out, self.buf = _output()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        wks = workspace()
        wks.albums = {'rel-1': Album('rel-1')}

    def _lines(self, *lines):
        it = iter(lines)

        def read_line():
            try:
                return next(it)
            except StopIteration:
                raise EOFError from None

        return read_line

    def test_quit_leaves(self):
        run_repl(self.session, self.reg, self.out, self._lines('quit'))
        # Should return without error; nothing dispatched.
        self.assertNotIn('unknown command', self.buf.getvalue())

    def test_eof_leaves(self):
        run_repl(self.session, self.reg, self.out, self._lines())  # immediate EOF
        # No exception; loop exits cleanly.

    def test_blank_lines_skipped(self):
        run_repl(self.session, self.reg, self.out, self._lines('', '   ', 'quit'))
        self.assertEqual('', self.buf.getvalue().replace('\n', ''))

    def test_help_lists_commands(self):
        run_repl(self.session, self.reg, self.out, self._lines('help', 'quit'))
        text = self.buf.getvalue()
        self.assertIn('ls', text)
        self.assertIn('cluster lookup', text)
        self.assertIn('selectors', text)
        self.assertIn('quit', text)

    def test_help_of_a_command_is_not_followed_by_how_to_leave(self):
        run_repl(self.session, self.reg, self.out, self._lines('help ls', 'quit'))
        self.assertIn('ls [selector]', self.buf.getvalue())
        self.assertNotIn('quit', self.buf.getvalue())

    def test_ls_dispatched_and_rendered(self):
        run_repl(self.session, self.reg, self.out, self._lines('ls', 'quit'))
        # The album handle a1 is minted and rendered.
        self.assertIn('a1', self.buf.getvalue())

    def test_unknown_command_rendered_as_error(self):
        run_repl(self.session, self.reg, self.out, self._lines('bogus thing', 'quit'))
        self.assertIn('unknown command', self.buf.getvalue())

    def test_ctrl_c_at_prompt_cancels_line_and_continues(self):
        # Ctrl-C at the prompt raises KeyboardInterrupt from read_line; the loop
        # must swallow it, return to the prompt, and NOT exit or crash.
        calls = iter([KeyboardInterrupt(), 'ls', 'quit'])

        def read_line():
            value = next(calls)
            if isinstance(value, BaseException):
                raise value
            return value

        run_repl(self.session, self.reg, self.out, read_line)
        # The command after the interrupt still ran (a1 rendered).
        self.assertIn('a1', self.buf.getvalue())

    def test_ctrl_c_during_command_is_caught(self):
        # Ctrl-C while a command runs (dispatch) must abort that command and
        # return to the prompt rather than propagating out of run_repl.
        # KeyboardInterrupt is a BaseException, so dispatch's `except Exception`
        # does not swallow it; run_repl must catch it around dispatch.
        def boom(session, args):
            raise KeyboardInterrupt()

        self.reg.register(EngineCommand(name='hang', run=boom))
        run_repl(self.session, self.reg, self.out, self._lines('hang', 'quit'))
        self.assertIn('interrupted', self.buf.getvalue())

    def _register_destructive(self):
        ran = []

        def wipe(session, args):
            ran.append(args)
            return EngineResult()

        self.reg.register(EngineCommand(name='wipe', run=wipe, destructive=True))
        return ran

    def test_destructive_command_runs_when_confirmed(self):
        ran = self._register_destructive()
        questions = []

        def confirm(question):
            questions.append(question)
            return True

        run_repl(self.session, self.reg, self.out, self._lines('wipe x', 'quit'), confirm=confirm)
        self.assertEqual(1, len(ran))
        self.assertIn('wipe x', questions[0])

    def test_destructive_command_is_cancelled_when_declined(self):
        ran = self._register_destructive()
        run_repl(self.session, self.reg, self.out, self._lines('wipe x', 'quit'), confirm=lambda question: False)
        self.assertEqual([], ran)
        self.assertIn('cancelled', self.buf.getvalue())

    def test_ctrl_c_at_confirmation_cancels_the_command_and_continues(self):
        ran = self._register_destructive()

        def confirm(question):
            raise KeyboardInterrupt

        run_repl(self.session, self.reg, self.out, self._lines('wipe x', 'ls', 'quit'), confirm=confirm)
        self.assertEqual([], ran)
        self.assertIn('cancelled', self.buf.getvalue())
        # The loop went on to the next line.
        self.assertIn('a1', self.buf.getvalue())

    def test_non_destructive_command_is_not_confirmed(self):
        def confirm(question):
            raise AssertionError("must not ask")

        run_repl(self.session, self.reg, self.out, self._lines('ls', 'quit'), confirm=confirm)
        self.assertIn('a1', self.buf.getvalue())

    def test_trash_is_destructive(self):
        self.assertTrue(self.reg.get('trash').destructive)
        self.assertFalse(self.reg.get('remove').destructive)


class SystemCommandTest(PicardTestCase):
    """A line that starts with ! is given as it is to the shell of the system."""

    def setUp(self):
        super().setUp()
        self.out, self.buf = _output()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        self.ran = []

    def _run(self, *lines, status=0):
        it = iter(lines)

        def read_line():
            try:
                return next(it)
            except StopIteration:
                raise EOFError from None

        def system(command):
            self.ran.append(command)
            return status

        run_repl(self.session, self.reg, self.out, read_line, run_system=system)
        return self.buf.getvalue()

    def test_the_rest_of_the_line_is_run_as_it_is(self):
        self._run('!ls -l "/tmp/a b" | wc -l')
        self.assertEqual(['ls -l "/tmp/a b" | wc -l'], self.ran)

    def test_spaces_after_the_mark_do_not_matter(self):
        self._run('!   ls')
        self.assertEqual(['ls'], self.ran)

    def test_it_is_not_an_engine_command(self):
        text = self._run('!ls')
        self.assertNotIn('unknown command', text)

    def test_a_failed_command_says_its_exit_status(self):
        self.assertIn('exit status 3', self._run('!false', status=3))

    def test_a_command_that_succeeds_says_nothing(self):
        self.assertEqual('', self._run('!true').strip())

    def test_a_mark_alone_says_how_to_use_it(self):
        text = self._run('!')
        self.assertEqual([], self.ran)
        self.assertIn('!<command>', text)

    def test_ctrl_c_returns_to_the_prompt(self):
        def system(command):
            raise KeyboardInterrupt

        lines = iter(['!sleep 100', 'ls'])

        def read_line():
            try:
                return next(lines)
            except StopIteration:
                raise EOFError from None

        run_repl(self.session, self.reg, self.out, read_line, run_system=system)
        self.assertIn('interrupted', self.buf.getvalue())

    def test_help_mentions_it(self):
        self.assertIn('!<command>', self._run('help'))


class RunSystemCommandTest(PicardTestCase):
    def test_returns_the_exit_status_of_the_command(self):
        # 'exit 3' means the same to sh and to cmd.exe.
        self.assertEqual(3, run_system_command('exit 3'))
        self.assertEqual(0, run_system_command('exit 0'))


class ChangeDirectoryTest(PicardTestCase):
    """!cd changes the directory of the console, which a shell of its own could not."""

    def setUp(self):
        super().setUp()
        self.out, self.buf = _output()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        self.ran = []
        self.tmp = os.path.realpath(self.mktmpdir())
        self.sub = os.path.join(self.tmp, 'a b')
        os.mkdir(self.sub)
        self.home = os.path.realpath(self.mktmpdir())
        # Registered after the directories, so that it runs before they are
        # removed (cleanups run last first): Windows cannot remove the current
        # directory.
        cwd = os.getcwd()
        environ = {name: os.environ.get(name) for name in ('PWD', 'OLDPWD')}
        self.addCleanup(self._restore_environ, environ)
        self.addCleanup(os.chdir, cwd)

    @staticmethod
    def _restore_environ(environ):
        for name, value in environ.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _run(self, *lines):
        it = iter(lines)

        def read_line():
            try:
                return next(it)
            except StopIteration:
                raise EOFError from None

        def system(command):
            self.ran.append(command)
            return 0

        run_repl(self.session, self.reg, self.out, read_line, run_system=system)
        return self.buf.getvalue()

    def test_cd_changes_the_directory_of_the_console(self):
        self._run(f'!cd {self.tmp}')
        self.assertEqual(self.tmp, os.getcwd())
        self.assertEqual([], self.ran)

    def test_the_directory_is_the_one_of_the_next_commands(self):
        self._run(f'!cd {self.tmp}', '!pwd')
        self.assertEqual(['pwd'], self.ran)
        self.assertEqual(self.tmp, os.getcwd())
        self.assertEqual(self.tmp, os.environ['PWD'])

    def test_a_relative_and_a_quoted_directory(self):
        self._run(f'!cd {self.tmp}', '!cd "a b"')
        self.assertEqual(self.sub, os.getcwd())

    def test_cd_alone_goes_home_and_tilde_is_home(self):
        with patch.dict(os.environ, {'HOME': self.home, 'USERPROFILE': self.home}):
            self._run(f'!cd {self.tmp}', '!cd')
            self.assertEqual(self.home, os.path.realpath(os.getcwd()))
            self._run(f'!cd {self.tmp}', '!cd ~')
            self.assertEqual(self.home, os.path.realpath(os.getcwd()))

    def test_cd_dash_goes_back_and_says_where(self):
        start = os.getcwd()
        text = self._run(f'!cd {self.tmp}', '!cd -')
        self.assertEqual(start, os.getcwd())
        self.assertIn(start, text)

    def test_a_directory_that_does_not_exist_is_reported(self):
        start = os.getcwd()
        text = self._run(f'!cd {os.path.join(self.tmp, "nope")}')
        self.assertEqual(start, os.getcwd())
        self.assertIn('nope', text)

    def test_more_than_a_cd_goes_to_the_shell(self):
        # A cd in a list of commands is the shell's: it cannot change the console's directory.
        start = os.getcwd()
        self._run(f'!cd {self.tmp} && ls')
        self.assertEqual([f'cd {self.tmp} && ls'], self.ran)
        self.assertEqual(start, os.getcwd())


class PromptTest(PicardTestCase):
    def test_prompt_escapes_are_zero_width_for_readline(self):
        prompt = _prompt(CliOutput(stdout=io.StringIO(), color=True))
        self.assertTrue(prompt.startswith('\001'))
        self.assertIn('\002picard> \001', prompt)

    def test_prompt_is_plain_without_color(self):
        self.assertEqual('picard> ', _prompt(CliOutput(stdout=io.StringIO(), color=False)))


class BusyMessageTest(PicardTestCase):
    """What the busy indicator says while a command runs."""

    def setUp(self):
        super().setUp()
        self.out, self.buf = _output()
        self.reg = EngineCommandRegistry()
        self.session = LocalEngineSession(MagicMock())
        self.status = ShellStatus()
        self.messages = []
        # What the command reports while it runs.
        self.reported = None

    def _run(self, status):
        def run(session, args):
            if self.reported:
                self.status.set_statusbar_message(self.reported, echo=None)
            self.messages.append(indicator.call_args.kwargs['message']())
            return EngineResult()

        self.reg.register(EngineCommand(name='slow', run=run))
        lines = iter(['slow'])

        def read_line():
            try:
                return next(lines)
            except StopIteration:
                raise EOFError from None

        with patch('picard.cli.shell.BusyIndicator') as indicator:
            run_repl(self.session, self.reg, self.out, read_line, status=status)

    def test_default_message(self):
        self._run(None)
        self.assertEqual(['working…'], self.messages)

    def test_message_is_what_the_command_declared(self):
        self.session.activity = 'loading release x'
        self._run(None)
        self.assertEqual(['loading release x'], self.messages)

    def test_message_is_the_latest_status_of_the_core(self):
        self.session.activity = 'loading release x'
        self.reported = 'Loading album x …'
        self._run(self.status)
        self.assertEqual(['Loading album x …'], self.messages)

    def test_status_of_the_previous_command_is_forgotten(self):
        self.status.latest = 'from the previous command'
        self.session.activity = 'loading release x'
        self._run(self.status)
        self.assertEqual(['loading release x'], self.messages)


class _FakeReadline:
    """The part of the readline module the history uses."""

    def __init__(self, lines=()):
        self.lines = list(lines)
        self.auto = True
        self.length = None
        self.read_from = None
        self.written_to = None

    def set_auto_history(self, enabled):
        self.auto = enabled

    def set_history_length(self, length):
        self.length = length

    def read_history_file(self, path):
        self.read_from = path
        with open(path) as f:
            self.lines += f.read().splitlines()

    def add_history(self, line):
        self.lines.append(line)

    def get_current_history_length(self):
        return len(self.lines)

    def get_history_item(self, index):
        return self.lines[index - 1]

    def clear_history(self):
        self.lines = []

    def remove_history_item(self, index):
        del self.lines[index]

    def write_history_file(self, path):
        self.written_to = path
        with open(path, 'w') as f:
            f.writelines(line + '\n' for line in self.lines)

    def append_history_file(self, count, path):
        """As readline does: append the last ``count`` lines, then cut the file to the length."""
        self.written_to = path
        with open(path, 'a') as f:
            f.writelines(line + '\n' for line in self.lines[-count:])
        if self.length is not None and self.length >= 0:
            with open(path) as f:
                kept = f.read().splitlines()[-self.length :] if self.length else []
            with open(path, 'w') as f:
                f.writelines(line + '\n' for line in kept)


class HistoryTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.path = os.path.join(self.mktmpdir(), 'shell_history')
        self.readline = _FakeReadline()
        self.history = History(self.readline, self.path, length=50)

    def test_the_file_is_read_and_the_lines_are_added_by_the_history(self):
        self.assertEqual((self.path, False, 50), (self.readline.read_from, self.readline.auto, self.readline.length))

    def test_the_lines_kept(self):
        for line in ('ls', 'ls', '', '   ', ' login secret', 'tree', 'ls'):
            self.history.remember(line)
        self.assertEqual(['ls', 'tree', 'ls'], self.readline.lines)

    def test_a_login_with_the_address_of_the_browser_is_not_kept(self):
        # The address holds the code the browser got from MusicBrainz.
        for line in ("login 'http://127.0.0.1:8000/auth?code=abc&state=xyz'", 'login http://127.0.0.1/auth?code=abc'):
            self.history.remember(line)
        self.history.remember('login')
        self.assertEqual(['login'], self.readline.lines)

    def _file_lines(self):
        with open(self.path) as f:
            return f.read().splitlines()

    def test_consoles_at_the_same_time_keep_the_lines_of_each_other(self):
        # Both start from the same file; as with histappend, each adds its own lines when it ends.
        with open(self.path, 'w') as f:
            f.write('old\n')
        first = History(_FakeReadline(), self.path, length=50)
        second = History(_FakeReadline(), self.path, length=50)
        first.remember('ls')
        second.remember('tree')
        second.save()
        first.save()
        self.assertEqual(['old', 'tree', 'ls'], self._file_lines())

    def test_the_file_is_cut_to_the_length_oldest_first(self):
        history = History(self.readline, self.path, length=2)
        for line in ('a', 'b', 'c'):
            history.remember(line)
        history.save()
        self.assertEqual(['b', 'c'], self._file_lines())

    def test_a_session_with_no_line_kept_leaves_the_file_alone(self):
        self.history.save()
        self.assertIsNone(self.readline.written_to)
        self.assertFalse(os.path.exists(self.path))

    def test_saving_twice_does_not_add_the_lines_twice(self):
        self.history.remember('ls')
        self.history.save()
        self.history.save()
        self.assertEqual(['ls'], self._file_lines())

    def test_without_append_the_whole_history_is_written(self):
        readline = _FakeReadline()
        # As some builds of libedit, which have no append.
        readline.append_history_file = None
        history = History(readline, self.path)
        history.remember('ls')
        history.save()
        self.assertEqual(['ls'], self._file_lines())

    def test_the_lines_are_listed_oldest_first(self):
        for line in ('ls', 'tree'):
            self.history.remember(line)
        self.assertEqual(['ls', 'tree'], self.history.lines())

    def test_clear_forgets_the_lines_here_and_in_the_file(self):
        self.history.remember('file add /music/private')
        self.history.save()
        self.history.remember('ls')
        self.history.clear()
        self.assertEqual([], self.history.lines())
        self.assertEqual([], self._file_lines())
        # What this session typed before is not added back when it ends.
        self.history.save()
        self.assertEqual([], self._file_lines())
        self.history.remember('ls')
        self.history.save()
        self.assertEqual(['ls'], self._file_lines())

    def test_clear_without_clear_history_in_readline(self):
        self.readline.clear_history = None
        for line in ('a', 'b', 'c'):
            self.history.remember(line)
        self.history.clear()
        self.assertEqual([], self.history.lines())

    def test_clear_with_no_file_yet(self):
        self.history.remember('ls')
        self.history.clear()
        self.assertFalse(os.path.exists(self.path))

    def test_save_writes_a_file_for_the_user_only(self):
        self.history.remember('ls')
        self.history.save()
        self.assertEqual(self.path, self.readline.written_to)
        if not IS_WIN:
            self.assertEqual(0o600, os.stat(self.path).st_mode & 0o777)

    def test_a_file_that_cannot_be_written_is_logged_not_raised(self):
        # A folder cannot be made under a file.
        open(self.path, 'w').close()
        history = History(self.readline, os.path.join(self.path, 'sub', 'shell_history'))
        history.remember('ls')
        with self.assertLogs(log.main_logger, level='WARNING'):
            history.save()

    def test_a_file_that_cannot_be_read_is_logged_not_raised(self):
        self.readline.read_history_file = MagicMock(side_effect=PermissionError('denied'))
        with self.assertLogs(log.main_logger, level='WARNING'):
            History(self.readline, self.path)

    def test_save_makes_the_folder(self):
        history = History(self.readline, os.path.join(self.path + '.d', 'sub', 'shell_history'))
        history.remember('ls')
        history.save()
        self.assertTrue(os.path.isfile(os.path.join(self.path + '.d', 'sub', 'shell_history')))


class HistorySizeTest(PicardTestCase):
    def test_the_size_comes_from_the_environment(self):
        for value, size in (('', 1000), ('50', 50), (' 0 ', 0), ('-1', -1)):
            with self.subTest(value=value), patch.dict(os.environ, {'PICARD_SHELL_HISTORY_SIZE': value}):
                self.assertEqual(size, _history_size())

    def test_a_size_that_is_not_a_number_is_the_default(self):
        with patch.dict(os.environ, {'PICARD_SHELL_HISTORY_SIZE': 'many'}):
            with self.assertLogs(log.main_logger, level='WARNING'):
                self.assertEqual(1000, _history_size())


class ShellHistoryCommandTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.reg = EngineCommandRegistry()
        register_builtins(self.reg)
        self.session = LocalEngineSession(MagicMock())
        self.readline = _FakeReadline()
        self.session.history = History(self.readline, os.path.join(self.mktmpdir(), 'shell_history'))
        for line in ('file add a.flac', 'cluster', 'cluster lookup'):
            self.session.history.remember(line)

    def _run(self, line):
        return dispatch(self.session, self.reg, line)

    def test_the_lines_are_listed_numbered(self):
        result = self._run('shell history')
        self.assertTrue(result.ok, result.error)
        self.assertEqual(
            [('1', 'file add a.flac'), ('2', 'cluster'), ('3', 'cluster lookup')],
            [(item.handle, item.data['line']) for item in result.items],
        )

    def test_only_the_last_ones(self):
        self.assertEqual(['2', '3'], [item.handle for item in self._run('shell history 2').items])
        self.assertEqual('the history is empty', self._run('shell history 0').message)

    def test_clear(self):
        result = self._run('shell history clear')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('the history is cleared', result.message)
        self.assertEqual([], self.readline.lines)
        self.assertEqual('the history is empty', self._run('shell history').message)

    def test_a_console_without_history(self):
        self.session.history = None
        result = self._run('shell history')
        self.assertFalse(result.ok)
        self.assertIn('keeps no history', result.error)

    def test_usage(self):
        self.assertIn('usage', self._run('shell history many').error)

    def test_rendered_as_a_shell_lists_its_history(self):
        for line in [f'line {n}' for n in range(4, 11)]:
            self.session.history.remember(line)
        out, buf = _output()
        render_result(self._run('shell history 3'), out)
        self.assertEqual([' 8  line 8', ' 9  line 9', '10  line 10'], buf.getvalue().splitlines())

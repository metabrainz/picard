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

"""Interactive console for the command engine (picard-cli shell).

A human-oriented REPL over a headless :class:`LocalEngineSession`: read a line,
dispatch it to a command, render the structured result. This is the first
frontend of the command engine (see docs/CommandEngine.md) — primarily for
experimenting with and debugging the engine. Lines use the ``<noun> <verb>``
vocabulary, e.g.::

    picard> file add ~/Music/incoming/*.flac
    picard> cluster
    picard> cluster lookup
    picard> match c1 m2
    picard> save

``help`` lists the commands and explains them; ``quit``/``exit`` (or EOF / Ctrl-D) leaves.
A line that starts with ``!`` is run by the shell of the system, as it is, except
``!cd``, which changes the directory of the console.
"""

from argparse import ArgumentParser
from contextlib import contextmanager
import os
import re
import subprocess

from PyQt6.QtCore import pyqtRemoveInputHook

from picard import log
from picard.cli.base import ExitCode
from picard.cli.busy import BusyIndicator
from picard.cli.engine.completion import ShellCompleter
from picard.cli.engine.dispatch import (
    dispatch,
    find_command,
    split_line,
)
from picard.cli.engine.render import render_result
from picard.cli.status import ShellStatus
from picard.cli.subcommand import Subcommand
from picard.const.appdirs import shell_history_file
from picard.const.sys import IS_WIN
from picard.notification import set_notifier_sink


# Locks the history file while several consoles add their lines to it; not on Windows.
if IS_WIN:
    fcntl = None
else:
    import fcntl


_PROMPT = 'picard> '

# A color escape sequence, as written by CliOutput.
_ANSI_ESCAPE = re.compile(r'\033\[[0-9;]*m')

# What a console has that the engine does not, said after the list of the commands.
_CONSOLE_HELP = (
    "In this console, !<command> runs a command of the system shell, !cd <directory> changes",
    "the directory of the console, and quit or exit (or Ctrl-D) leaves. The up key recalls",
    "the lines typed, also in the previous sessions, except those that start with a space",
    "('shell history' lists them).",
)

# The most lines the history keeps, unless PICARD_SHELL_HISTORY_SIZE says otherwise.
_HISTORY_SIZE = 1000

# Characters that make a line more than a single command for the shell (cd a && ls).
_SHELL_SYNTAX = frozenset('&|;<>`(')


def _holds_secret(line: str) -> bool:
    """Whether ``line`` holds what must not be written to the history file.

    ``login <address>`` is given the address the browser was sent to, which has
    the authorization code of the login in it.
    """
    words = line.split(None, 1)
    return len(words) == 2 and words[0] == 'login'


class History:
    """The lines typed in the console, recalled with the up and down keys, and kept from one session to the next.

    As in a shell, an empty line, one that starts with a space and the same line
    twice in a row are not kept. Several consoles can run at once: as bash does
    with its histappend option, each one appends the lines of its session to the
    file when it ends, rather than writing the whole history it read, so that the
    lines of the others are not lost. ``readline`` is the readline module, given
    so that the history can be tested without a terminal.
    """

    def __init__(self, readline, path: str, length: int = _HISTORY_SIZE):
        self._readline = readline
        self._path = path
        self._last: str | None = None
        # The lines of this session, the ones to append to the file.
        self._added = 0
        # The lines are added here, not by input(), to choose which ones are kept.
        readline.set_auto_history(False)
        readline.set_history_length(length)
        try:
            readline.read_history_file(path)
        except FileNotFoundError:
            pass
        except OSError as e:
            log.warning("Could not read the history of the shell from %s: %s", path, e)

    def remember(self, line: str) -> None:
        """Keep ``line`` in the history, unless it is empty, starts with a space, is the last one again, or holds a secret."""
        if not line.strip() or line[0].isspace() or line == self._last or _holds_secret(line):
            return
        self._readline.add_history(line)
        self._last = line
        self._added += 1

    def lines(self) -> list[str]:
        """The lines, the oldest first."""
        return [
            self._readline.get_history_item(index)
            for index in range(1, self._readline.get_current_history_length() + 1)
        ]

    def clear(self) -> None:
        """Forget the lines, here and in the file, which is emptied under the lock of :meth:`save`."""
        clear_history = getattr(self._readline, 'clear_history', None)
        if clear_history is not None:
            clear_history()
        else:  # not in every build of readline
            for index in reversed(range(self._readline.get_current_history_length())):
                self._readline.remove_history_item(index)
        self._last = None
        self._added = 0
        try:
            with _locked(self._path, create=False) as fd:
                os.ftruncate(fd, 0)
        except FileNotFoundError:
            pass
        except OSError as e:
            log.warning("Could not clear the history of the shell in %s: %s", self._path, e)

    def save(self) -> None:
        """Add the lines of this session to the file, readable by the user only (it can hold paths and addresses).

        The file is then cut to the length of the history, the oldest lines first.
        Without a way to append (some builds of libedit), it is written whole, and
        the last console to end wins, as in bash without histappend.
        """
        if not self._added:
            return
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with _locked(self._path, create=True):
                append = getattr(self._readline, 'append_history_file', None)
                if append is not None:
                    append(self._added, self._path)
                else:
                    self._readline.write_history_file(self._path)
            os.chmod(self._path, 0o600)
            self._added = 0
        except OSError as e:
            log.warning("Could not save the history of the shell to %s: %s", self._path, e)


@contextmanager
def _locked(path: str, create: bool):
    """Open the history file, readable by the user only if it is made, and lock it; give its descriptor.

    The lock keeps out the consoles that add their lines (or clear them) at the
    same time: it is advisory, they all take it. Not on Windows, without fcntl.
    """
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | (os.O_CREAT if create else 0), 0o600)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield fd
    finally:
        os.close(fd)  # and with it the lock


def _history_size() -> int:
    """The most lines the history keeps: PICARD_SHELL_HISTORY_SIZE, 0 for none, a negative number for no limit."""
    text = os.environ.get('PICARD_SHELL_HISTORY_SIZE', '').strip()
    if not text:
        return _HISTORY_SIZE
    try:
        return int(text)
    except ValueError:
        log.warning("PICARD_SHELL_HISTORY_SIZE is not a number: %r, %d lines are kept", text, _HISTORY_SIZE)
        return _HISTORY_SIZE


def _setup_readline(registry, session) -> 'History | None':
    """Enable tab-completion (handles + file paths) and the history if readline is available."""
    # Imported here, not at the top: readline is optional, and importing it
    # changes how input() behaves for every command of picard-cli, not only this one.
    try:
        import readline
    except ImportError:  # e.g. some Windows Pythons without pyreadline
        return None

    completer = ShellCompleter(registry, session, readline.get_line_buffer)
    readline.set_completer(completer.complete)
    # Complete whole tokens: do not break on characters common in paths/handles
    # (default delims include '/', '-', '~', etc. which would split paths).
    readline.set_completer_delims(' \t\n')
    # 'libedit' (macOS) uses a different bind syntax than GNU readline.
    if 'libedit' in getattr(readline, '__doc__', ''):
        readline.parse_and_bind('bind ^I rl_complete')
    else:
        readline.parse_and_bind('tab: complete')
    return History(readline, shell_history_file(), _history_size())


class ShellSubcommand(Subcommand):
    def __init__(self):
        super().__init__(
            name='shell',
            help='interactive command engine console (experimental)',
            examples=('shell',),
        )

    def setup_parser(self, parser: ArgumentParser):
        parser.description = 'Start an interactive console to drive the tagging engine (experimental).'
        parser.set_defaults(run_command=_run_shell)


def _ask_yes_no(question: str) -> bool:
    """Ask ``question`` on the terminal; anything but yes (or EOF) is no."""
    try:
        answer = input(f"{question} [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {'y', 'yes'}


def _prompt(output) -> str:
    """The prompt, colored by the output; readline needs the escapes marked as zero-width to keep the line aligned."""
    return _ANSI_ESCAPE.sub(lambda match: f'\001{match.group()}\002', output.d_input_prompt(_PROMPT))


def _always_yes(question: str) -> bool:
    """Confirm without asking (``--yes``)."""
    return True


def run_system_command(command: str) -> int:
    """Run ``command`` with the shell of the system, on the terminal, and return its exit status.

    The command is given to the shell as it is (pipes, quotes and variables are
    the shell's), with the standard input, output and error of the console.
    """
    # The user typed the command at their own console: running it through the
    # shell, as it is, is the point.
    return subprocess.run(command, shell=True, check=False).returncode


def _cd_target(command: str) -> 'str | None':
    """The directory of a line that is only a ``cd`` (``''`` for home), or None if it is something else."""
    if _SHELL_SYNTAX & set(command):
        return None
    try:
        words = split_line(command)
    except ValueError:
        return None
    if not words or words[0] != 'cd' or len(words) > 2:
        return None
    return words[1] if len(words) == 2 else ''


def _change_directory(target: str, output) -> None:
    """Change the directory of the console, as ``cd`` does in a shell.

    A command run by the shell of the system runs in a shell of its own, which
    cannot change the directory of the console; this one does, so that the
    commands that follow, a relative path given to 'file add' and the completion
    of paths start from there. ``cd`` alone goes home, ``cd -`` back.
    """
    previous = os.getcwd()
    if target == '-':
        directory = os.environ.get('OLDPWD')
        if not directory:
            output.error("cd: no previous directory")
            return
    else:
        directory = os.path.expandvars(os.path.expanduser(target or '~'))
    try:
        os.chdir(directory)
    except OSError as e:
        output.error(f"cd: {directory}: {e.strerror or e}")
        return
    os.environ['OLDPWD'] = previous
    os.environ['PWD'] = os.getcwd()
    if target == '-':
        output.print(os.getcwd())


def _run_system_line(command: str, output, run_system) -> None:
    """Run what follows ``!`` on a line, and say how it ended if it failed."""
    if not command:
        output.warning("usage: !<command>, to run a command of the system shell")
        return
    target = _cd_target(command)
    if target is not None:
        _change_directory(target, output)
        return
    try:
        status = run_system(command)
    except KeyboardInterrupt:
        # The command got the Ctrl-C too, as in a shell; back to the prompt.
        output.nl()
        output.warning("interrupted")
        return
    except OSError as e:
        output.error(f"could not run the command: {e}")
        return
    if status:
        output.warning(f"exit status {status}")


def run_repl(
    session,
    registry,
    output,
    read_line,
    confirm=_ask_yes_no,
    run_system=run_system_command,
    status=None,
) -> None:
    """Run the read-dispatch-render loop.

    ``read_line`` is a callable returning the next input line, or raising
    EOFError at end of input. ``confirm`` is called with a question before a
    destructive command (see ``EngineCommand.destructive``) and returns whether
    to go ahead. ``run_system`` runs the command of a line that starts with ``!``
    and returns its exit status. They are factored out so the loop can be driven
    by scripted input in tests (not only an interactive terminal).

    ``status`` (a :class:`~picard.cli.status.ShellStatus`) holds the latest
    status message of the core, shown next to the busy indicator while a command
    runs; without one (no message ever comes in), the indicator says what the
    command declared it waits for.
    """
    status = status or ShellStatus()

    def busy_message() -> str:
        return status.latest or session.activity or 'working…'

    while True:
        try:
            line = read_line()
        except EOFError:
            # Ctrl-D at the prompt: leave the shell.
            output.nl()
            return
        except KeyboardInterrupt:
            # Ctrl-C cancels the current line and returns to a fresh prompt
            # (as in the Python REPL / psql), rather than crashing with a
            # traceback. Use quit/exit or Ctrl-D to leave.
            output.nl()
            continue
        line = line.strip()
        if not line:
            continue
        if line.startswith('!'):
            _run_system_line(line[1:].strip(), output, run_system)
            continue
        head = line.split(None, 1)[0]
        if head in {'quit', 'exit'}:
            return
        command = find_command(registry, line)
        if command is not None and command.destructive:
            try:
                confirmed = confirm(f"'{command.name}' is destructive. Run '{line}'?")
            except KeyboardInterrupt:
                # Ctrl-C at the question is an answer: no.
                output.nl()
                confirmed = False
            if not confirmed:
                output.warning("cancelled")
                continue
        status.reset()
        try:
            with BusyIndicator(output, message=busy_message):
                result = dispatch(session, registry, line)
        except KeyboardInterrupt:
            # Ctrl-C during a running command (e.g. a lookup pumping the event
            # loop) aborts that command and returns to the prompt.
            output.nl()
            output.warning("interrupted")
            continue
        render_result(result, output, minted_max=session.settings.limit('minted_max'))
        if result.ok and line.split() == ['help']:
            # The commands that only make sense in a console are not the engine's.
            for text in _CONSOLE_HELP:
                output.print(output.dim(text))


def _run_shell(args):
    from picard.cli._bootstrap import (
        init_logging,
        is_color_disabled,
    )
    from picard.cli.engine.builtins import register_builtins
    from picard.cli.engine.commands import EngineCommandRegistry
    from picard.cli.engine.session import LocalEngineSession
    from picard.cli.headless import HeadlessTagger
    from picard.cli.output import CliOutput

    config_file = getattr(args, 'config_file', None)
    app = HeadlessTagger([], config_file=config_file)
    # PyQt hooks input() to run the Qt event loop while it waits, and with that hook
    # a Ctrl-C does not interrupt the prompt until the next line is read. The
    # event loop is pumped by the commands (run_until_idle), not by the prompt.
    pyqtRemoveInputHook()
    init_logging(args)
    output = CliOutput(color=False if is_color_disabled(args) else None)

    registry = EngineCommandRegistry()
    register_builtins(registry)
    session = LocalEngineSession(app)

    history = _setup_readline(registry, session)
    session.history = history

    output.print(output.dim("Picard engine shell — type 'help', 'quit' to exit."))

    def read_line():
        line = input(_prompt(output))
        if history is not None:
            history.remember(line)
        return line

    # --yes skips the confirmation of destructive commands
    confirm = _always_yes if getattr(args, 'yes', False) else _ask_yes_no

    # The status messages of the core ("Loading album … …"), shown while a command runs.
    status = ShellStatus()
    set_notifier_sink(status)
    try:
        run_repl(session, registry, output, read_line, confirm=confirm, status=status)
    finally:
        if history is not None:
            history.save()
        set_notifier_sink(None)
        app.run_cleanup()
    return ExitCode.SUCCESS

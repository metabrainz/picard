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
import os
import subprocess

from PyQt6.QtCore import pyqtRemoveInputHook

from picard.cli.base import ExitCode
from picard.cli.engine.completion import ShellCompleter
from picard.cli.engine.dispatch import (
    dispatch,
    find_command,
    split_line,
)
from picard.cli.engine.render import render_result
from picard.cli.subcommand import Subcommand


_PROMPT = 'picard> '

# What a console has that the engine does not, said after the list of the commands.
_CONSOLE_HELP = (
    "In this console, !<command> runs a command of the system shell, !cd <directory> changes",
    "the directory of the console, and quit or exit (or Ctrl-D) leaves.",
)

# Characters that make a line more than a single command for the shell (cd a && ls).
_SHELL_SYNTAX = frozenset('&|;<>`(')


def _setup_readline(registry, session) -> None:
    """Enable tab-completion (handles + file paths) if readline is available."""
    # Imported here, not at the top: readline is optional, and importing it
    # changes how input() behaves for every command of picard-cli, not only this one.
    try:
        import readline
    except ImportError:  # e.g. some Windows Pythons without pyreadline
        return

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
) -> None:
    """Run the read-dispatch-render loop.

    ``read_line`` is a callable returning the next input line, or raising
    EOFError at end of input. ``confirm`` is called with a question before a
    destructive command (see ``EngineCommand.destructive``) and returns whether
    to go ahead. ``run_system`` runs the command of a line that starts with ``!``
    and returns its exit status. They are factored out so the loop can be driven
    by scripted input in tests (not only an interactive terminal).
    """
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
            if not confirm(f"'{command.name}' is destructive. Run '{line}'?"):
                output.warning("cancelled")
                continue
        try:
            result = dispatch(session, registry, line)
        except KeyboardInterrupt:
            # Ctrl-C during a running command (e.g. a lookup pumping the event
            # loop) aborts that command and returns to the prompt.
            output.nl()
            output.warning("interrupted")
            continue
        render_result(result, output)
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

    _setup_readline(registry, session)

    output.print(output.dim("Picard engine shell — type 'help', 'quit' to exit."))

    def read_line():
        return input(_PROMPT)

    # --yes skips the confirmation of destructive commands
    confirm = _always_yes if getattr(args, 'yes', False) else _ask_yes_no

    try:
        run_repl(session, registry, output, read_line, confirm=confirm)
    finally:
        app.run_cleanup()
    return ExitCode.SUCCESS

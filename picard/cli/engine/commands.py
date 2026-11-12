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

"""Command declarations, the command registry, and the session interface.

A command is declared ONCE (:class:`EngineCommand`) with a ``noun verb`` name
and a ``run`` callable. Both frontends (console REPL, MCP) read the same
registry, so there is one vocabulary.

:class:`EngineSession` is the INTERFACE commands run against. Commands are
written against this protocol and do not know whether they run in-process
(``LocalEngineSession``, headless) or against a running GUI over a transport (a
future ``RemoteEngineSession``). Keeping it a Protocol now is the single
concession to that two-backend future.

See ``docs/CommandEngine.md``.
"""

from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Sequence,
)
from dataclasses import (
    dataclass,
    field,
)
import inspect
from typing import (
    Any,
    Protocol,
    runtime_checkable,
)

from picard.cli.engine.result import EngineResult
from picard.cli.engine.settings import ConsoleSettings


class ConsoleHistory(Protocol):
    """The lines typed in a console, for ``shell history``: given by a frontend that keeps them."""

    def lines(self) -> list[str]:
        """The lines, the oldest first."""
        ...

    def clear(self) -> None:
        """Forget the lines, in the console and in the file they are kept in."""
        ...


class UsageError(Exception):
    """A command was not given what it needs.

    A command raises it instead of describing the usage itself: the dispatcher
    reports it with the usage declared by the command, so that there is one copy.
    """


@runtime_checkable
class EngineSession(Protocol):
    """What a command is handed to do its work.

    Implemented in-process by ``LocalEngineSession`` (headless); a future
    ``RemoteEngineSession`` satisfies the same protocol by proxying to a running
    GUI. Commands depend only on this surface, never on a concrete tagger.

    ``activity`` says what the command that is running waits for ("loading
    release ...", or None when it has nothing more to say than that it works):
    a frontend can show it while the command runs.
    """

    activity: 'str | None'

    # The settings of the console (``shell set``): limits that commands and frontends read.
    settings: ConsoleSettings

    # The lines typed (``shell history``), or None if the frontend keeps none.
    history: 'ConsoleHistory | None'

    def resolve(self, selector: 'str | Sequence[str]') -> 'tuple[list[Any], list[str]]':
        """Resolve a selector to ``(entities, unresolved_tokens)``.

        ``selector`` is a string, or the words a command line split it into
        (``a1, c2`` arrives as ``['a1,', 'c2']``).
        """
        ...

    def resolve_targets(self, selector: str) -> list[Any]:
        """Resolve one selector term to the places it names, unexpanded (``u`` stays a bucket)."""
        ...

    def handle_for(self, entity: Any) -> str:
        """Return (minting if needed) the session handle for ``entity``."""
        ...

    def option_names(self) -> 'list[str]':
        """The names of all the options, sorted, for completion."""
        ...

    def list_options(self, pattern: 'str | None' = None) -> 'list[dict[str, Any]]':
        """Describe the options matching ``pattern`` (all those not at their default without one)."""
        ...

    def describe_option(self, name: str) -> 'dict[str, Any]':
        """Describe one option: value, default, type, title and where the value comes from."""
        ...

    def set_option(self, name: str, text: str) -> 'dict[str, Any]':
        """Set an option for this session only, from its text form; describe it."""
        ...

    def unset_option(self, name: str) -> 'dict[str, Any]':
        """Forget the session's value of an option; describe it."""
        ...

    def save_options(self, names: 'list[str] | None' = None) -> 'list[dict[str, Any]]':
        """Write the options set in this session (or just ``names``) to the configuration."""
        ...

    def remint(self, kind: str) -> int:
        """Mint the handles of ``kind`` (``f``, ``c``, ...) from 1 again if none is left; return how many are."""
        ...

    def mint_mark(self) -> int:
        """A mark of the handles minted so far, for ``minted_since``."""
        ...

    def minted_since(self, mark: int) -> 'list[str]':
        """The handles minted after ``mark``, in order."""
        ...

    def path_of(self, handle: str) -> 'str | None':
        """Where the entity of ``handle`` currently sits, as a selector path (or None)."""
        ...

    def path_segments(self, base: str) -> 'list[str]':
        """The path segments that can follow ``base`` (``a1`` -> ``d*``, ``t*``, ...), for completion."""
        ...

    def enumerate_prefix(self, prefix: str) -> Iterable[Any]:
        """Yield the live entities of a handle prefix (for wildcards / ls)."""
        ...

    def set_candidates(self, target: Any, candidates: list[Any]) -> list[str]:
        """Replace the lookup candidates for ``target``; return their handles."""
        ...

    def candidates_for(self, target: Any) -> list[Any]:
        """Return the current candidates held for ``target`` (may be empty)."""
        ...

    def set_versions(self, album: Any, versions: list[Any]) -> list[str]:
        """Replace the release versions held for ``album``; return their handles."""
        ...

    def versions_for(self, album: Any) -> list[Any]:
        """Return the current release versions held for ``album`` (may be empty)."""
        ...

    def version_owner(self, version: Any) -> Any:
        """The album ``version`` was listed for, or None if it is no longer held."""
        ...

    def run_until_idle(self, timeout: float | None = None) -> bool:
        """Drain async work (thread pools, pending requests) to completion."""
        ...


# A command's implementation: given the session and parsed args, return a
# result. It must not print or touch transport.
CommandFunc = Callable[[EngineSession, 'dict[str, Any]'], EngineResult]


@dataclass(frozen=True)
class EngineCommand:
    """A single declared command.

    ``name`` is the full ``noun verb`` (e.g. ``"album save"``). ``run`` receives
    the session and a dict of parsed arguments and returns an EngineResult.
    """

    name: str
    run: CommandFunc
    # One line, for the list of commands.
    help: str = ''
    # How to write the command, ``name`` followed by its arguments: ``<x>`` is
    # required, ``[x]`` optional, ``x...`` repeatable.
    usage: str = ''
    # What ``help <command>`` shows: plain text for the user, with the details
    # and examples. The decorator takes it from the docstring of the function.
    description: str = ''
    # Names of positional args this command expects, for frontends to parse/
    # document. Kept as simple strings; there is no typed-parameter layer.
    args: tuple[str, ...] = field(default_factory=tuple)
    # Completion hint per positional arg, parallel to ``args``: one of
    # 'path' (filesystem path), 'device' (CD/DVD drive), 'selector' (handle
    # selector / wildcard), 'handle' (a single handle), 'tag' (tag name),
    # 'option' (option name), 'option-value' (value of the option named by the
    # previous word), 'setting' (setting of the console), 'handle-kind' (prefix
    # of handles), 'history' (what 'shell history' does), or '' (no completion). Used by the shell's tab-completer.
    # Missing entries default to no completion.
    arg_kinds: tuple[str, ...] = field(default_factory=tuple)
    # True for a command whose effect on disk is hard to undo (e.g. ``trash``).
    # The engine itself never prompts; an interactive frontend should ask for
    # confirmation before running such a command, and an automated one can apply
    # its own policy.
    destructive: bool = False

    def arg_kind(self, index: int) -> str:
        """Completion kind for the word at ``index`` (''/unknown).

        The last declared arg absorbs every remaining word (see the dispatcher),
        so its kind applies to all the words from there on: ``file add a b <TAB>``
        still completes a path, and ``move f1 f2 <TAB>`` a selector.
        """
        if index < 0 or not self.arg_kinds:
            return ''
        return self.arg_kinds[min(index, len(self.arg_kinds) - 1)]

    @property
    def noun(self) -> str:
        return self.name.split(' ', 1)[0]

    @property
    def verb(self) -> str:
        parts = self.name.split(' ', 1)
        return parts[1] if len(parts) > 1 else ''


class EngineCommandRegistry:
    """Holds the declared commands; both frontends read it."""

    def __init__(self):
        self._commands: dict[str, EngineCommand] = {}

    def register(self, command: EngineCommand) -> EngineCommand:
        """Register ``command``. Raises ValueError on a duplicate name."""
        if command.name in self._commands:
            raise ValueError(f"command already registered: {command.name!r}")
        self._commands[command.name] = command
        return command

    def command(
        self,
        name: str,
        *,
        help: str = '',
        usage: str = '',
        args: tuple[str, ...] = (),
        arg_kinds: tuple[str, ...] = (),
        destructive: bool = False,
    ) -> Callable[[CommandFunc], CommandFunc]:
        """Return a decorator declaring the decorated function as the command ``name``.

        The command is registered here when the decorator is applied, so it is
        declared next to its implementation, and the function itself is returned
        unchanged. Its docstring is the description ``help`` shows, so it is
        written for the user::

            @registry.command('file add', help="Load files.", usage='file add <path>...',
                              args=('paths',), arg_kinds=('path',))
            def file_add(session, args):
                # The docstring here is the text of 'help file add'.
                ...

        Raises ValueError on a duplicate name, like :meth:`register`.
        """

        def decorator(run: CommandFunc) -> CommandFunc:
            self.register(
                EngineCommand(
                    name=name,
                    run=run,
                    help=help,
                    usage=usage or name,
                    description=inspect.getdoc(run) or '',
                    args=args,
                    arg_kinds=arg_kinds,
                    destructive=destructive,
                )
            )
            return run

        return decorator

    def get(self, name: str) -> 'EngineCommand | None':
        return self._commands.get(name)

    def names(self) -> list[str]:
        """Registered command names, sorted."""
        return sorted(self._commands)

    def __iter__(self) -> Iterator[EngineCommand]:
        """Iterate over the registered commands, in registration order."""
        return iter(self._commands.values())

    def __contains__(self, name: str) -> bool:
        return name in self._commands

    def __len__(self) -> int:
        return len(self._commands)

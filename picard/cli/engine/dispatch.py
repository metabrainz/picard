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

"""Turn a command line into a command invocation.

A frontend (console REPL or MCP) hands :func:`dispatch` a raw command line, the
registry, and the session. Dispatch resolves the ``noun verb`` name, parses the
remaining tokens into the command's declared positional args, and runs it —
always returning an :class:`~picard.cli.engine.result.EngineResult` (never
raising to the frontend).

Argument parsing is intentionally minimal: a ``shlex`` split (:func:`split_line`)
into the declared positional ``args``, with the last arg soaking up the remainder. The command
contract (positional ``args``) leaves room for a typed param / flag layer to be
added without changing call sites.
"""

import shlex

from picard import log
from picard.cli.engine.commands import (
    EngineCommand,
    EngineCommandRegistry,
    EngineSession,
    UsageError,
)
from picard.cli.engine.result import EngineResult
from picard.cli.engine.selectors import SelectorError
from picard.const.sys import IS_WIN


def split_line(line: str, posix: 'bool | None' = None) -> list[str]:
    """Split a command line into words, honouring quotes.

    The backslash is an escape character in POSIX mode. On Windows it is the
    path separator (``C:\\Music\\a.flac`` must stay as typed), so the line is
    split in non-POSIX mode there, where quotes group words but are kept in the
    words and have to be removed. ``posix`` defaults to the platform's choice.

    Raises :class:`ValueError` on an unbalanced quote.
    """
    if posix is None:
        posix = not IS_WIN
    words = shlex.split(line, posix=posix)
    if posix:
        return words
    return [word[1:-1] if len(word) >= 2 and word[0] == word[-1] and word[0] in {'"', "'"} else word for word in words]


def split_command_name(tokens: list[str], registry: EngineCommandRegistry) -> 'tuple[str, list[str]]':
    """Split tokens into (command-name, remaining-args).

    Tries a two-word ``noun verb`` name first, then a one-word name, so both
    ``album save`` and ``ls`` resolve. Returns the longest matching registered
    name; if none matches, returns the best guess (two-word if two+ tokens)
    so the caller can report "unknown command".
    """
    if len(tokens) >= 2:
        two = f"{tokens[0]} {tokens[1]}"
        if two in registry:
            return two, tokens[2:]
    if tokens:
        one = tokens[0]
        if one in registry:
            return one, tokens[1:]
    # No match: prefer the two-word form for the error message when possible.
    if len(tokens) >= 2:
        return f"{tokens[0]} {tokens[1]}", tokens[2:]
    return (tokens[0], []) if tokens else ('', [])


def find_command(registry: EngineCommandRegistry, line: str) -> 'EngineCommand | None':
    """Return the registered command ``line`` would run, or None.

    None also when the line is empty or cannot be tokenized: :func:`dispatch`
    reports those.
    """
    try:
        tokens = split_line(line)
    except ValueError:
        return None
    if not tokens:
        return None
    name, _rest = split_command_name(tokens, registry)
    return registry.get(name)


def dispatch(session: EngineSession, registry: EngineCommandRegistry, line: str) -> EngineResult:
    """Parse ``line`` and run the matching command against ``session``."""
    try:
        tokens = split_line(line)
    except ValueError as e:
        return EngineResult.failure(f"could not parse command line: {e}")
    if not tokens:
        return EngineResult.failure("empty command")

    name, rest = split_command_name(tokens, registry)
    command = registry.get(name)
    if command is None:
        return EngineResult.failure(f"unknown command: {name!r}")

    args = _bind_args(command.args, rest)
    try:
        result = command.run(session, args)
    except UsageError:
        return EngineResult.failure(f"{name}: usage: {command.usage} (see 'help {name}')")
    except SelectorError as e:
        # The user's selector is at fault (malformed, ambiguous, ...), not the command.
        return EngineResult.failure(f"{name}: invalid selector: {e}")
    except Exception as e:  # a command bug must not crash the frontend
        return EngineResult.failure(f"command {name!r} failed: {e}")
    _add_paths(session, result)
    return result


def _add_paths(session: EngineSession, result: EngineResult) -> None:
    """Fill in where each reported entity currently sits (``EngineItemResult.path``).

    The command has already run, so a failure here must not turn its outcome
    into an error: an item is simply left without a path.
    """
    for item in result.items:
        if not item.handle or item.path:
            continue
        try:
            item.path = session.path_of(item.handle) or ''
        except Exception as e:
            log.debug("Could not work out the path of %r: %s", item.handle, e)


def _bind_args(names: tuple[str, ...], values: list[str]) -> 'dict[str, object]':
    """Bind positional ``values`` to declared ``names``.

    A missing arg binds to None. The last declared arg soaks up all the remaining
    values (so ``file add`` can take many paths): None if there is none, the
    value itself if there is one, else the list of them.
    """
    if not names:
        return {}
    *leading, last = names
    bound: dict[str, object] = {name: values[i] if i < len(values) else None for i, name in enumerate(leading)}
    remainder = values[len(leading) :]
    bound[last] = remainder[0] if len(remainder) == 1 else (remainder or None)
    return bound

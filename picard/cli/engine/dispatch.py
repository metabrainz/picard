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


def _split_windows(line: str) -> list[str]:
    """Split a command line into words by the rules of Windows, where a backslash is a path separator.

    A backslash is literal, so ``C:\\Music\\a.flac`` and ``\\\\server\\share`` stay as typed,
    unless it comes right before a double quote: ``\\"`` is a literal quote
    (and ``\\\\"`` a backslash followed by a quote that begins or ends a group), as
    for the command line of a program. Double quotes group words and are removed.
    A word that begins with a single quote is a group up to the next one, in
    which nothing is special; elsewhere a single quote is an apostrophe.

    Raises :class:`ValueError` on an unbalanced quote.
    """
    words: list[str] = []
    word: list[str] = []
    started = False  # an empty group ("") is a word
    in_double = in_single = False
    i = 0
    while i < len(line):
        char = line[i]
        if in_single:
            if char == "'":
                in_single = False
            else:
                word.append(char)
        elif char == '\\':
            end = i
            while end < len(line) and line[end] == '\\':
                end += 1
            count = end - i
            started = True
            if end < len(line) and line[end] == '"':
                word.append('\\' * (count // 2))
                if count % 2:
                    word.append('"')
                    end += 1
                # An even count leaves the quote to begin or end a group.
            else:
                word.append('\\' * count)
            i = end
            continue
        elif char == '"':
            in_double = not in_double
            started = True
        elif char == "'" and not in_double and not started:
            in_single = started = True
        elif char.isspace() and not in_double:
            if started:
                words.append(''.join(word))
                word, started = [], False
        else:
            word.append(char)
            started = True
        i += 1
    if in_double or in_single:
        raise ValueError("No closing quotation")
    if started:
        words.append(''.join(word))
    return words


def split_line(line: str, posix: 'bool | None' = None) -> list[str]:
    """Split a command line into words, honouring quotes.

    The backslash is an escape character in POSIX mode. On Windows it is the
    path separator (``C:\\Music\\a.flac`` must stay as typed), so the rules of
    Windows apply there (see :func:`_split_windows`). The same rules apply to
    every argument, whether it is a path or the value of a tag. ``posix``
    defaults to the platform's choice.

    Raises :class:`ValueError` on an unbalanced quote.
    """
    if posix is None:
        posix = not IS_WIN
    if posix:
        return shlex.split(line, posix=True)
    return _split_windows(line)


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
        verbs = sorted(c.verb for c in registry if c.noun == name and c.verb)
        if verbs and not rest:
            # A group on its own ('album'): say what can follow, rather than "unknown".
            return EngineResult.failure(f"{name}: needs a command: {', '.join(verbs)} (see 'help {name}')")
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

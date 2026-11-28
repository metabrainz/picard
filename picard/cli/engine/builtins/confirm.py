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

"""The commands that control the confirmations of the console: ``confirm ls``, ``on``, ``off`` and ``save``."""

import difflib
from typing import Any

from picard.cli.engine.builtins.helpers import arg_words
from picard.cli.engine.builtins.registry import (
    BUILTIN_COMMANDS,
    command,
)
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.confirmations import confirmation_keys
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)


# The word of 'confirm on' and 'confirm off' that stands for every confirmation.
ALL_KEYS = 'all'


def _confirmation_item(session: EngineSession, key: str, commands: list[str]) -> EngineItemResult:
    """A result item for a confirmation: its key is the handle, where its state comes from the status."""
    return EngineItemResult(
        handle=key,
        status=session.confirmations.source_of(key),
        data={'value': 'on' if session.confirmations.is_enabled(key) else 'off', 'commands': ', '.join(commands)},
    )


def _known_keys() -> dict[str, list[str]]:
    """The confirmations of the built-in commands, as ``{key: commands that ask for it}``."""
    return confirmation_keys(BUILTIN_COMMANDS)


def _checked_keys(words: list[str], name: str) -> 'tuple[list[str], EngineResult | None]':
    """The keys in ``words`` (all of them if none), or a failure if one is not a confirmation."""
    known = _known_keys()
    unknown = [word for word in words if word not in known]
    if unknown:
        close = difflib.get_close_matches(unknown[0], known, n=3)
        hint = f"did you mean {', '.join(close)}?" if close else ', '.join(known)
        return [], EngineResult.failure(f"{name}: unknown confirmation {', '.join(map(repr, unknown))} ({hint})")
    return words or list(known), None


def _items(session: EngineSession, keys: list[str], message: str = '') -> EngineResult:
    """The result listing the confirmations ``keys``."""
    known = _known_keys()
    return EngineResult(items=[_confirmation_item(session, key, known[key]) for key in keys], message=message)


@command(
    'confirm ls',
    usage='confirm ls [key...]',
    help="List the confirmations the console asks for.",
    args=('keys',),
    arg_kinds=('confirmation',),
)
def _cmd_confirm_ls(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List the confirmations the console asks for before a destructive command.

    Each has a key, the name of the command with underscores, and the commands that
    ask for it are listed. All are on until turned off. Without a key all of them
    are listed, otherwise only those.

    The source is session (set with 'confirm on' or 'confirm off'), config for a
    state that was kept with 'confirm save', or default.

    Examples:
      confirm ls
      confirm ls save trash
    """
    keys, failure = _checked_keys(arg_words(args.get('keys')), 'confirm ls')
    return failure or _items(session, keys)


def _set_state(session: EngineSession, args: dict[str, Any], name: str, enabled: bool) -> EngineResult:
    """Turn the confirmations named on or off; 'all' names every one, and a key or 'all' is required."""
    words = arg_words(args.get('keys'))
    if not words:
        raise UsageError
    keys, failure = _checked_keys([] if ALL_KEYS in words else words, name)
    if failure:
        return failure
    for key in keys:
        session.confirmations.set(key, enabled)
    return _items(session, keys)


@command(
    'confirm on',
    usage='confirm on <key...|all>',
    help="Ask for confirmations, for this session.",
    args=('keys',),
    arg_kinds=('confirmation-all',),
)
def _cmd_confirm_on(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Ask for the confirmations named, or all of them, in this session.

    Name the keys, or write all for every confirmation. Nothing is written to the
    configuration, 'confirm save' keeps the change.

    Examples:
      confirm on save trash
      confirm on all
    """
    return _set_state(session, args, 'confirm on', True)


@command(
    'confirm off',
    usage='confirm off <key...|all>',
    help="Stop asking for confirmations, for this session.",
    args=('keys',),
    arg_kinds=('confirmation-all',),
)
def _cmd_confirm_off(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Stop asking for the confirmations named, or all of them, in this session.

    Name the keys, or write all for every confirmation. Nothing is written to the
    configuration, 'confirm save' keeps the change.

    Examples:
      confirm off save trash
      confirm off all
    """
    return _set_state(session, args, 'confirm off', False)


@command(
    'confirm save',
    usage='confirm save [key...]',
    help="Write the confirmations set in this session to the configuration.",
    args=('keys',),
    arg_kinds=('confirmation',),
    destructive=True,
)
def _cmd_confirm_save(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Write the confirmations turned on or off in this session to the configuration.

    Without a key all of them are written, otherwise only the named ones. The
    console asks for a confirmation.

    Examples:
      confirm save
      confirm save trash
    """
    words = arg_words(args.get('keys'))
    _, failure = _checked_keys(words, 'confirm save')
    if failure:
        return failure
    written = [key for key in session.confirmations.overridden() if not words or key in words]
    session.confirmations.save(written)
    message = "written to the configuration" if written else "no confirmation was set in this session"
    return _items(session, written, message)

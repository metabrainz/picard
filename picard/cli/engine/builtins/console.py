#
# Picard, the next-generation MusicBrainz tagger
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

"""The commands that control the console itself: ``shell set``, ``shell get``, ``shell remint`` and ``shell history``."""

from typing import Any

from picard.cli.engine.builtins.helpers import (
    arg_first,
    arg_joined,
    arg_words,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.handles import HANDLE_KINDS
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cli.engine.settings import SettingError


def _setting_item(info: dict[str, Any]) -> EngineItemResult:
    """A result item for a setting: its name is the handle, where its value comes from the status."""
    data = {key: info[key] for key in ('value', 'default', 'title')}
    return EngineItemResult(handle=info['name'], status=info['source'], data=data)


@command(
    'shell get',
    usage='shell get [name]',
    help="Show the settings of the console.",
    args=('name',),
    arg_kinds=('setting',),
)
def _cmd_shell_get(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Show a setting of the console, or all of them: the value, the default and what it is for.

    A number is a limit, and -1 means no limit. See 'shell set'.

    Examples:
      shell get
      shell get open_max
    """
    name = arg_first(args.get('name'))
    try:
        names = [name] if name else session.settings.names()
        return EngineResult(items=[_setting_item(session.settings.describe(n)) for n in names])
    except SettingError as e:
        return EngineResult.failure(f"shell get: {e}")


@command(
    'shell set',
    usage='shell set <name> <value>',
    help="Set a setting of the console for this session.",
    args=('name', 'value'),
    arg_kinds=('setting', ''),
)
def _cmd_shell_set(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Set a setting of the console for this session only.

    The value is a number, and -1 means no limit. Nothing is written to the
    configuration. 'shell get' shows the settings, what they are for and their
    default.

    Examples:
      shell set open_max 10
      shell set minted_max -1
    """
    name = arg_first(args.get('name'))
    value = arg_joined(args.get('value'))
    if not name or value is None:
        raise UsageError
    try:
        session.settings.set(name, value)
        return EngineResult(items=[_setting_item(session.settings.describe(name))])
    except SettingError as e:
        return EngineResult.failure(f"shell set: {e}")


@command(
    'shell remint',
    usage='shell remint [kind]...',
    help="Mint the handles of a kind from 1 again.",
    args=('kind',),
    arg_kinds=('handle-kind',),
)
def _cmd_shell_remint(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Mint the handles of a kind from 1 again.

    Handles are never reused, so after objects are removed and others added the
    numbers keep growing. This mints them from 1 again, for a kind of object (f for
    files, c clusters, a albums, t tracks, m lookup candidates, v release
    versions, k collections) when none of that kind is left: the objects that are
    there are never renumbered, and a kind with some is reported as in_use and left
    as it is. Without a kind, all of them are tried.

    A handle printed before (f3) may name another object afterwards, so use it
    only when nothing refers to the old ones.

    Examples:
      shell remint f
      shell remint f c a
      shell remint
    """
    kinds = arg_words(args.get('kind')) or list(HANDLE_KINDS)
    unknown = [kind for kind in kinds if kind not in HANDLE_KINDS]
    if unknown:
        kinds_text = ', '.join(f"{prefix} {name}" for prefix, name in HANDLE_KINDS.items())
        return EngineResult.failure(f"shell remint: unknown kind {', '.join(unknown)} ({kinds_text})")
    items = []
    notes = []
    for kind in dict.fromkeys(kinds):
        live = session.remint(kind)
        items.append(EngineItemResult(handle=kind, status='in_use' if live else 'reminted'))
        if live:
            notes.append(f"{kind}: {live} {HANDLE_KINDS[kind]}(s) still there, left as they are")
    return EngineResult(items=items, message='; '.join(notes))


@command(
    'shell history',
    usage='shell history [count|clear]',
    help="List the lines typed, or forget them.",
    args=('what',),
    arg_kinds=('history',),
)
def _cmd_shell_history(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List the lines typed in the console, the ones the up key recalls, numbered, the last ones last.

    With a number, only that many of the last ones. 'shell history clear' forgets
    them all, in this console and in the file they are kept in, for a line that
    should not have been kept (a line that starts with a space is not). A console
    running at the same time still adds the lines of its session when it ends.

    Examples:
      shell history
      shell history 20
      shell history clear
    """
    what = arg_first(args.get('what'))
    history = session.history
    if history is None:
        return EngineResult.failure("shell history: this console keeps no history")
    if what == 'clear':
        history.clear()
        return EngineResult(message="the history is cleared")
    lines = history.lines()
    numbered = list(enumerate(lines, 1))
    if what is not None:
        if not what.isdigit():
            raise UsageError
        numbered = numbered[-int(what) :] if int(what) else []
    if not numbered:
        return EngineResult(message="the history is empty")
    return EngineResult(
        items=[EngineItemResult(handle=str(number), status='history', data={'line': line}) for number, line in numbered]
    )

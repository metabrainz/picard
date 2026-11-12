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

"""The commands that control the console itself: ``shell set`` and ``shell get``."""

from typing import Any

from picard.cli.engine.builtins.helpers import (
    arg_first,
    arg_joined,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
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

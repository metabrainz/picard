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

"""The commands that control the options of the session: ``option ls``, ``get``, ``set``, ``unset`` and ``save``."""

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
from picard.cli.engine.options import OptionCommandError
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)


def _option_item(info: dict[str, Any]) -> EngineItemResult:
    """A result item for an option: its name is the handle, where its value comes from the status."""
    data = {key: info[key] for key in ('value', 'default', 'type', 'title', 'settable')}
    return EngineItemResult(handle=info['name'], status=info['source'], data=data)


@command(
    'option ls',
    usage='option ls [pattern]',
    help="List options and where their value comes from.",
    args=('pattern',),
    arg_kinds=('option',),
)
def _cmd_option_ls(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List options, with their value and where it comes from.

    Without a pattern only the options that are not at their default are listed: set
    in the configuration, by a profile, or in this session. With a pattern, the
    options whose name or title contains it, or that match it as a glob if it has
    *, ? or [, whatever their value. The source is session, profile <title>, config
    or default.

    Examples:
      option ls
      option ls rename
      option ls *script*
    """
    infos = session.list_options(arg_joined(args.get('pattern')))
    return EngineResult(items=[_option_item(info) for info in infos])


@command(
    'option get',
    usage='option get <name>',
    help="Show an option.",
    args=('name',),
    arg_kinds=('option',),
)
def _cmd_option_get(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Show an option: its value, default, type, title and where the value comes from.

    Example:
      option get move_files
    """
    name = arg_first(args.get('name'))
    if not name:
        raise UsageError
    try:
        info = session.describe_option(name)
    except OptionCommandError as e:
        return EngineResult.failure(f"option get: {e}")
    return EngineResult(items=[_option_item(info)])


@command(
    'option set',
    usage='option set <name> <value>',
    help="Set an option for this session only.",
    args=('name', 'value'),
    arg_kinds=('option', 'option-value'),
)
def _cmd_option_set(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Set an option for this session only.

    The value is checked as the option expects: true or false for a yes/no option, a
    number within the allowed range, comma-separated items or a JSON array for a
    list. The rest of the line is the value, so a text with spaces needs no quotes.

    Nothing is written to the configuration, so an experiment cannot change the
    settings the GUI uses; 'option save' keeps a value. Interface and plugin
    options, scripts, and the AcoustID and fpcalc settings can be shown but not set.

    Examples:
      option set move_files true
      option set move_files_to /tmp/out
    """
    name = arg_first(args.get('name'))
    value = arg_joined(args.get('value'))
    if not name or value is None:
        raise UsageError
    try:
        info = session.set_option(name, value)
    except OptionCommandError as e:
        return EngineResult.failure(f"option set: {e}")
    return EngineResult(items=[_option_item(info)])


@command(
    'option unset',
    usage='option unset <name>',
    help="Forget the session's value of an option.",
    args=('name',),
    arg_kinds=('option',),
)
def _cmd_option_unset(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Forget the value an option was given in this session.

    The option goes back to what is below it: a profile, the configuration or the
    default.

    Example:
      option unset move_files
    """
    name = arg_first(args.get('name'))
    if not name:
        raise UsageError
    try:
        info = session.unset_option(name)
    except OptionCommandError as e:
        return EngineResult.failure(f"option unset: {e}")
    return EngineResult(items=[_option_item(info)])


@command(
    'option save',
    usage='option save [name...]',
    help="Write the session's options to the configuration.",
    args=('names',),
    arg_kinds=('option',),
    destructive=True,
)
def _cmd_option_save(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Write the options set in this session to the configuration.

    Without a name all of them are written, otherwise only the named ones. It is the
    only way a session changes the configuration, which the GUI uses too. A value
    goes into the profile that sets the option if there is one, else into the
    configuration. The console asks for a confirmation.

    Examples:
      option save
      option save move_files_to
    """
    try:
        infos = session.save_options(arg_words(args.get('names')) or None)
    except OptionCommandError as e:
        return EngineResult.failure(f"option save: {e}")
    message = "written to the configuration" if infos else "no option was set in this session"
    return EngineResult(items=[_option_item(info) for info in infos], message=message)

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

"""The ``help`` command."""

from difflib import get_close_matches
import inspect
from typing import Any

from picard.cli.engine.builtins.helpers import arg_words
from picard.cli.engine.commands import (
    EngineCommand,
    EngineCommandRegistry,
    EngineSession,
)
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cli.engine.topics import (
    TOPICS,
    Topic,
)


def _command_item(command: EngineCommand, detail: bool) -> EngineItemResult:
    """A result item for a command: the line of a list, or all its help if ``detail``."""
    data: dict[str, Any] = {'kind': 'command', 'name': command.name, 'summary': command.help, 'detail': detail}
    if detail:
        data['usage'] = command.usage
        data['description'] = command.description
    return EngineItemResult(handle='', status='help', data=data)


def _topic_item(topic: Topic, detail: bool) -> EngineItemResult:
    """A result item for a topic: the line of a list, or its whole text if ``detail``."""
    data: dict[str, Any] = {'kind': 'topic', 'name': topic.name, 'summary': topic.summary, 'detail': detail}
    if detail:
        data['description'] = topic.text
    return EngineItemResult(handle='', status='help', data=data)


def _cmd_help(registry: EngineCommandRegistry, session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Show the commands, or explain one.

    help                 list the commands and the topics
    help <command>       how to use a command, with examples ('help move')
    help <group>         the commands of a group ('help option')
    help <topic>         explain how to name things: 'help selectors',
                         'help paths', 'help tags' and 'help quoting'

    Commands are written as a group and a verb ('option set'), and a few have a
    single word ('ls').
    """
    query = ' '.join(arg_words(args.get('topic')))
    commands = sorted(registry, key=lambda command: command.name)
    topics = {topic.name: topic for topic in TOPICS}

    if not query:
        items = [_command_item(command, detail=False) for command in commands]
        items += [_topic_item(topic, detail=False) for topic in TOPICS]
        return EngineResult(items=items)

    command = registry.get(query)
    group = [other for other in commands if other.noun == query and other is not command]
    if command is not None or group:
        # A command that is also a group ('cluster', 'cluster lookup') shows both.
        items = [_command_item(command, detail=True)] if command is not None else []
        items += [_command_item(other, detail=False) for other in group]
        return EngineResult(items=items)
    if query in topics:
        return EngineResult(items=[_topic_item(topics[query], detail=True)])

    known = {command.name for command in commands} | {command.noun for command in commands} | set(topics)
    close = get_close_matches(query, sorted(known), n=3)
    hint = f" (did you mean {', '.join(close)}?)" if close else ""
    return EngineResult.failure(f"help: no command, group or topic named {query!r}{hint}")


def make_help_command(registry: EngineCommandRegistry) -> EngineCommand:
    """The ``help`` command of ``registry``, which it describes.

    Unlike the other commands it is made for a registry rather than declared
    once: it has to know the commands of the frontend it is run from.
    """
    return EngineCommand(
        name='help',
        run=lambda session, args: _cmd_help(registry, session, args),
        help="Explain the commands and the topics.",
        usage='help [command|group|topic]',
        description=inspect.getdoc(_cmd_help) or '',
        args=('topic',),
        arg_kinds=('help',),
    )

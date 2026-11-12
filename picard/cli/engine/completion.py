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

"""Tab-completion for the engine shell.

The core is :func:`complete` — a pure function (no readline) that, given the
current line and the word being completed, returns candidate completions. It
decides what to complete from the command registry and the command's declared
``arg_kinds``:

- command name (first word(s)) -> matching ``noun verb`` names
- the words after ``!command`` (a line for the system shell) -> paths
- a ``path`` arg -> filesystem paths (``~`` expanded, directory-aware)
- a ``device`` arg -> detected CD/DVD drives (cross-platform)
- a ``tag`` arg -> the names of the tags
- an ``option`` arg -> option names, and an ``option-value`` arg the values
  that make sense for the option named by the previous word
- a ``help`` arg -> the commands, their groups and the topics, a word at a time
- a ``selector`` / ``handle`` arg -> live session handles + wildcards, and
  after a ``.`` the path segments that can follow (``a1.`` -> ``a1.d1``,
  ``a1.t*``, ...); in a comma-separated union the last term is completed

:class:`ShellCompleter` adapts :func:`complete` to the stdlib ``readline``
completer protocol.
"""

import glob
import os

from picard.cli.engine.dispatch import split_command_name
from picard.cli.engine.topics import TOPICS


_WILDCARDS = ('*', 'f*', 'c*', 'a*', 't*', 'm*', 'v*', 'k*', 'u')
_HANDLE_PREFIXES = ('f', 'c', 'a', 't', 'm', 'v', 'k')


def _complete_path(text: str) -> list[str]:
    """Filesystem path completions for ``text`` (supports ~ and directories)."""
    expanded = os.path.expanduser(text)
    # The text is a prefix of a name, not a pattern: [ ] * ? in it are part of the name.
    matches = glob.glob(glob.escape(expanded) + '*')
    results = []
    for match in matches:
        # Re-collapse the home dir so the completion matches what the user typed.
        shown = match
        if text.startswith('~'):
            home = os.path.expanduser('~')
            if match.startswith(home):
                shown = '~' + match[len(home) :]
        if os.path.isdir(match):
            shown += os.sep
        results.append(shown)
    return sorted(results)


def _cdrom_devices() -> list[str]:
    """Available CD/DVD drive identifiers, for completing a device argument.

    Uses Picard's cross-platform drive detection (Linux device nodes like
    ``/dev/cdrom``, Windows drive letters like ``D:``). Imported lazily to keep
    the optional discid / cdrom machinery off the completer's import path.
    """
    try:
        from picard.util.cdrom import get_cdrom_drives

        return get_cdrom_drives()
    except Exception:
        return []


def _tag_names() -> list[str]:
    """The names of the tags a user can set, plugin-provided ones included, for completing a tag.

    Imported lazily, with the configuration they depend on, like the drives.
    """
    try:
        from picard.tags import tag_names

        return sorted(tag_names())
    except Exception:
        return []


def _option_values(session, name: str) -> list[str]:
    """Values worth offering for the option ``name``: true/false, or its current value."""
    try:
        info = session.describe_option(name)
    except ValueError:  # not an option
        return []
    if not info['settable']:
        return []
    if info['type'] == 'bool':
        return ['true', 'false']
    if info['type'] == 'list':
        return []
    return [str(info['value'])]


def _complete_help(registry, words: list[str], text: str) -> list[str]:
    """Completions for the argument of ``help``: the word after ``words`` in a command name or a topic.

    A command is a group and a verb (``option set``), so the first word is that
    of a group, a command or a topic and the second the verb of that group.
    """
    names = registry.names() + [topic.name for topic in TOPICS]
    prefix = ' '.join(words) + ' ' if words else ''
    following = (name[len(prefix) :].split(' ', 1)[0] for name in names if name.startswith(prefix))
    return sorted({word for word in following if word and word.startswith(text)})


def _live_handles(session) -> list[str]:
    """All currently-live handles across the known prefixes, via the session."""
    handles = []
    for prefix in _HANDLE_PREFIXES:
        for entity in session.enumerate_prefix(prefix):
            try:
                handles.append(session.handle_for(entity))
            except ValueError:
                continue
    return handles


def _complete_selector(session, text: str, wildcards: bool) -> list[str]:
    """Completions for the selector ``text``: handles, wildcards and path segments.

    Only the term being typed is completed (the part after the last ``,``), and
    after a ``.`` the options are what can follow the path before it.
    """
    union, comma, term = text.rpartition(',')
    union += comma
    base, dot, _partial = term.rpartition('.')
    if dot:
        options = [f"{base}.{segment}" for segment in session.path_segments(base)]
    else:
        options = _live_handles(session)
        if wildcards:
            options += list(_WILDCARDS)
    return [union + option for option in set(options) if option.startswith(term)]


def complete(line: str, text: str, registry, session) -> list[str]:
    """Return completions for ``text`` given the full ``line`` so far.

    ``text`` is the word being completed (readline's current token); ``line``
    is the whole line up to the cursor.
    """
    # Tokens already on the line (the trailing partial word is ``text``).
    head = line[: len(line) - len(text)]
    tokens = head.split()

    # A line for the shell of the system (``!command args``): its words are
    # paths, except the command itself, which is the shell's to find.
    if line.lstrip().startswith('!'):
        command_words = head.lstrip()[1:].split()
        return _complete_path(text) if command_words else []

    # Completing the command name itself (nothing resolved yet).
    if not tokens:
        names = registry.names() + ['quit', 'exit']
        return sorted(n for n in names if n.startswith(text))

    # When the first word is on the line and we're completing the second word,
    # offer the verbs of any two-word command sharing that first word. This is
    # needed even when the first word is ITSELF a complete command (e.g.
    # ``cluster`` is a command and also the noun of ``cluster lookup``):
    # ``cluster loo<TAB>`` must still complete to ``lookup``.
    verb_matches: list[str] = []
    if len(tokens) == 1:
        prefix = tokens[0] + ' '
        verb_matches = [
            n[len(prefix) :] for n in registry.names() if n.startswith(prefix) and n[len(prefix) :].startswith(text)
        ]

    # Is the first token (or first two) a known command?
    name, rest = split_command_name(tokens, registry)
    command = registry.get(name)
    if command is None:
        # First word is not a command on its own; only the verb matches apply.
        return sorted(set(verb_matches))

    # We have a command; the number of already-typed args decides the arg index.
    arg_index = len(rest)
    kind = command.arg_kind(arg_index)
    arg_matches: list[str] = []
    if kind == 'path':
        arg_matches = _complete_path(text)
    elif kind == 'device':
        arg_matches = [d for d in _cdrom_devices() if d.startswith(text)]
    elif kind == 'tag':
        arg_matches = [tag for tag in _tag_names() if tag.startswith(text)]
    elif kind == 'option':
        arg_matches = [name for name in session.option_names() if name.startswith(text)]
    elif kind == 'setting':
        arg_matches = [name for name in session.settings.names() if name.startswith(text)]
    elif kind == 'option-value' and rest:
        arg_matches = [value for value in _option_values(session, rest[0]) if value.startswith(text)]
    elif kind == 'help':
        arg_matches = _complete_help(registry, rest, text)
    elif kind in {'selector', 'handle'}:
        arg_matches = _complete_selector(session, text, wildcards=(kind == 'selector'))

    # Merge verb completions (two-word commands) with the one-word command's
    # arg completions, so both ``cluster lookup`` and ``cluster <selector>`` are
    # offered after ``cluster ``.
    return sorted(set(verb_matches) | set(arg_matches))


class ShellCompleter:
    """readline completer adapter around :func:`complete`."""

    def __init__(self, registry, session, get_line_buffer):
        self._registry = registry
        self._session = session
        self._get_line_buffer = get_line_buffer
        self._matches: list[str] = []

    def complete(self, text: str, state: int) -> 'str | None':
        if state == 0:
            line = self._get_line_buffer()
            self._matches = complete(line, text, self._registry, self._session)
        if 0 <= state < len(self._matches):
            return self._matches[state]
        return None

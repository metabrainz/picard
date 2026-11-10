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

"""The commands that act on files: ``file add``, ``save``, ``move``, ``remove`` and ``trash``."""

import glob
import os
import re
from typing import Any

from picard.cli.engine.builtins.helpers import (
    TIMEOUT_DEFAULT,
    arg_words,
    drain,
    entity_item,
    join_notes,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
)
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.file import File
from picard.util import (
    normpath,
    resolve_fs_path,
)
from picard.workspace import workspace


def _unescape_glob(path: str) -> str:
    """Drop the backslashes put before ``[``, ``]``, ``*`` and ``?`` (``\\[1998\\]`` -> ``[1998]``)."""
    return re.sub(r'\\([\[\]*?])', r'\1', path)


def _existing_path(token: str) -> 'str | None':
    """The path ``token`` names as it is, or None if there is no such path.

    A path that exists is taken literally: nothing expands the command line
    before it gets here, so ``[1998]`` in the name of a folder is just part of
    its name, as it is when quoted for ``cd`` in a shell. A backslash before a
    character that is also glob syntax is accepted (``\\[1998\\]``), as people
    type it out of habit.
    """
    expanded = os.path.expanduser(token)
    candidates = [expanded]
    # On Windows a backslash is the path separator, not an escape.
    if os.sep != '\\':
        candidates.append(_unescape_glob(expanded))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _glob_matches(token: str) -> list[str]:
    """The paths matching ``token`` as a pattern, none if it has no wildcard.

    When the folder part of the pattern exists it is matched as it is, so
    ``[1998] Album/*.flac`` works whatever the folder is called.
    """
    expanded = os.path.expanduser(token)
    if not glob.has_magic(expanded):
        return []
    head, tail = os.path.split(expanded)
    if head and os.path.isdir(head):
        expanded = os.path.join(glob.escape(head), tail)
    return sorted(glob.glob(expanded))


def _resolve_token(token: str) -> list[str]:
    """The existing paths ``token`` stands for: the path itself, or what it matches."""
    path = _existing_path(token)
    if path is not None:
        return [path]
    return _glob_matches(token)


def _expand_input_paths(tokens: list[str]) -> 'tuple[list[str], list[str]]':
    """Expand user path tokens to concrete paths, recursing into directories.

    Each token is ``~``-expanded and, when no path of that name exists, glob-expanded
    (so ``dir/*`` works inside the REPL, where no shell expands it). Directories
    are walked by ``Workspace.scan_paths`` (respecting the recursively_add_files /
    ignore_hidden_files settings), as when adding paths in the GUI. Returns
    ``(files, unmatched_tokens)`` where unmatched tokens are those matching no
    existing path.
    """
    roots: list[str] = []
    unmatched: list[str] = []
    for token in tokens:
        matches = _resolve_token(token)
        if matches:
            roots.extend(matches)
        else:
            unmatched.append(token)

    # Fallback for unquoted paths containing spaces: the shell tokenizer split
    # e.g. "/music/Second tour/" into ["/music/Second", "tour/"]. If the
    # leftover tokens, re-joined with spaces, name an existing path (or a glob
    # that matches), treat them as that single path rather than reporting each
    # fragment as unresolved.
    if unmatched:
        matches = _resolve_token(' '.join(unmatched))
        if matches:
            roots.extend(matches)
            unmatched = []

    files = list(workspace().scan_paths(roots))
    return files, unmatched


def _named_files(tokens: list[str]) -> set[str]:
    """The paths among ``tokens`` that name an existing file directly (no pattern, not a directory)."""
    named = set()
    for token in tokens:
        path = _existing_path(token)
        if path is not None and os.path.isfile(path):
            named.add(normpath(resolve_fs_path(path)))
    return named


@command(
    'file add',
    usage='file add <path>...',
    help="Load files into the working set.",
    args=('paths',),
    arg_kinds=('path',),
)
def _cmd_file_add(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Load files into the working set.

    It takes files, directories and patterns such as *.flac. They are added as when
    they are dropped in the GUI: directories are walked (see the options
    recursively_add_files and ignore_hidden_files), files with MusicBrainz IDs go
    to their album or track, and cluster_new_files and analyze_new_files are
    honoured. Ignored files are skipped, and so are unsupported files found in a
    folder; one you named is reported.

    A path that exists is taken as it is, so a folder called '[1998] Album' needs no
    escaping; *, ? and [...] only act as a pattern when no such path exists. A path
    with spaces can be quoted.

    Each file gets a handle (f1, f2, ...), in filename order. A file that is already
    loaded is reported, not loaded twice.

    Examples:
      file add "/music/Billy Joel - [1998] Storm Front"
      file add ~/Music/incoming/*.flac
    """
    paths = arg_words(args.get('paths'))
    if not paths:
        return EngineResult.failure("file add: no paths given")

    filepaths, unmatched = _expand_input_paths(paths)
    # What the user pointed at by name, as opposed to what a folder or a pattern
    # brought in: an unsupported file among the latter (a cover image next to
    # the tracks) is ignored silently, as the GUI does, but one named explicitly
    # deserves to be told about.
    named = _named_files(paths)

    wks = workspace()
    opened = wks.add_files(filepaths)
    notes: list[str] = []
    # Drain the loads, and with them the placement of each file and the album
    # loads and matching it schedules.
    drain(session, TIMEOUT_DEFAULT, notes)

    # Report in filename order, whatever the outcome, like the GUI adds them, and
    # once for each path, although a folder and a name can bring the same one.
    # That order decides the handles the files are given.
    entries: list[tuple[str, str, File | None]] = [(path, 'ignored', None) for path in dict.fromkeys(opened.ignored)]
    entries += [(file.filename, 'already_loaded', file) for file in dict.fromkeys(opened.already_loaded)]
    entries += [(path, 'unsupported', None) for path in dict.fromkeys(opened.unsupported) if path in named]
    entries += [(file.filename, 'loaded', file) for file in opened.opened]

    items = []
    mints = []
    for path, outcome, file in sorted(entries, key=lambda entry: entry[0]):
        if file is None:
            items.append(EngineItemResult(handle='', status=outcome, data={'path': path}))
        elif outcome == 'already_loaded':
            # Never open a second File for a path that is already in the set.
            items.append(EngineItemResult(handle=session.handle_for(file), status=outcome, data={'path': path}))
        elif file.state == File.State.ERROR:
            items.append(EngineItemResult(handle='', status='error', data={'path': path}))
        else:
            # A file whose load had not finished when we gave up is not "added" yet.
            status = 'pending' if file.state == File.State.PENDING else 'added'
            items.append(entity_item(session, file, status))
            mints.append(items[-1].handle)

    ok = any(it.status in {'added', 'pending'} for it in items) or (not opened.opened and not unmatched)
    return EngineResult(ok=ok, items=items, mints=mints, unresolved=unmatched, message=join_notes(notes))

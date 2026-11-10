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

"""The commands that show the tags of the entities of the working set: ``metadata show``."""

from fnmatch import fnmatchcase
from typing import Any

from picard.album import Album
from picard.cli.engine.builtins.helpers import (
    arg_words,
    entity_item,
    reject_candidates,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.result import (
    EngineResult,
)
from picard.cluster import Cluster
from picard.config import get_config
from picard.file import File
from picard.tagdiff import (
    TagCounter,
    TagDiff,
    TagStatus,
    build_tag_diff,
    selection_of,
)
from picard.track import Track


_STATUS_NAMES = {
    TagStatus.CHANGED: 'changed',
    TagStatus.ADDED: 'added',
    TagStatus.REMOVED: 'removed',
    TagStatus.EMPTY: 'empty',
    TagStatus.UNCHANGED: 'unchanged',
}


def _kind(entity: Any) -> str:
    """What kind of entity ``entity`` is, as shown in the result."""
    for kind, entity_type in (('file', File), ('track', Track), ('album', Album), ('cluster', Cluster)):
        if isinstance(entity, entity_type):
            return kind
    return 'entity'


def _values(counter: TagCounter, tag: str) -> 'list[str] | None':
    """The values of ``tag`` as a list, or None if the objects do not agree on one list.

    The text of a row joins the values, so a value that contains the joiner looks
    like two values; the list tells them apart.
    """
    if counter.status(tag).is_grouped:
        return None
    if not counter.counts[tag]:
        return []
    values = counter.get(tag)
    return list(values) if isinstance(values, list) else None


def _row(tag_diff: TagDiff, tag: str) -> dict[str, Any]:
    """A tag of ``tag_diff`` as the metadata box shows it: the value it had, the one it has and how they differ.

    The values are also given as lists (``orig_values`` and ``new_values``) when
    the objects agree on them, which is not the case for a value that is grouped.
    """
    row: dict[str, Any] = {
        'tag': tag,
        'orig': tag_diff.old.display_value(tag).text,
        'new': tag_diff.new.display_value(tag).text,
        'status': _STATUS_NAMES[tag_diff.tag_status(tag)],
    }
    for key, counter in (('orig_values', tag_diff.old), ('new_values', tag_diff.new)):
        values = _values(counter, tag)
        if values is not None:
            row[key] = values
    return row


def tag_rows(entity: Any, patterns: list[str], settings: dict[str, Any], changes_first: bool) -> list[dict[str, Any]]:
    """The tags the metadata box shows for ``entity``, those that match ``patterns`` (all without any).

    This is the tag diff of what ``entity`` stands for in a selection (a track for
    its files, an album for its tracks and their files, ...), so the values of
    several files are grouped as in the box ("(different across 3 items)").
    """
    selection = selection_of([entity])
    if not (selection.files or selection.tracks):
        return []
    tag_diff = build_tag_diff(selection.files, selection.tracks, settings, changes_first=changes_first)
    return [_row(tag_diff, tag) for tag in tag_diff.tag_names if not patterns or _matches(tag, patterns)]


def _matches(tag: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(tag, pattern) for pattern in patterns)


@command(
    'metadata show',
    usage='metadata show <selector> [tag...]',
    help="Show the tags of files, tracks, albums or clusters.",
    args=('selector', 'tags'),
    arg_kinds=('selector', 'tag'),
)
def _cmd_metadata_show(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Show the tags of files, tracks, albums or clusters.

    It shows what the metadata box of the GUI shows when they are selected. A file
    has the tags it was loaded with and the ones it would be saved with, each shown
    as unchanged, changed (old -> new), added (+) or removed (-). A track, an album
    or a cluster stands for its files, and values that differ are grouped. The
    length and the name the file would be saved with are tags too.

    Without a tag, all the tags the box shows are listed, in its order. A tag is a
    name or a pattern. The selector must be a single word (f1,f2); see 'help tags'.

    The values of a tag are joined with '; ' to be read. A frontend that needs the
    values themselves, as a list, finds them in the result (orig_values and
    new_values), unless the objects of a selection do not agree on them.

    Examples:
      metadata show f1
      metadata show a1 artist album
      metadata show c1 musicbrainz_*
    """
    selector = args.get('selector')
    if not selector:
        raise UsageError
    patterns = arg_words(args.get('tags'))

    entities, unresolved = session.resolve(selector)
    rejected = reject_candidates(session, 'metadata show', entities, unresolved, what="has no tags")
    if rejected is not None:
        return rejected

    config = get_config()
    settings = config.setting.as_dict()
    changes_first = config.persist['show_changes_first']
    items = []
    for entity in entities:
        item = entity_item(session, entity, 'shown')
        item.data['kind'] = _kind(entity)
        item.data['tags'] = tag_rows(entity, patterns, settings, changes_first)
        items.append(item)

    shown = {row['tag'] for item in items for row in item.data['tags']}
    unmatched = [pattern for pattern in patterns if not any(fnmatchcase(tag, pattern) for tag in shown)]
    message = f"no tag matches: {', '.join(unmatched)}" if entities and unmatched else ''
    return EngineResult(items=items, resolved=[item.handle for item in items], unresolved=unresolved, message=message)

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

"""The commands that show and change the tags of the entities of the working set: ``metadata show``, ``set``, ``add``, ``rm-value`` and ``rm``."""

from collections.abc import Callable
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
    EngineItemResult,
    EngineResult,
)
from picard.cluster import Cluster
from picard.config import get_config
from picard.file import File
from picard.tagdiff import (
    TagCounter,
    TagDiff,
    TagStatus,
    apply_tag_values,
    build_tag_diff,
    merge_values,
    selection_of,
)
from picard.tags import ALL_TAGS
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


def _tag_name_error(tag: str) -> 'str | None':
    """Why ``tag`` cannot be the name of a tag to set, or None if it can."""
    if any(char in tag for char in '*?['):
        return f"{tag!r} is a pattern, a tag to set has a name"
    if tag.startswith('~'):
        return f"{tag!r} is a variable of the scripts, not a tag that can be set"
    return None


def _holds_single_value(tag: str) -> bool:
    """Whether ``tag`` is declared as holding a single value (a tag Picard does not know may hold several)."""
    tagvar = ALL_TAGS.tagvar_from_name(tag)
    return tagvar is not None and not tagvar.is_multi_value


def _resolve_to_edit(
    session: EngineSession, command: str, selector: str
) -> 'tuple[list[Any], list[str], EngineResult | None]':
    """The entities of ``selector`` to change the tags of, those not found and a failure if it is refused."""
    entities, unresolved = session.resolve(selector)
    return entities, unresolved, reject_candidates(session, command, entities, unresolved, what="has no tags")


def _change_values(
    session: EngineSession,
    args: dict[str, Any],
    command: str,
    change: Callable[[list[str], list[str]], list[str]],
    check_support: bool = True,
    check_single_value: bool = True,
) -> EngineResult:
    """Change the values of a tag on the entities of a selection.

    ``change(current, values)`` gives the values a tag should have, from those it
    has and those given on the command line.
    """
    selector = args.get('selector')
    tag = args.get('tag')
    values = arg_words(args.get('values'))
    if not (selector and tag and values):
        raise UsageError
    if '' in values:
        return EngineResult.failure(f"{command}: a value cannot be empty; to remove the tag use metadata rm")
    error = _tag_name_error(tag)
    if error:
        return EngineResult.failure(f"{command}: {error}")
    if check_single_value and len(values) > 1 and _holds_single_value(tag):
        # The words are one value that was not quoted: title a b c is "a b c".
        values = [' '.join(values)]
    entities, unresolved, rejected = _resolve_to_edit(session, command, selector)
    if rejected is not None:
        return rejected

    modified = set()
    items = []
    for entity in entities:
        changed = 0
        unsupported = 0
        for obj in selection_of([entity]).objects:
            # A file whose format cannot hold the tag would not save it: say so, as the box does not show it.
            if check_support and isinstance(obj, File) and not obj.supports_tag(tag):
                unsupported += 1
                continue
            current = obj.metadata.getall(tag)
            new = change(current, values)
            if new != current:
                modified.update(apply_tag_values([obj], tag, new))
                changed += 1
        if isinstance(entity, File) and unsupported:
            status = 'unsupported'
        else:
            status = 'changed' if changed else 'unchanged'
        item = entity_item(session, entity, status)
        item.data.update({'tag': tag, 'objects_changed': changed})
        if unsupported:
            item.data['files_unsupported'] = unsupported
        items.append(item)
    for obj in modified:
        obj.update()
    return EngineResult(items=items, resolved=[item.handle for item in items], unresolved=unresolved)


@command(
    'metadata set',
    usage='metadata set <selector> <tag> <value>...',
    help="Set the values of a tag.",
    args=('selector', 'tag', 'values'),
    arg_kinds=('selector', 'tag', ''),
)
def _cmd_metadata_set(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Set a tag of files, tracks, albums or clusters.

    Each word after the tag is a value, so a value with spaces is quoted, and a
    tag with several values is given them one after the other. A value is never
    split on '; ', which is only how 'metadata show' joins values for display:
    "Rock; Pop" is one value, Rock Pop are two. The words given to a tag that
    holds a single value, such as title, are one value ('title A Song' sets
    "A Song"). The tag is replaced if it has values already. Like the metadata
    box of the GUI, it changes what would be saved: look at it with 'metadata show', and write it
    with 'save'. An album, a track or a cluster is changed together with its
    files. A file whose format cannot hold the tag is left alone and reported as
    unsupported.

    Tags that start with ~ are variables of the scripts, not tags, and cannot be
    set. See 'help tags'.

    Examples:
      metadata set f1 title "A Song"
      metadata set c1 genre Rock Pop
      metadata set a1 albumartist "The Artist"
    """
    return _change_values(session, args, 'metadata set', lambda current, values: list(values))


@command(
    'metadata add',
    usage='metadata add <selector> <tag> <value>...',
    help="Add values to a tag.",
    args=('selector', 'tag', 'values'),
    arg_kinds=('selector', 'tag', ''),
)
def _cmd_metadata_add(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Add values to a tag of files, tracks, albums or clusters.

    The values are added after those the tag has, and the ones it has already are
    not repeated. It is otherwise like 'metadata set', which replaces them.

    Examples:
      metadata add f1 genre Jazz
      metadata add c1 performer:guitar "Some One"
    """
    return _change_values(session, args, 'metadata add', merge_values)


@command(
    'metadata rm-value',
    usage='metadata rm-value <selector> <tag> <value>...',
    help="Remove values from a tag.",
    args=('selector', 'tag', 'values'),
    arg_kinds=('selector', 'tag', ''),
)
def _cmd_metadata_rm_value(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Remove values from a tag of files, tracks, albums or clusters.

    The values given are taken out of the ones the tag has, and the others stay in
    their order. A value that is not there is ignored. A tag left with no value is
    removed, as 'metadata rm' does. It is otherwise like 'metadata add', which
    puts values in.

    Examples:
      metadata rm-value f1 genre Pop
      metadata rm-value c1 performer:guitar "Some One"
    """
    return _change_values(
        session,
        args,
        'metadata rm-value',
        lambda current, values: [value for value in current if value not in values],
        check_support=False,
        check_single_value=False,
    )


@command(
    'metadata rm',
    usage='metadata rm <selector> <tag>...',
    help="Remove tags.",
    args=('selector', 'tags'),
    arg_kinds=('selector', 'tag'),
)
def _cmd_metadata_rm(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Remove tags from files, tracks, albums or clusters.

    A tag is a name or a pattern (see 'help tags'): 'metadata rm f1 comment' or
    'metadata rm c1 musicbrainz_*'. The tags removed are those the metadata box
    shows for the selection, except the ones that cannot be removed (the length
    and the file path). As with 'metadata set', the files are changed when they
    are saved, and only then; 'metadata show' shows the tag as removed.

    Examples:
      metadata rm f1 comment
      metadata rm c1 musicbrainz_*
    """
    selector = args.get('selector')
    patterns = arg_words(args.get('tags'))
    if not (selector and patterns):
        raise UsageError
    entities, unresolved, rejected = _resolve_to_edit(session, 'metadata rm', selector)
    if rejected is not None:
        return rejected

    config = get_config()
    settings = config.setting.as_dict()
    modified = set()
    items: list[EngineItemResult] = []
    removed_all: set[str] = set()
    for entity in entities:
        selection = selection_of([entity])
        removed = []
        if selection.files or selection.tracks:
            tag_diff = build_tag_diff(selection.files, selection.tracks, settings)
            for tag in tag_diff.tag_names:
                if _matches(tag, patterns) and tag_diff.is_removable(tag):
                    modified.update(apply_tag_values(selection.objects, tag, []))
                    removed.append(tag)
        removed_all.update(removed)
        item = entity_item(session, entity, 'removed' if removed else 'unchanged')
        item.data['removed'] = removed
        items.append(item)
    for obj in modified:
        obj.update()

    unmatched = [pattern for pattern in patterns if not any(fnmatchcase(tag, pattern) for tag in removed_all)]
    message = f"no tag removed for: {', '.join(unmatched)}" if entities and unmatched else ''
    return EngineResult(items=items, resolved=[item.handle for item in items], unresolved=unresolved, message=message)

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

"""Human rendering of an EngineResult for the console frontend.

Commands return a structured :class:`~picard.cli.engine.result.EngineResult`
and never print. This is the console's renderer — the ONE place that turns a
result into text via :class:`~picard.cli.output.CliOutput`. The MCP frontend
will instead serialize ``result.to_dict()``; both read the same structured
result.
"""

import re
from typing import Any

from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cli.output import CliOutput
from picard.util.mbentity import RE_MB_ENTITY


# A lookup can return dozens of candidates, most of them hopeless; show the best
# ones and say how to see the others (the result itself keeps them all).
_CANDIDATES_SHOWN = 10

# What identifies an item in a one-line summary: its value is displayed as a name.
_NAME_KEYS = frozenset({'title', 'artist'})

# Statuses of the engine by what they mean for the user; any other is dimmed.
_STATUS_DONE = frozenset(
    {'matched', 'identified', 'saved', 'loaded', 'switched', 'moved', 'trashed', 'refreshed', 'opened'}
)
_STATUS_PENDING = frozenset({'pending', 'changed', 'not_loaded'})
_STATUS_FAILED = frozenset(
    {
        'error',
        'timeout',
        'load_failed',
        'lookup_failed',
        'unsupported',
        'no_match',
        'no_matches',
        'no_confident_match',
        'no_versions',
        'open_failed',
    }
)


_HANDLE = re.compile(r'([a-z]+)(\d+)')


def _compact_handles(handles: list[str]) -> list[str]:
    """The handles as terms of a selector, a run of consecutive ones written as a range.

    ``f1, f2, f3, c1, c2, a1, a3`` gives ``f1-3``, ``c1-2``, ``a1``, ``a3``.
    The order is kept: only the handles that follow each other are joined.
    """
    terms: list[str] = []
    run: tuple[str, int, int] | None = None  # prefix, first number, last number

    def flush() -> None:
        if run is None:
            return
        prefix, first, last = run
        terms.append(f"{prefix}{first}" if first == last else f"{prefix}{first}-{last}")

    for handle in handles:
        match = _HANDLE.fullmatch(handle)
        if match is None:
            flush()
            run = None
            terms.append(handle)
            continue
        prefix, number = match.group(1), int(match.group(2))
        if run is not None and run[0] == prefix and run[2] + 1 == number:
            run = (prefix, run[1], number)
        else:
            flush()
            run = (prefix, number, number)
    flush()
    return terms


def _candidates_to_show(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The first candidates, plus the applied one if it is further down the list."""
    return [cand for index, cand in enumerate(candidates) if index < _CANDIDATES_SHOWN or cand.get('applied')]


def _status(status: str, output: CliOutput) -> str:
    """A status, green when done, yellow when pending, red when failed."""
    if status in _STATUS_DONE:
        return output.d_status_ok(status)
    if status in _STATUS_PENDING:
        return output.d_status_pending(status)
    if status in _STATUS_FAILED:
        return output.d_status_failed(status)
    return output.dim(status)


def _score(score: float, output: CliOutput) -> str:
    """A similarity score (0 to 1), green when high, yellow when middling, red when low."""
    if score >= 0.9:
        return output.d_status_ok(score)
    if score >= 0.7:
        return output.d_status_pending(score)
    return output.d_status_failed(score)


def _highlight_mb_refs(text: str, output: CliOutput) -> str:
    """Colorize the MusicBrainz references (``release:<mbid>``, a bare MBID, ...) found in ``text``.

    Uses the same matcher as the commands that read such references
    (:data:`picard.util.mbentity.RE_MB_ENTITY`): the entity type is colored, and the MBID is dimmed.
    """

    def colorize(match) -> str:
        entity = match.group('entity')
        prefix = match.string[match.start() : match.start('id')]
        if entity:
            prefix = output.d_mb_entity(entity) + prefix[len(entity) :]
        return prefix + output.d_uuid(match.group('id'))

    return RE_MB_ENTITY.sub(colorize, text)


def _entity_ref(item: dict[str, Any]) -> str:
    """Build a ``<type>:<mbid>`` MusicBrainz reference from an item dict.

    Used to always surface which entity a candidate/match points at (e.g.
    ``release:0bad6e23-...``). Falls back gracefully: a bare MBID if the type
    is absent, or ``''`` if there is no MBID at all.
    """
    mbid = item.get('mbid')
    if not mbid:
        return ''
    entity_type = item.get('entity_type')
    return f"{entity_type}:{mbid}" if entity_type else str(mbid)


def _colored_entity_ref(item: dict[str, Any], output: CliOutput) -> str:
    """The ``<type>:<mbid>`` reference of an item with its colors, or ``''`` if it has none."""
    return _highlight_mb_refs(_entity_ref(item), output)


def _format_item_data(data: dict[str, Any], output: CliOutput) -> str:
    """Compact one-line summary of an item's data (title/artist/path/etc.).

    Leads with the ``<type>:<mbid>`` reference when the item points at a
    MusicBrainz entity, so every listed entity shows what it is and resolves to.
    """
    parts = []
    ref = _colored_entity_ref(data, output)
    if ref:
        parts.append(ref)
    for key in (
        'value',
        'default',
        'tag',
        'removed',
        'title',
        'artist',
        'filename',
        'username',
        'size',
        'albums',
        'url',
        'path',
        'file_count',
        'matched_album',
        'error',
    ):
        value = data.get(key)
        if isinstance(value, list):
            value = ', '.join(str(item) for item in value)
        if value not in (None, ''):
            if key == 'error':
                parts.append(output.d_warning(f"{key}={value}"))
            elif key == 'url':
                parts.append(f"{key}={output.d_url(value)}")
            elif key in _NAME_KEYS:
                parts.append(f"{key}={output.d_name(value)}")
            else:
                parts.append(f"{key}={value}")
    return '  '.join(parts)


def _tag_line(row: dict[str, Any], width: int, output: CliOutput) -> str:
    """One line for a tag of ``metadata show``: its name and its value, or what changed."""
    orig = row['orig']
    new = row['new']
    status = row['status']
    if status == 'changed':
        value = f"{output.d_replaced(orig)} {output.d_arrow()} {output.d_added(new)}"
    elif status == 'added':
        value = output.d_added(f"+ {new}")
    elif status == 'removed':
        value = output.d_removed(f"- {orig}")
    else:
        value = new
    return f"{output.d_name(row['tag'])}{' ' * (width - len(row['tag']))}  {value}"


def _render_help(items: list[EngineItemResult], output: CliOutput) -> None:
    """Render the result of ``help``: the lines of a list, or the whole help of a command or a topic."""
    width = max((len(item.data['name']) for item in items if not item.data['detail']), default=0)
    previous = None
    for item in items:
        data = item.data
        if data['detail']:
            if data['kind'] == 'command':
                output.print(output.d_command(data['usage']))
                output.nl()
            output.print(data['description'])
            previous = 'detail'
            continue
        if previous != data['kind']:
            if previous is not None:
                output.nl()
            header = 'See also:' if previous == 'detail' else {'command': 'Commands:', 'topic': 'Topics:'}[data['kind']]
            output.print(output.dim(header))
            previous = data['kind']
        name = output.d_command(data['name']) if data['kind'] == 'command' else output.d_name(data['name'])
        output.print(f"  {name}{' ' * (width - len(data['name']))}  {data['summary']}")


def render_result(result: EngineResult, output: CliOutput, minted_max: 'int | None' = None) -> None:
    """Render ``result`` to ``output`` for a human reader.

    ``minted_max`` is the most handles written after ``minted:`` (0 for none, None for no limit).
    """
    if not result.ok:
        output.error(_highlight_mb_refs(result.error or "command failed", output))
        if result.unresolved:
            output.warning("unresolved: " + ', '.join(result.unresolved))
        return

    if result.items and all(item.status == 'help' for item in result.items):
        _render_help(result.items, output)
        return

    for item in result.items:
        indent = '  ' * int(item.data.get('depth', 0))
        handle = output.d_id(item.handle) if item.handle else '—'
        # Where the entity sits now (the handle is what stays valid).
        location = f"{output.d_path(item.path)}  " if item.path else ''
        summary = _format_item_data(item.data, output)
        line = f"{indent}{handle}  {location}{_status(item.status, output)}"
        if summary:
            line += f"  {summary}"
        output.print(line)
        # The tags of an entity (metadata show), one per line under it.
        tags = item.data.get('tags', [])
        width = max((len(row['tag']) for row in tags), default=0)
        for row in tags:
            output.print(f"{indent}    {_tag_line(row, width, output)}")
        # Lookup items carry a candidate list; show it indented.
        candidates = item.data.get('candidates', [])
        shown = _candidates_to_show(candidates)
        for cand in shown:
            mark = output.d_mark('*') if cand.get('applied') else ' '
            chandle = output.d_id(cand.get('handle', '?'))
            title = output.d_name(cand.get('title', ''))
            score = cand.get('similarity')
            score_s = f" ({_score(score, output)})" if score is not None else ''
            # Always show the MusicBrainz entity reference as <type>:<mbid>
            # (e.g. release:0bad6e23-...), so a candidate is unambiguously
            # identifiable and directly usable with the lookup/URL tools.
            ref = _colored_entity_ref(cand, output)
            ref_s = f"{ref}  " if ref else ''
            output.print(f"    {mark} {chandle}  {ref_s}{title}{score_s}")
        if len(shown) < len(candidates):
            output.print(output.dim(f"      … {len(candidates) - len(shown)} more: ls {item.handle}.m*"))
        # The versions of an album: all of them, the one it is now marked.
        versions = item.data.get('versions', [])
        for version in versions:
            mark = output.d_mark('*') if version.get('current') else ' '
            vhandle = output.d_id(version.get('handle', '?'))
            ref = _colored_entity_ref(version, output)
            ref_s = f"{ref}  " if ref else ''
            output.print(f"    {mark} {vhandle}  {ref_s}{output.d_name(version.get('title', ''))}")
        if item.data.get('total', 0) > len(versions) > 0:
            output.print(
                output.dim(f"      … {item.data['total']} releases in the group, the first {len(versions)} are listed")
            )

    if result.mints and minted_max != 0:
        terms = _compact_handles(result.mints)
        shown = terms if minted_max is None else terms[:minted_max]
        minted = ', '.join(shown)
        if len(shown) < len(terms):
            minted += f" … (+{len(terms) - len(shown)} more)"
        output.print(output.dim("minted: " + minted))
    if result.unresolved:
        output.warning("unresolved: " + ', '.join(result.unresolved))
    if result.message:
        output.info(_highlight_mb_refs(result.message, output))
    if not result.items and not result.mints and not result.unresolved and not result.message:
        output.print(output.dim("(nothing)"))

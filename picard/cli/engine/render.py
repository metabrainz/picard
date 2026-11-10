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

from typing import Any

from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cli.output import CliOutput


# A lookup can return dozens of candidates, most of them hopeless; show the best
# ones and say how to see the others (the result itself keeps them all).
_CANDIDATES_SHOWN = 10
_MINTED_SHOWN = 12


def _candidates_to_show(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The first candidates, plus the applied one if it is further down the list."""
    return [cand for index, cand in enumerate(candidates) if index < _CANDIDATES_SHOWN or cand.get('applied')]


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


def _format_item_data(data: dict[str, Any]) -> str:
    """Compact one-line summary of an item's data (title/artist/path/etc.).

    Leads with the ``<type>:<mbid>`` reference when the item points at a
    MusicBrainz entity, so every listed entity shows what it is and resolves to.
    """
    parts = []
    ref = _entity_ref(data)
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
        'path',
        'file_count',
        'matched_album',
        'error',
    ):
        value = data.get(key)
        if isinstance(value, list):
            value = ', '.join(str(item) for item in value)
        if value not in (None, ''):
            parts.append(f"{key}={value}")
    return '  '.join(parts)


def _tag_line(row: dict[str, Any], width: int, output: CliOutput) -> str:
    """One line for a tag of ``metadata show``: its name and its value, or what changed."""
    orig = row['orig']
    new = row['new']
    status = row['status']
    if status == 'changed':
        value = f"{orig} {output.d_arrow()} {new}"
    elif status == 'added':
        value = f"+ {new}"
    elif status == 'removed':
        value = f"- {orig}"
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


def render_result(result: EngineResult, output: CliOutput) -> None:
    """Render ``result`` to ``output`` for a human reader."""
    if not result.ok:
        output.error(result.error or "command failed")
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
        location = f"{output.dim(item.path)}  " if item.path else ''
        summary = _format_item_data(item.data)
        line = f"{indent}{handle}  {location}{output.dim(item.status)}"
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
            mark = '*' if cand.get('applied') else ' '
            chandle = output.d_id(cand.get('handle', '?'))
            title = cand.get('title', '')
            score = cand.get('similarity')
            score_s = f" ({score})" if score is not None else ''
            # Always show the MusicBrainz entity reference as <type>:<mbid>
            # (e.g. release:0bad6e23-...), so a candidate is unambiguously
            # identifiable and directly usable with the lookup/URL tools.
            ref = _entity_ref(cand)
            ref_s = f"{output.dim(ref)}  " if ref else ''
            output.print(f"    {mark} {chandle}  {ref_s}{title}{score_s}")
        if len(shown) < len(candidates):
            output.print(output.dim(f"      … {len(candidates) - len(shown)} more: ls {item.handle}.m*"))
        # The versions of an album: all of them, the one it is now marked.
        versions = item.data.get('versions', [])
        for version in versions:
            mark = '*' if version.get('current') else ' '
            vhandle = output.d_id(version.get('handle', '?'))
            ref = _entity_ref(version)
            ref_s = f"{output.dim(ref)}  " if ref else ''
            output.print(f"    {mark} {vhandle}  {ref_s}{version.get('title', '')}")
        if item.data.get('total', 0) > len(versions) > 0:
            output.print(
                output.dim(f"      … {item.data['total']} releases in the group, the first {len(versions)} are listed")
            )

    if result.mints:
        minted = ', '.join(result.mints[:_MINTED_SHOWN])
        if len(result.mints) > _MINTED_SHOWN:
            minted += f" … (+{len(result.mints) - _MINTED_SHOWN} more)"
        output.print(output.dim("minted: " + minted))
    if result.unresolved:
        output.warning("unresolved: " + ', '.join(result.unresolved))
    if result.message:
        output.info(result.message)
    if not result.items and not result.mints and not result.unresolved and not result.message:
        output.print(output.dim("(nothing)"))

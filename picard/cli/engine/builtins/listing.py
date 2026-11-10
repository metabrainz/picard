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

"""The commands that show the working set: ``ls`` and ``tree``."""

from typing import Any

from picard.album import (
    Album,
)
from picard.cli.engine.builtins.helpers import (
    entity_item,
    handles_of,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import EngineSession
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track


@command(
    'ls',
    usage='ls [selector]',
    help="List the objects of the working set.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_ls(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List the objects of the working set, with their handles.

    Without a selector it lists the top level: the files that are in no cluster, the
    clusters and the albums. With one, it lists the objects the selector names.

    Examples:
      ls
      ls a*
      ls c1.f*
    """
    # Without a selector, the universal ``*``: the top level, as in the GUI panes.
    entities, unresolved = session.resolve(args.get('selector') or '*')
    items = [entity_item(session, entity, 'listed') for entity in entities]
    return EngineResult(items=items, resolved=[it.handle for it in items], unresolved=unresolved)


def _tree_item(session: EngineSession, entity: Any, kind: str, depth: int) -> EngineItemResult:
    """Build a depth-tagged tree item for ``entity``.

    ``kind`` is a short structural role ('unclustered', 'cluster', 'album',
    'track', 'file', 'unmatched') shown as the status; ``depth`` drives the
    renderer's indentation.
    """
    item = entity_item(session, entity, kind)
    item.data['depth'] = depth
    return item


def _tree_track(session: EngineSession, track: Any, items: list, depth: int = 0) -> None:
    """Append ``track`` and the files matched to it to ``items``."""
    items.append(_tree_item(session, track, 'track', depth))
    for file in track.files:
        items.append(_tree_item(session, file, 'file', depth + 1))


def _tree_album(session: EngineSession, album: Any, items: list, depth: int = 0) -> None:
    """Append ``album`` and its tracks/matched-files/unmatched bucket to ``items``."""
    items.append(_tree_item(session, album, 'album', depth))
    for track in album.tracks:
        _tree_track(session, track, items, depth + 1)
    for file in album.unmatched_files.files:
        items.append(_tree_item(session, file, 'unmatched', depth + 1))


def _tree_cluster(session: EngineSession, cluster: Any, items: list, depth: int = 0) -> None:
    """Append ``cluster`` and its files to ``items``."""
    items.append(_tree_item(session, cluster, 'cluster', depth))
    for file in cluster.files:
        items.append(_tree_item(session, file, 'file', depth + 1))


@command(
    'tree',
    usage='tree [selector]',
    help="Show the working set as a tree.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_tree(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Show the working set as a tree, like the panes of the GUI.

    Without a selector it shows the files that are in no cluster, the clusters with
    their files, and the albums with their tracks, the files matched to each track
    and the files of the album that are not matched. With a selector it shows only
    the selected objects and what is below them.

    Every line starts with the handle of the object, to use in other commands. 'ls'
    gives a flat list instead.

    Examples:
      tree
      tree a1
    """
    selector = args.get('selector')
    # Without a selector, the universal ``*``: the unclustered files, the clusters
    # and the albums, as in the GUI panes.
    entities, unresolved = session.resolve(selector or '*')
    items: list[EngineItemResult] = []
    for entity in entities:
        if isinstance(entity, Album):
            _tree_album(session, entity, items)
        elif isinstance(entity, Cluster):
            _tree_cluster(session, entity, items)
        elif isinstance(entity, Track):
            _tree_track(session, entity, items)
        elif isinstance(entity, File):
            # Without a selector the files are the unclustered ones.
            items.append(_tree_item(session, entity, 'file' if selector else 'unclustered', 0))
        else:  # a lookup candidate: nothing below it
            items.append(_tree_item(session, entity, 'candidate', 0))
    return EngineResult(items=items, resolved=handles_of(session, entities), unresolved=unresolved)

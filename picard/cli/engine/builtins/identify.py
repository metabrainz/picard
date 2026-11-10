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

"""The commands that identify files: ``cluster``."""

from typing import Any

from picard.album import (
    Album,
)
from picard.cli.engine.builtins.helpers import (
    entity_item,
    handles_of,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
)
from picard.cli.engine.result import (
    EngineResult,
)
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track
from picard.workspace import workspace


@command(
    'cluster',
    usage='cluster [selector]',
    help="Group files into clusters.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_cluster(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Group files into clusters by their metadata.

    Without a selector the files that are in no cluster are grouped. A cluster
    stands for its files, so 'cluster c1' groups them again. An album or a track is
    refused: taking files out of an album should be explicit, with 'move' first or
    by naming the files ('cluster a1.f*'). The new clusters get handles; a group of
    a single file stays where it is.

    Examples:
      cluster
      cluster f1,f2,f3
    """
    selector = args.get('selector') or 'f*'
    entities, unresolved = session.resolve(selector)
    files: list[File] = []
    for entity in entities:
        if isinstance(entity, File):
            files.append(entity)
        elif isinstance(entity, Cluster):
            files.extend(file for file in entity.files if isinstance(file, File))
        else:
            handle = session.handle_for(entity)
            hint = f" (name its files to cluster them: {handle}.f*)" if isinstance(entity, (Album, Track)) else ""
            return EngineResult.failure(
                f"cluster: {handle} is neither a file nor a cluster{hint}", unresolved=unresolved
            )
    files = list(dict.fromkeys(files))
    clusters = workspace().cluster_files(files)
    items = []
    mints = []
    for cluster in clusters:
        items.append(entity_item(session, cluster, 'clustered'))
        mints.append(items[-1].handle)
    return EngineResult(items=items, mints=mints, resolved=handles_of(session, files), unresolved=unresolved)

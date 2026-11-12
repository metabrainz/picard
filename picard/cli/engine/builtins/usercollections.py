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

"""The commands on the release collections of the user: ``collection ls``, ``add`` and ``rm``.

The user has to be logged in (see ``login``). As in the GUI, the releases are
those of the albums (not the standalone recordings) and the collections are
the ones of the user, as MusicBrainz last told.
"""

from typing import Any

from picard import collection as collection_module
from picard.album import (
    Album,
    NatAlbum,
)
from picard.cli.engine.builtins.helpers import (
    TIMEOUT_SHORT,
    arg_words,
    describe_collection,
    drain,
    handles_of,
    join_notes,
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
from picard.collection import (
    Collection,
    load_user_collections,
)
from picard.config import get_config
from picard.services import services
from picard.workspace import workspace


def _unavailable(name: str) -> 'str | None':
    """Why the collections cannot be used by ``name``, or None if they can."""
    if not services().webservice.oauth_manager.is_authorized():
        return f"{name}: not logged in (see 'login')"
    if not get_config().setting['enable_user_collections']:
        return f"{name}: the user collections are disabled (option enable_user_collections)"
    return None


def _refresh(session: EngineSession, notes: list[str]) -> 'str | None':
    """Load the collections of the user again; return why that failed, or None."""
    outcome: dict[str, Any] = {}

    def loaded(error: 'str | None' = None) -> None:
        outcome['error'] = error
        outcome['done'] = True

    load_user_collections(loaded)
    drain(session, TIMEOUT_SHORT, notes, doing="loading your collections")
    if not outcome:
        return "timed out waiting for the collections"
    return outcome['error']


def _albums_in(collection: Collection) -> list[Album]:
    """The albums of the working set known to be in ``collection``."""
    return [album for album in workspace().albums.values() if type(album) is Album and album.id in collection.releases]


@command(
    'collection ls',
    usage='collection ls',
    help="List the release collections of the user.",
)
def _cmd_collection_ls(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List the release collections of the user.

    The collections are requested from MusicBrainz, so the sizes are current. Each
    gets a handle (k1, k2, ...) to use with 'collection add' and 'collection rm',
    and the albums of the working set that are in it are listed.

    A collection knows its releases only when the albums were loaded while logged
    in (with the option enable_user_collections on): an album loaded before the
    login is not shown as in its collections, whatever it is on MusicBrainz.

    Example:
      collection ls
    """
    why = _unavailable('collection ls')
    if why:
        return EngineResult.failure(why)
    notes: list[str] = []
    error = _refresh(session, notes)
    if error:
        return EngineResult.failure(f"collection ls: could not load the collections: {error}")

    items = []
    for collection in collection_module.user_collections.values():
        data = describe_collection(collection)
        data['albums'] = handles_of(session, _albums_in(collection))
        items.append(EngineItemResult(handle=session.handle_for(collection), status='collection', data=data))
    return EngineResult(
        items=items,
        resolved=[item.handle for item in items],
        mints=[item.handle for item in items],
        message=join_notes(notes),
    )


def _modify(session: EngineSession, name: str, args: dict[str, Any], adding: bool) -> EngineResult:
    """Add the albums to a collection, or remove them from it."""
    collection_sel = args.get('collection')
    album_words = arg_words(args.get('albums'))
    if not collection_sel or not album_words:
        raise UsageError
    why = _unavailable(name)
    if why:
        return EngineResult.failure(why)

    found, unresolved = session.resolve(collection_sel)
    collections = [e for e in found if isinstance(e, Collection)]
    if len(collections) != 1 or len(found) != 1:
        return EngineResult.failure(
            f"{name}: need exactly one collection (see 'collection ls')",
            unresolved=unresolved,
        )
    collection = collections[0]
    entities, album_unresolved = session.resolve(album_words)
    unresolved = unresolved + album_unresolved
    # The releases of the albums; the standalone recordings are not releases.
    albums = [e for e in entities if isinstance(e, Album) and not isinstance(e, NatAlbum)]
    if not albums:
        return EngineResult.failure(f"{name}: no album selected", unresolved=unresolved)
    release_ids = {album.id for album in albums}
    # Adding what is known to be in already is pointless; removing is not
    # filtered, as a release can be in the collection without the album knowing.
    wanted = release_ids - collection.releases if adding else release_ids
    handle = session.handle_for(collection)
    resolved = [handle, *handles_of(session, albums)]
    if not wanted:
        item = EngineItemResult(handle=handle, status='unchanged', data=describe_collection(collection))
        return EngineResult(items=[item], resolved=resolved, unresolved=unresolved)

    errors: list[str] = []

    def modified(error: 'str | None' = None) -> None:
        if error is not None:
            errors.append(error)

    notes: list[str] = []
    if adding:
        collection.add_releases(wanted, modified)
    else:
        collection.remove_releases(wanted, modified)
    drained = drain(session, TIMEOUT_SHORT, notes, doing="updating the collection")
    if errors:
        status, extra = 'failed', {'error': errors[0]}
    elif not drained:
        status, extra = 'timeout', {}
    else:
        status, extra = ('added' if adding else 'removed'), {}
        # The size the collection has now, rather than the one deduced from what
        # was sent (a release can have been in it already).
        error = _refresh(session, notes)
        if error:
            notes.append(f"could not load the collections again: {error}")
    data = {**describe_collection(collection), **extra, 'albums': handles_of(session, albums)}
    return EngineResult(
        items=[EngineItemResult(handle=handle, status=status, data=data)],
        resolved=resolved,
        unresolved=unresolved,
        message=join_notes(notes),
    )


@command(
    'collection add',
    usage='collection add <collection> <albums>',
    help="Add the releases of albums to a collection.",
    args=('collection', 'albums'),
    arg_kinds=('selector', 'selector'),
)
def _cmd_collection_add(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Add the releases of albums to a collection of the user.

    The collection is one of 'collection ls' (k1); the albums are selected as
    everywhere (a1, a*). The standalone recordings are not releases and are left
    out, as in the GUI.

    The result is added, unchanged (they were in it already), failed (with the
    reason) or timeout.

    Example:
      collection add k1 a1,a2
    """
    return _modify(session, 'collection add', args, adding=True)


@command(
    'collection rm',
    usage='collection rm <collection> <albums>',
    help="Remove the releases of albums from a collection.",
    args=('collection', 'albums'),
    arg_kinds=('selector', 'selector'),
)
def _cmd_collection_rm(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Remove the releases of albums from a collection of the user.

    The collection is one of 'collection ls' (k1); the albums are selected as
    everywhere (a1, a*). The releases are removed from the collection, not the
    albums from the working set.

    The result is removed, failed (with the reason) or timeout.

    Example:
      collection rm k1 a1
    """
    return _modify(session, 'collection rm', args, adding=False)

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

"""The commands on the release versions of an album: ``album versions`` and ``album switch``.

The versions of an album are the releases of its release group, the "Other
versions" of the GUI, in the same order (see ``alternative_versions``).
"""

from typing import Any

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cli.engine.builtins.helpers import (
    TIMEOUT_SHORT,
    arg_first,
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
from picard.cli.engine.selectors import SelectorError
from picard.cli.engine.versions import Version
from picard.releasegroup import alternative_versions
from picard.util.mbentity import parse_mb_entity
from picard.workspace import workspace


def _load_versions(album: Album, session: EngineSession, notes: list[str]) -> 'tuple[bool, str | None]':
    """Make sure the versions of the release group of ``album`` are loaded.

    Returns whether they are, and why not if the request failed. The release
    group is shared by the albums of the working set, and its versions are
    only requested once, until an album of it is reloaded.
    """
    release_group = album.release_group
    if release_group is None:
        return False, "the album has no release group"
    if not release_group.loaded:
        release_group.load_versions(lambda: None)
        drain(session, TIMEOUT_SHORT, notes, doing="loading the release versions")
    if not release_group.loaded:
        return False, None
    return True, release_group.load_error


def _versions_of(session: EngineSession, album: Album, notes: list[str]) -> EngineItemResult:
    """List the versions of one album, and mint their handles."""
    handle = session.handle_for(album)
    if isinstance(album, NatAlbum):
        return EngineItemResult(handle=handle, status='no_versions', data={'versions': []})
    if album.release_group is None:
        # Not loaded yet (or its load failed): there is no release group to ask.
        return EngineItemResult(handle=handle, status='not_loaded', data={'versions': []})

    ready, error = _load_versions(album, session, notes)
    if not ready:
        return EngineItemResult(handle=handle, status='timeout', data={'versions': []})
    if error:
        return EngineItemResult(handle=handle, status='load_failed', data={'versions': [], 'error': error})

    versions = [Version(item, group, current=item['id'] == album.id) for group, item in alternative_versions(album)]
    handles = session.set_versions(album, versions)
    data: dict[str, Any] = {
        'versions': [{'handle': h, **v.describe()} for h, v in zip(handles, versions, strict=True)],
    }
    total = album.release_group.versions_count
    if total is not None and total > len(versions):
        # The request is limited to the first releases of the group.
        data['total'] = total
    return EngineItemResult(handle=handle, status='listed', data=data)


@command(
    'album versions',
    usage='album versions <album>',
    help="List the other releases of the release group of an album.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_album_versions(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """List the versions of an album: the releases of its release group.

    This is the "Other versions" menu of the GUI, in the same order: the versions
    with as many tracks as the album first, then those of the preferred release
    countries, then those of the preferred release formats. Each gets a handle
    (v1, v2, ...) to use with 'album switch', and the one the album is now is
    marked. The versions are requested from MusicBrainz the first time.

    The handles last until the versions of the album are listed again. The album
    must be loaded; a version can be reached as a1.v2 and listed with 'ls a1.v*'.

    A version is reported as listed, not_loaded (the album is not loaded),
    no_versions (the standalone recordings have no release group), load_failed
    (the request failed) or timeout.

    Example:
      album versions a1
    """
    selector = args.get('selector')
    if not selector:
        raise UsageError
    entities, unresolved = session.resolve(selector)
    albums = [e for e in entities if isinstance(e, Album)]
    notes: list[str] = []
    items = [_versions_of(session, album, notes) for album in albums]
    mints = [version['handle'] for item in items for version in item.data['versions']]
    return EngineResult(
        items=items,
        resolved=handles_of(session, albums),
        unresolved=unresolved,
        mints=mints,
        message=join_notes(notes),
    )


def _requested_release(session: EngineSession, album: Album, text: str) -> 'tuple[str | None, str | None]':
    """The release a word of ``album switch`` names, as ``(release id, None)``, or ``(None, why not)``.

    It is a release (an MBID, ``release:<mbid>`` or a URL) or a version listed for ``album`` (v2, a1.v2).
    """
    ref = parse_mb_entity(text, default_entity='release')
    if ref is not None:
        if ref.entity != 'release':
            return None, f"{text!r} is a {ref.entity}, not a release"
        return ref.id, None
    try:
        entities, _unresolved = session.resolve(text)
    except SelectorError as exc:
        return None, f"invalid version: {exc}"
    versions = [e for e in entities if isinstance(e, Version)]
    if len(entities) != 1 or len(versions) != 1:
        return None, f"{text!r} is not a version (see 'album versions')"
    version = versions[0]
    if not any(held is version for held in session.versions_for(album)):
        return None, f"{session.handle_for(version)} is not a version listed for {session.handle_for(album)}"
    return version.release_id, None


@command(
    'album switch',
    usage='album switch <version> | <album> <version|mbid>',
    help="Switch an album to another release of its release group.",
    args=('album', 'version'),
    arg_kinds=('selector', 'selector'),
)
def _cmd_album_switch(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Switch an album to another release of its release group.

    The version is one listed by 'album versions' (v2, or a1.v2), the ID of a
    release, 'release:<id>' or the URL of a release. It has to be a release of the
    release group of the album. A listed version says which album it is of, so the
    album can be left out: 'album switch v2'. The files of the album are matched again to the
    tracks of the other release, as the GUI does.

    The album keeps its handle, unless the other release is already loaded: then
    the files go to that album, and the first one is removed from the working set.
    The result names the album that holds the files. Its versions have to be listed
    again to get new handles.

    The result says switched, unchanged (the album already is that release),
    load_failed (the release could not be loaded) or timeout.

    Examples:
      album switch v2
      album switch a1 v2
      album switch a1 release:<mbid>
    """
    album_sel = args.get('album')
    version_text = arg_first(args.get('version'))
    if not album_sel:
        raise UsageError

    entities, unresolved = session.resolve(album_sel)
    if not version_text:
        # A version alone ('v2', 'a1.v2') says which album it is of.
        versions = [e for e in entities if isinstance(e, Version)]
        owners = [session.version_owner(v) for v in versions]
        if len(entities) != 1 or len(versions) != 1 or owners[0] is None:
            raise UsageError
        entities = owners
        version_text = session.handle_for(versions[0])
    albums = [e for e in entities if isinstance(e, Album)]
    if len(albums) != 1 or len(entities) != 1:
        return EngineResult.failure("album switch: need exactly one album", unresolved=unresolved)
    album = albums[0]
    album_handle = session.handle_for(album)
    release_group = album.release_group
    if isinstance(album, NatAlbum) or release_group is None:
        return EngineResult.failure(f"album switch: {album_handle} is not a loaded release", unresolved=unresolved)

    mbid, why = _requested_release(session, album, version_text)
    if mbid is None:
        return EngineResult.failure(f"album switch: {why}", unresolved=unresolved)

    if album.has_critical_tasks():
        return EngineResult.failure(f"album switch: {album_handle} is still loading", unresolved=unresolved)

    notes: list[str] = []
    ready, error = _load_versions(album, session, notes)
    if error:
        return EngineResult.failure(f"album switch: could not get the versions: {error}", unresolved=unresolved)
    if not ready:
        return EngineResult.failure(
            "album switch: timed out waiting for the versions", unresolved=unresolved, message=join_notes(notes)
        )
    if not any(version['id'] == mbid for version in release_group.versions):
        return EngineResult.failure(
            f"album switch: release:{mbid} is not a version of {album_handle}", unresolved=unresolved
        )

    if mbid == album.id:
        item = EngineItemResult(handle=album_handle, status='unchanged', data={'entity_type': 'release', 'mbid': mbid})
        return EngineResult(items=[item], resolved=[album_handle], unresolved=unresolved)

    previous = album.id
    album.switch_release_version(mbid)
    drain(session, TIMEOUT_SHORT, notes, doing="switching the release version")

    # The files went to the album of that release: the same one, or another if it was loaded.
    target = workspace().albums.get(mbid)
    if target is None:
        return EngineResult.failure(f"album switch: release:{mbid} did not load", unresolved=unresolved)
    target_handle = session.handle_for(target)
    data: dict[str, Any] = {'entity_type': 'release', 'mbid': mbid, 'previous': previous}
    if target.errors:
        status = 'load_failed'
        data['error'] = target.errors[-1]
    elif not target.loaded:
        status = 'timeout'
    else:
        status = 'switched'
        for version in session.versions_for(target):
            version.current = version.release_id == mbid
    item = EngineItemResult(handle=target_handle, status=status, data=data)
    return EngineResult(
        items=[item],
        resolved=[album_handle],
        unresolved=unresolved,
        mints=[] if target is album else [target_handle],
        message=join_notes(notes),
    )

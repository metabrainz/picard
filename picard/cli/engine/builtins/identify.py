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

"""The commands that identify files: ``cluster``, ``cluster lookup``, ``match`` and ``lookup``."""

from typing import Any

from picard import config
from picard.album import (
    Album,
)
from picard.cli.engine.builtins.helpers import (
    TIMEOUT_LONG,
    TIMEOUT_SHORT,
    drain,
    entity_item,
    handles_of,
    join_notes,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.result import (
    EngineItemResult,
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


def _load_release(session: EngineSession, release_id: str, notes: list[str]) -> 'tuple[Album, str | None]':
    """Load a release, wait for it, and say why it did not load if it did not.

    ``load_album()`` only schedules the request. If it failed (a 503 from the
    server, say) ``album.errors`` is populated, and if it is slow the album is
    not loaded yet when we stop waiting: moving files onto it would report a
    match that did not happen. Returns the album and the reason, or None.
    """
    album = workspace().load_album(release_id)
    loaded = drain(session, TIMEOUT_SHORT, notes)
    if album.errors:
        return album, album.errors[-1]
    if not loaded and not album.loaded:
        return album, "timed out waiting for the release to load"
    return album, None


def _matched_album_handle(session: EngineSession, obj: Any, mints: list[str]) -> 'str | None':
    """The handle of the album a file has been matched to, if any; new albums are added to ``mints``."""
    album = getattr(obj.parent_item, 'album', None) if isinstance(obj, File) else None
    if album is None:
        return None
    handle = session.handle_for(album)
    if handle not in mints:
        mints.append(handle)
    return handle


def _request_error_text(http: Any, error: Any) -> str:
    """Human text for a failed web service request (as the album load reports it)."""
    try:
        return http.errorString()
    except AttributeError:
        return str(error)


def _lookup_cluster(session: EngineSession, cluster: Cluster, notes: list[str]) -> EngineItemResult:
    """Look up one cluster: capture ranked candidates, auto-apply the best.

    Issues the same release search as the GUI cluster lookup but with our own
    callback to capture all candidates, drains the request, ranks them, mints
    m handles, and auto-applies the top match (producing an album) when it
    passes the similarity floor.
    """
    captured: dict[str, Any] = {}

    def capture(document, http, error):
        captured['document'] = document
        captured['http'] = http
        captured['error'] = error

    cluster.lookup_metadata(callback=capture)
    drained = drain(session, TIMEOUT_SHORT, notes)

    if not drained and not captured:
        # No reply at all before we gave up: neither "no matches" nor a result.
        return EngineItemResult(handle=session.handle_for(cluster), status='timeout', data={'candidates': []})

    if captured.get('error'):
        # The search request itself failed (network/server error): say so
        # instead of reporting it as "no matches".
        return EngineItemResult(
            handle=session.handle_for(cluster),
            status='lookup_failed',
            data={'candidates': [], 'error': _request_error_text(captured.get('http'), captured['error'])},
        )

    document = captured.get('document')
    releases = None
    if document is not None:
        try:
            releases = document['releases']
        except (KeyError, TypeError):
            releases = None
    if not releases:
        return EngineItemResult(
            handle=session.handle_for(cluster),
            status='no_matches',
            data={'candidates': []},
        )

    settings = config.get_config().setting
    ranked, best = cluster.rank_release_candidates(
        releases,
        min_similarity=settings['match_min_similarity'],
        min_margin=settings['match_min_margin'],
    )

    applied_release = best.result.release  # None when below floor
    candidates = [Candidate(m, applied=(m.release is applied_release and applied_release is not None)) for m in ranked]
    candidate_handles = session.set_candidates(cluster, candidates)

    matched_album_handle = None
    load_error = None
    if applied_release is not None:
        album, load_error = _load_release(session, applied_release['id'], notes)
        if load_error is None:
            # cluster.files is typed as generic metadata items; only File here.
            files = [f for f in cluster.files if isinstance(f, File)]
            workspace().move_files_to_album(files, album=album)
            matched_album_handle = session.handle_for(album)

    if matched_album_handle:
        status = 'matched'
    elif load_error is not None:
        status = 'load_failed'
    else:
        status = 'no_confident_match'

    data = {
        'reason': best.reason,
        'matched_album': matched_album_handle,
        'candidates': [{'handle': h, **c.describe()} for h, c in zip(candidate_handles, candidates, strict=True)],
    }
    if load_error is not None:
        data['error'] = load_error
    return EngineItemResult(
        handle=session.handle_for(cluster),
        status=status,
        data=data,
    )


@command(
    'cluster lookup',
    usage='cluster lookup [selector]',
    help="Look clusters up on MusicBrainz.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_cluster_lookup(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Look clusters up on MusicBrainz, and apply the best match.

    Without a selector all the clusters are looked up. The releases found for a
    cluster are ranked: if the best one is confident enough it is loaded and the
    files of the cluster are matched to it. The other releases are kept as
    candidates (m1, m2, ...): the console shows the best ten, 'ls c1.m*' lists
    them all, and 'match' applies another one.

    A cluster is reported as matched, no_confident_match, no_matches (nothing was
    found), lookup_failed (the request failed), load_failed (the release could not
    be loaded) or timeout.

    Example:
      cluster lookup c1
    """
    selector = args.get('selector') or 'c*'
    entities, unresolved = session.resolve(selector)
    clusters = [e for e in entities if isinstance(e, Cluster)]
    notes: list[str] = []
    items = [_lookup_cluster(session, cluster, notes) for cluster in clusters]
    mints = []
    for item in items:
        if item.data.get('matched_album'):
            mints.append(item.data['matched_album'])
        mints.extend(c['handle'] for c in item.data.get('candidates', []))
    return EngineResult(
        items=items,
        resolved=handles_of(session, clusters),
        unresolved=unresolved,
        mints=mints,
        message=join_notes(notes),
    )


@command(
    'match',
    usage='match <cluster> <candidate>',
    help="Apply another candidate of a cluster lookup.",
    args=('target', 'candidate'),
    arg_kinds=('selector', 'handle'),
)
def _cmd_match(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Apply another candidate of a cluster lookup.

    'match c1 m2' loads the release of candidate m2, moves the files of cluster c1
    onto it and marks m2 as the applied candidate. A candidate can only be applied
    to the cluster it was found for; 'ls c1.m*' lists them.

    Example:
      match c1 m2
    """
    target_sel = args.get('target')
    candidate_sel = args.get('candidate')
    if not target_sel or not candidate_sel:
        raise UsageError

    targets, target_unresolved = session.resolve(target_sel)
    cands, cand_unresolved = session.resolve(candidate_sel)
    unresolved = target_unresolved + cand_unresolved

    clusters = [e for e in targets if isinstance(e, Cluster)]
    candidates = [c for c in cands if isinstance(c, Candidate)]
    if len(clusters) != 1 or len(candidates) != 1:
        return EngineResult.failure(
            "match: need exactly one target cluster and one candidate",
            unresolved=unresolved,
        )
    cluster = clusters[0]
    candidate = candidates[0]
    if candidate.release_id is None:
        return EngineResult.failure("match: candidate has no release", unresolved=unresolved)
    # A candidate is only an alternative for the cluster it was looked up for.
    if not any(c is candidate for c in session.candidates_for(cluster)):
        return EngineResult.failure(
            f"match: {session.handle_for(candidate)} is not a candidate of {session.handle_for(cluster)}",
            unresolved=unresolved,
        )

    notes: list[str] = []
    album, load_error = _load_release(session, candidate.release_id, notes)
    if load_error is not None:
        return EngineResult.failure(f"match: release load failed: {load_error}", unresolved=unresolved)
    workspace().move_files_to_album(cluster.files, album=album)

    # Reflect the new selection in the target's candidate set.
    for c in session.candidates_for(cluster):
        c.applied = c is candidate

    album_handle = session.handle_for(album)
    return EngineResult(
        items=[
            EngineItemResult(
                handle=session.handle_for(cluster),
                status='matched',
                data={'matched_album': album_handle, 'candidate': session.handle_for(candidate)},
            )
        ],
        resolved=[session.handle_for(cluster)],
        unresolved=unresolved,
        mints=[album_handle],
    )


@command(
    'lookup',
    usage='lookup [selector]',
    help="Look objects up on MusicBrainz from their tags.",
    args=('selector',),
    arg_kinds=('selector',),
)
def _cmd_lookup(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Look objects up on MusicBrainz from their current tags.

    This is the Lookup action of the GUI: a cluster or a file is matched to a
    release or a recording, and moved onto it. Without a selector it applies to
    everything at the top level. Each object is reported as matched, with its album,
    or done. 'cluster lookup' keeps the alternatives.

    Example:
      lookup c1
    """
    selector = args.get('selector') or '*'
    entities, unresolved = session.resolve(selector)
    taggable = [e for e in entities if getattr(e, 'can_autotag', False)]
    if not taggable:
        return EngineResult(items=[], resolved=handles_of(session, entities), unresolved=unresolved)

    workspace().autotag(taggable)
    # autotag dispatches async web lookups (and album loads on a match); drain.
    notes: list[str] = []
    drain(session, TIMEOUT_LONG, notes)

    items = []
    mints = []
    for obj in taggable:
        album_handle = _matched_album_handle(session, obj, mints)
        data = {'album': album_handle} if album_handle else {}
        status = 'matched' if album_handle else 'done'
        items.append(EngineItemResult(handle=session.handle_for(obj), status=status, data=data))
    return EngineResult(
        items=items,
        mints=mints,
        resolved=handles_of(session, taggable),
        unresolved=unresolved,
        message=join_notes(notes),
    )

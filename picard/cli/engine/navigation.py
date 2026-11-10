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

"""Walk the working set by selector path (``a1.d2.t3``, ``c1.f*``, ``u.f*``).

:class:`PathNavigator` implements the :class:`~picard.cli.engine.selectors.Navigator`
protocol for the real entity types. What each segment means under each parent:

=============  =========================================================
parent         children
=============  =========================================================
(root)         ``u``: the files not in any cluster
album          ``d``: a disc; ``t``: a track; ``f``: any of its files;
               ``u``: its unmatched files
disc           ``t``: a track on that disc; ``f``: its files
track          ``f``: the files matched to it
cluster        ``f``: its files; ``m``: its lookup candidates
file           ``m``: its lookup candidates
=============  =========================================================

Numbers are positions in the listing order, except for discs and tracks of a
release, which use the numbers MusicBrainz gives them (the ``discnumber`` and
``tracknumber`` tags): ``a1.d2.t3`` is track 3 of disc 2, and that survives an
album reload. Picard has no disc object, so ``d`` is a view: a disc is not an
entity of its own and a path ending at one stands for its tracks (likewise, a
path ending at a bucket stands for its files).

A release with a single disc may leave the disc out (``a1.t3``); with several
it must say which one, as guessing could hit the wrong disc. Non-album tracks
have no numbers, so they are numbered by position and have no discs.
"""

from collections.abc import (
    Callable,
    Iterable,
)
from typing import Any

from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.selectors import (
    Segment,
    SelectorError,
)
from picard.cluster import Cluster
from picard.file import File
from picard.track import Track
from picard.workspace import workspace


class DiscView:
    """One disc of an album: a view over the album's tracks, not an entity."""

    __slots__ = ('album', 'number')

    def __init__(self, album: Album, number: int):
        self.album = album
        self.number = number

    @property
    def tracks(self) -> list[Track]:
        return [track for track in self.album.tracks if _disc_of(track) == self.number]


def _int_or_none(value: Any) -> 'int | None':
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _disc_of(track: Track) -> int:
    """The disc number of ``track``; a release without disc numbers has one disc."""
    disc = _int_or_none(track.metadata['discnumber'])
    return 1 if disc is None else disc


def _number_of(track: Track) -> 'int | None':
    return _int_or_none(track.metadata['tracknumber'])


def _is_numbered(album: Album) -> bool:
    """True if every track has a track number (releases do, non-album tracks do not)."""
    return bool(album.tracks) and all(_number_of(track) is not None for track in album.tracks)


def _disc_numbers(album: Album) -> list[int]:
    return sorted({_disc_of(track) for track in album.tracks})


def _files_of_tracks(tracks: Iterable[Track]) -> list[File]:
    return [file for track in tracks for file in track.files if isinstance(file, File)]


# The most numbered segments offered when completing under one container.
_MAX_COMPLETIONS = 100


def _numbered(prefix: str, count: int) -> list[str]:
    """``prefix1`` ... ``prefixN`` (at most :data:`_MAX_COMPLETIONS` of them)."""
    return [f"{prefix}{number}" for number in range(1, min(count, _MAX_COMPLETIONS) + 1)]


def _position(items: Iterable, item: Any) -> 'int | None':
    """The 1-based position of ``item`` in ``items`` (by identity), or None."""
    for position, candidate in enumerate(items, 1):
        if candidate is item:
            return position
    return None


def _positional(items: list, segment: Segment) -> list:
    """Select from ``items`` by 1-based position (ordinal) or all of them (wildcard)."""
    if segment.kind == 'wildcard':
        return list(items)
    position = segment.value
    return [items[position - 1]] if 1 <= position <= len(items) else []


def _unsupported(parent: str, segment: Segment) -> SelectorError:
    return SelectorError(f"'{segment.prefix}' is not valid under {parent}")


class PathNavigator:
    """Navigator over the working set (see the module docstring for the rules)."""

    def __init__(
        self,
        candidates_for: Callable[[Any], list],
        candidate_owner: 'Callable[[Candidate], Any] | None' = None,
    ):
        """``candidates_for(target)`` returns the lookup candidates held for ``target``;
        ``candidate_owner(candidate)`` the target a candidate was found for.
        """
        self._candidates_for = candidates_for
        self._candidate_owner = candidate_owner

    # --- Navigator protocol -------------------------------------------------

    def step(self, node: Any, segment: Segment) -> list:
        if node is None:
            if segment.prefix == 'u':
                return [workspace().unclustered_files]
            raise SelectorError(f"'{segment.prefix}' cannot start a path")
        if isinstance(node, Album):
            return self._album_children(node, segment)
        if isinstance(node, DiscView):
            return self._disc_children(node, segment)
        if isinstance(node, Track):
            return self._track_children(node, segment)
        if isinstance(node, Cluster):
            return self._cluster_children(node, segment)
        if isinstance(node, File):
            return self._file_children(node, segment)
        raise SelectorError("a candidate has no children")

    def finish(self, node: Any) -> list:
        if isinstance(node, DiscView):
            return node.tracks
        if isinstance(node, Cluster) and node.special:
            return list(node.files)
        return [node]

    def segments(self, node: Any) -> list[str]:
        """The segments that can follow ``node``, as text (``t*``, ``d2``, ``f1``, ...).

        Wildcards come first. Numbered segments are capped, so completing under
        a container with thousands of files stays usable.
        """
        if isinstance(node, Album):
            return self._album_segments(node)
        if isinstance(node, DiscView):
            tracks = node.tracks
            numbers = [_number_of(track) for track in tracks]
            return ['t*', 'f*'] + [f"t{number}" for number in numbers[:_MAX_COMPLETIONS] if number is not None]
        if isinstance(node, Track):
            return ['f*', *_numbered('f', len(node.files))]
        if isinstance(node, Cluster):
            segments = ['f*', *_numbered('f', len(node.files))]
            candidates = [] if node.special else self._candidates_for(node)
            if candidates:
                segments += ['m*', *_numbered('m', len(candidates))]
            return segments
        if isinstance(node, File):
            candidates = self._candidates_for(node)
            return ['m*', *_numbered('m', len(candidates))] if candidates else []
        return []

    def _album_segments(self, album: Album) -> list[str]:
        segments = ['f*', 'u']
        if not album.tracks:
            return segments
        if not _is_numbered(album):
            return [*segments, 't*', *_numbered('t', len(album.tracks))]
        discs = _disc_numbers(album)
        segments += ['d*', *(f"d{number}" for number in discs[:_MAX_COMPLETIONS]), 't*']
        if len(discs) == 1:
            # With one disc a track needs no disc (with several it would be ambiguous).
            segments += [f"t{_number_of(track)}" for track in album.tracks[:_MAX_COMPLETIONS]]
        return segments

    # --- where an entity is now -------------------------------------------------

    def path_of(self, entity: Any, handle_for: Callable[[Any], str]) -> 'str | None':
        """The path that currently reaches ``entity``, or None.

        The inverse of resolving a path: tracks, files and candidates sit at a
        position under a container (``a1.d2.t3``, ``c1.f2``, ``c1.m1``). Albums
        and clusters are reached by their plain handle, so they have no path.
        ``handle_for`` supplies the handle of the container the path starts from.
        """
        if isinstance(entity, Track):
            return self._track_path(entity, handle_for)
        if isinstance(entity, File):
            return self._file_path(entity, handle_for)
        if isinstance(entity, Candidate):
            return self._candidate_path(entity, handle_for)
        return None

    def _track_path(self, track: Track, handle_for: Callable[[Any], str]) -> 'str | None':
        album = track.album
        if album is None:
            return None
        position = _position(album.tracks, track)
        if position is None:
            return None
        base = handle_for(album)
        if not _is_numbered(album):
            return f"{base}.t{position}"
        # The shortest form that resolves: the disc is only named when needed.
        if len(_disc_numbers(album)) > 1:
            return f"{base}.d{_disc_of(track)}.t{_number_of(track)}"
        return f"{base}.t{_number_of(track)}"

    def _file_path(self, file: File, handle_for: Callable[[Any], str]) -> 'str | None':
        parent = file.parent_item
        if parent is None:
            return None
        position = _position(parent.files, file)
        if position is None:
            return None
        if isinstance(parent, Track):
            base = self._track_path(parent, handle_for)
            return None if base is None else f"{base}.f{position}"
        if isinstance(parent, Cluster):
            if parent is workspace().unclustered_files:
                return f"u.f{position}"
            if parent.special:
                # The unmatched files of an album.
                return None if parent.album is None else f"{handle_for(parent.album)}.u.f{position}"
            return f"{handle_for(parent)}.f{position}"
        return None

    def _candidate_path(self, candidate: Candidate, handle_for: Callable[[Any], str]) -> 'str | None':
        if self._candidate_owner is None:
            return None
        owner = self._candidate_owner(candidate)
        if owner is None:
            return None
        position = _position(self._candidates_for(owner), candidate)
        return None if position is None else f"{handle_for(owner)}.m{position}"

    # --- children of each kind of node -----------------------------------------

    def _album_children(self, album: Album, segment: Segment) -> list:
        prefix = segment.prefix
        if prefix == 'u':
            return [album.unmatched_files]
        if prefix == 'f':
            files = _files_of_tracks(album.tracks) + list(album.unmatched_files.files)
            return _positional(files, segment)
        if prefix not in {'t', 'd'}:
            raise _unsupported('an album', segment)
        if not album.loaded:
            raise SelectorError("the album is not loaded")
        if not album.tracks:
            return []
        if not _is_numbered(album):
            if prefix == 'd':
                raise SelectorError("the album has no disc numbers")
            return _positional(list(album.tracks), segment)

        discs = _disc_numbers(album)
        if prefix == 'd':
            if segment.kind == 'wildcard':
                return [DiscView(album, number) for number in discs]
            return [DiscView(album, segment.value)] if segment.value in discs else []

        # A track of the release itself, with no disc given.
        if segment.kind == 'wildcard':
            return list(album.tracks)
        if len(discs) > 1:
            listed = ', '.join(str(number) for number in discs)
            raise SelectorError(
                f"the album has {len(discs)} discs ({listed}); say which, e.g. 'd{discs[0]}.t{segment.value}'"
            )
        return [track for track in album.tracks if _number_of(track) == segment.value]

    def _disc_children(self, disc: DiscView, segment: Segment) -> list:
        tracks = disc.tracks
        if segment.prefix == 't':
            if segment.kind == 'wildcard':
                return tracks
            return [track for track in tracks if _number_of(track) == segment.value]
        if segment.prefix == 'f':
            return _positional(_files_of_tracks(tracks), segment)
        raise _unsupported('a disc', segment)

    def _track_children(self, track: Track, segment: Segment) -> list:
        if segment.prefix == 'f':
            return _positional(_files_of_tracks([track]), segment)
        raise _unsupported('a track', segment)

    def _cluster_children(self, cluster: Cluster, segment: Segment) -> list:
        if segment.prefix == 'f':
            return _positional([file for file in cluster.files if isinstance(file, File)], segment)
        if segment.prefix == 'm' and not cluster.special:
            return _positional(self._candidates_for(cluster), segment)
        raise _unsupported('a cluster', segment)

    def _file_children(self, file: File, segment: Segment) -> list:
        if segment.prefix == 'm':
            return _positional(self._candidates_for(file), segment)
        raise _unsupported('a file', segment)

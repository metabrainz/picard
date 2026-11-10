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

"""In-process (headless) implementation of the engine session.

:class:`LocalEngineSession` composes the engine substrate — a
:class:`~picard.cli.engine.handles.HandleRegistry` and the selector resolver —
over a running :class:`~picard.cli.headless.HeadlessTagger` and its
:class:`~picard.workspace.Workspace`. It satisfies the
:class:`~picard.cli.engine.commands.EngineSession` protocol, so commands run
against it unchanged in headless mode; a future ``RemoteEngineSession`` will
satisfy the same protocol by proxying to a running GUI.

This module owns the one piece that must know the concrete entity types: the
handle-prefix CLASSIFIER (entity -> 'f'/'c'/'a'/'t') and the prefix ENUMERATOR
(prefix -> live entities from the Workspace). Everything else is
type-agnostic.
"""

from collections.abc import (
    Iterable,
    Sequence,
)
from typing import Any
from weakref import WeakKeyDictionary

from picard import collection
from picard.album import Album
from picard.cli.engine.candidates import Candidate
from picard.cli.engine.handles import HandleRegistry
from picard.cli.engine.navigation import PathNavigator
from picard.cli.engine.options import SessionOptions
from picard.cli.engine.selectors import (
    SelectorError,
    resolve_nodes,
    resolve_selector,
)
from picard.cli.engine.versions import Version
from picard.cluster import (
    Cluster,
    UnclusteredFiles,
)
from picard.collection import Collection
from picard.file import File
from picard.track import Track
from picard.workspace import workspace


def classify_entity(entity: Any) -> 'str | None':
    """Map a working-set entity to its handle prefix, or None if not handleable.

    Order matters only where it clarifies intent; the types are otherwise
    disjoint. ``UnclusteredFiles`` is a ``Cluster`` subclass but is the
    unclustered bucket, not a user cluster, so it is NOT handleable as ``c``.
    ``NatAlbum`` is an ``Album`` ('a'); ``NonAlbumTrack`` is a ``Track`` ('t').
    A lookup match :class:`Candidate` is minted as ``m``, a release
    :class:`Version` as ``v``, a :class:`Collection` as ``k``.
    """
    if isinstance(entity, File):
        return 'f'
    if isinstance(entity, Album):
        return 'a'
    if isinstance(entity, UnclusteredFiles):
        return None
    if isinstance(entity, Cluster):
        return 'c'
    if isinstance(entity, Track):
        return 't'
    if isinstance(entity, Candidate):
        return 'm'
    if isinstance(entity, Version):
        return 'v'
    if isinstance(entity, Collection):
        return 'k'
    return None


class LocalEngineSession:
    """Headless EngineSession backed by HeadlessTagger + Workspace."""

    def __init__(self, app):
        """``app`` is the HeadlessTagger owning the Workspace and thread pools."""
        self._app = app
        self._handles = HandleRegistry(classify_entity)
        # Current lookup candidates, keyed (weakly) by the looked-up target
        # (cluster/file). The candidates themselves are held with strong refs so
        # their m-handles stay live; replaced on the next lookup of that target
        # (transient semantics) and dropped when the target leaves the working
        # set and is collected. Keying by the object, not id(), also means a
        # new target can never inherit a dead target's candidates.
        self._candidates: WeakKeyDictionary[Any, list[Candidate]] = WeakKeyDictionary()
        # Likewise the versions of the release group of an album (``album versions``).
        self._versions: WeakKeyDictionary[Any, list[Version]] = WeakKeyDictionary()
        # The options of the session: values set for it, over the configuration.
        self._options = SessionOptions()
        # Walks selector paths (a1.d2.t3, c1.f*, ...) through the working set.
        self._navigator = PathNavigator(
            self.candidates_for,
            self._candidate_owner,
            self.versions_for,
            self.version_owner,
        )

    # --- candidates ---------------------------------------------------------

    def set_candidates(self, target: Any, candidates: list[Candidate]) -> list[str]:
        """Replace the candidates for ``target`` and return their m handles.

        Dropping the previous candidate list lets the old m handles expire.
        """
        self._candidates[target] = candidates
        return [self._handles.handle_for(c) for c in candidates]

    def candidates_for(self, target: Any) -> list[Candidate]:
        """Return the current candidates held for ``target`` (may be empty)."""
        return self._candidates.get(target, [])

    def _candidate_owner(self, candidate: Candidate) -> Any:
        """The target ``candidate`` was found for, or None if it is no longer held."""
        for target, candidates in list(self._candidates.items()):
            if any(held is candidate for held in candidates):
                return target
        return None

    # --- versions -----------------------------------------------------------

    def set_versions(self, album: Any, versions: list[Version]) -> list[str]:
        """Replace the versions held for ``album`` and return their v handles.

        Dropping the previous versions lets the old v handles expire.
        """
        self._versions[album] = versions
        return [self._handles.handle_for(v) for v in versions]

    def versions_for(self, album: Any) -> list[Version]:
        """Return the current versions held for ``album`` (may be empty)."""
        return self._versions.get(album, [])

    def version_owner(self, version: Version) -> Any:
        """The album ``version`` was listed for, or None if it is no longer held."""
        for album, versions in list(self._versions.items()):
            if any(held is version for held in versions):
                return album
        return None

    # --- EngineSession protocol ---------------------------------------------

    def resolve(self, selector: 'str | Sequence[str]') -> 'tuple[list[Any], list[str]]':
        """Resolve a selector (a string, or the words of a command line) to ``(entities, unresolved_tokens)``."""
        return resolve_selector(selector, self._handles.resolve, self.enumerate_prefix, self._navigator)

    def resolve_targets(self, selector: str) -> list[Any]:
        """Resolve one selector term to the places it names, without expanding them.

        :meth:`resolve` turns a path ending at a disc or a bucket into its tracks
        or files, which is what a command acting on them wants. A command that
        puts things *into* a place (``move``) needs the place itself: ``u`` is
        the unclustered bucket, not the files in it. Returns ``[]`` if nothing
        matches; raises :class:`SelectorError` unless ``selector`` is one term.
        """
        return resolve_nodes(selector, self._handles.resolve, self.enumerate_prefix, self._navigator)

    def handle_for(self, entity: Any) -> str:
        """Return (minting if needed) the session handle for ``entity``."""
        return self._handles.handle_for(entity)

    def option_names(self) -> list[str]:
        """The names of all the options, sorted, for completion."""
        return self._options.names()

    def list_options(self, pattern: 'str | None' = None) -> list[dict[str, Any]]:
        """Describe the options matching ``pattern`` (all those not at their default without one)."""
        return self._options.matching(pattern)

    def describe_option(self, name: str) -> dict[str, Any]:
        """Describe one option: value, default, type, title and where the value comes from."""
        return self._options.describe(name)

    def set_option(self, name: str, text: str) -> dict[str, Any]:
        """Set an option for this session only, from its text form; describe it."""
        return self._options.set(name, text)

    def unset_option(self, name: str) -> dict[str, Any]:
        """Forget the session's value of an option; describe it."""
        return self._options.unset(name)

    def save_options(self, names: 'list[str] | None' = None) -> list[dict[str, Any]]:
        """Write the options set in this session (or just ``names``) to the configuration."""
        return self._options.save(names)

    def path_of(self, handle: str) -> 'str | None':
        """Where the entity of ``handle`` currently sits, as a selector path, or None."""
        try:
            entities, _unresolved = self.resolve(handle)
        except SelectorError:
            return None
        if not entities:
            return None
        return self._navigator.path_of(entities[0], self.handle_for)

    def path_segments(self, base: str) -> list[str]:
        """The segments that can follow the path ``base`` (``a1`` -> ``d*``, ``t*``, ``u``, ...)."""
        try:
            nodes = resolve_nodes(base, self._handles.resolve, self.enumerate_prefix, self._navigator)
        except SelectorError:
            return []
        return list(dict.fromkeys(segment for node in nodes for segment in self._navigator.segments(node)))

    def enumerate_prefix(self, prefix: str) -> Iterable[Any]:
        """Yield the live entities of a handle prefix, in a stable order."""
        wks = workspace()
        if prefix == 'f':
            return list(wks.unclustered_files.files)
        if prefix == 'c':
            return list(wks.clusters)
        if prefix == 'a':
            return list(wks.albums.values())
        if prefix == 't':
            return [track for album in wks.albums.values() for track in album.tracks]
        if prefix == 'm':
            # All candidates currently held across lookups, in mint order.
            return [c for candidates in self._candidates.values() for c in candidates]
        if prefix == 'v':
            # All versions currently held, in mint order.
            return [v for versions in self._versions.values() for v in versions]
        if prefix == 'k':
            # The collections of the user, as last loaded.
            return list(collection.user_collections.values())
        return []

    def run_until_idle(self, timeout: float | None = None) -> bool:
        """Drain async work (thread pools, pending requests) to completion."""
        return self._app.run_until_idle(timeout=timeout)

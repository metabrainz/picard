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

"""Session-local handles for working-set entities.

A headless session needs short, stable names to refer to the entities it holds
(files, clusters, albums, ...) across a sequence of commands — e.g. ``cluster``
returns ``c1``/``c2`` and a later ``lookup c1`` refers back to the same cluster.

:class:`HandleRegistry` mints a handle (a type prefix + a monotonically
increasing ordinal, e.g. ``f1``, ``c2``, ``a3``) the first time an entity is
seen, and returns the SAME handle on subsequent requests for that entity. Key
properties (see the design spec):

- Handles are STABLE IDS, never positions: removing ``a3`` then ``a4`` does not
  renumber anything; ordinals are never reused within a session.
- Backed by weak references, so when an entity leaves the working set and is
  garbage-collected its handle stops resolving (returns ``None``) rather than
  pinning the dead entity alive.
- The prefix for an entity is decided by an injectable classifier, so new
  entity kinds (match candidates ``m``, release versions ``v``, ...) can be
  added without changing this class.

This is frontend-agnostic session state: both the console and the MCP frontend
resolve the same handles through one registry.
"""

from collections.abc import Callable
import itertools
from typing import Any
from weakref import (
    WeakKeyDictionary,
    WeakValueDictionary,
)


# A classifier maps an entity to its handle prefix (a short lowercase tag), or
# returns None if the entity is not handle-able. Injected so the registry does
# not hard-code the core entity types (keeps this independent of picard.album
# etc. and lets new kinds be added later).
Classifier = Callable[[Any], 'str | None']


class HandleRegistry:
    """Mints and resolves session-local entity handles.

    Thread-affinity: intended to be used from the engine's main thread (the
    same thread that mutates the Workspace); it is not internally locked.
    """

    __slots__ = ('_classify', '_counters', '_by_handle', '_by_entity')

    def __init__(self, classifier: Classifier):
        self._classify = classifier
        # prefix -> count-up iterator (ordinals start at 1, never reused)
        self._counters: dict[str, itertools.count] = {}
        # handle -> entity (weak: entity GC'd when removed from the workspace)
        self._by_handle: WeakValueDictionary[str, Any] = WeakValueDictionary()
        # entity -> handle (weak keys: same entity yields the same handle)
        self._by_entity: WeakKeyDictionary[Any, str] = WeakKeyDictionary()

    def handle_for(self, entity: Any) -> str:
        """Return the handle for ``entity``, minting one on first request.

        Raises :class:`ValueError` if the classifier does not recognise the
        entity (no prefix).
        """
        existing = self._by_entity.get(entity)
        if existing is not None:
            return existing
        prefix = self._classify(entity)
        if not prefix:
            raise ValueError(f"No handle prefix for entity {entity!r}")
        counter = self._counters.get(prefix)
        if counter is None:
            counter = itertools.count(1)
            self._counters[prefix] = counter
        handle = f"{prefix}{next(counter)}"
        self._by_handle[handle] = entity
        self._by_entity[entity] = handle
        return handle

    def resolve(self, handle: str) -> Any | None:
        """Return the entity for ``handle``, or ``None`` if unknown/expired.

        Returns ``None`` both for a handle that was never minted and for one
        whose entity has since left the working set (and been collected).
        """
        return self._by_handle.get(handle)

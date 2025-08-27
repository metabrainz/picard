# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Script-based provider with caching and performance thresholds."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import re
from time import perf_counter
from weakref import WeakKeyDictionary

from picard import log
from picard.item import Item
from picard.script import ScriptParser

from picard.ui.itemviews.custom_columns.context import ContextStrategyManager
from picard.ui.itemviews.custom_columns.resolve import ValueResolverChain


class ChainedValueProvider:
    """Provide script-evaluated values with caching and performance limits.

    Caching strategy
    ----------------
    - Primary cache: WeakKeyDictionary keyed by the item when it supports
      weak references. This avoids retaining objects strongly.
    - Fallback id-cache: A bounded FIFO cache keyed by ``id(obj)`` for
      objects that cannot be weakly referenced. Evictions use O(1)
      ``deque.popleft``.
    """

    def __init__(
        self,
        script: str,
        max_runtime_ms: int = 25,
        cache_size: int = 1024,
        *,
        parser: ScriptParser | None = None,
        parser_factory: Callable[[], ScriptParser] | None = None,
    ):
        """Initialize provider.

        Parameters
        ----------
        script
            Scripting expression to evaluate.
        max_runtime_ms
            Limit execution time for caching.
        cache_size
            Set size of the fallback id-based cache.
        """
        self._script = script
        self._max_runtime_ms = max_runtime_ms

        self._context_manager = ContextStrategyManager()
        # Reuse a parser instance or factory through resolver chain
        self._value_resolver = ValueResolverChain(parser=parser, parser_factory=parser_factory)

        self._cache: WeakKeyDictionary[Item, str] = WeakKeyDictionary()
        self._id_cache: dict[int, str] = {}
        self._id_order: deque[int] = deque()
        self._id_cache_max = max(16, int(cache_size))

        m = re.fullmatch(r"%([a-zA-Z0-9_]+)%", script)
        self._simple_var: str | None = m.group(1) if m else None

    def evaluate(self, obj: Item) -> str:
        """Evaluate script for item.

        Parameters
        ----------
        obj
            The item to evaluate.

        Returns
        -------
        str
            Computed value (empty on failure).
        """
        can_cache = True
        avoid_cache_for_obj = False
        try:
            if obj in self._cache:
                return self._cache[obj]
        except TypeError as e:
            log.debug("Weak cache lookup failed (non-weakrefable object): %r", e)
            can_cache = False
        # Avoid caching for album-like objects that are not fully loaded yet
        if bool(getattr(obj, "is_album_like", False)) and not getattr(obj, "loaded", True):
            avoid_cache_for_obj = True

        obj_id = id(obj)
        if not can_cache:
            cached = self._id_cache.get(obj_id)
            if cached is not None:
                return cached

        start = perf_counter()

        ctx, file_obj = self._context_manager.make_context(obj)
        result = self._value_resolver.resolve_value(obj, self._simple_var, self._script, ctx, file_obj)

        elapsed_ms = (perf_counter() - start) * 1000.0
        should_cache = (result != "") and (elapsed_ms <= self._max_runtime_ms) and not avoid_cache_for_obj
        if can_cache and should_cache:
            try:
                self._cache[obj] = result
            except TypeError:
                pass
        elif not can_cache and should_cache:
            self._id_cache[obj_id] = result
            self._id_order.append(obj_id)
            if len(self._id_order) > self._id_cache_max:
                oldest = self._id_order.popleft()
                self._id_cache.pop(oldest, None)

        return result

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        cls_name = self.__class__.__name__
        return (
            f"{cls_name}(script={self._script!r}, max_runtime_ms={self._max_runtime_ms}, "
            f"cache_size={self._id_cache_max})"
        )

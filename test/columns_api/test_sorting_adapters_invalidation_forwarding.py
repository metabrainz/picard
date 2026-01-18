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

"""Tests for sorting adapters' invalidation forwarding."""

from __future__ import annotations

from typing import Protocol

import pytest

from picard.ui.columns import (
    ColumnAlign,
    ColumnSortType,
)
from picard.ui.itemviews.custom_columns import (
    CachedSortAdapter,
    CasefoldSortAdapter,
    CustomColumn,
)


class _CacheInvalidatable(Protocol):
    def invalidate(self, obj: object | None = None) -> None:  # pragma: no cover - protocol
        ...


class _ValueItem:
    def __init__(self, value: str) -> None:
        self.value = value


class _SpyProvider:
    def __init__(self) -> None:
        self.calls: list[object | None] = []

    def evaluate(self, obj: _ValueItem) -> str:
        return obj.value

    # CacheInvalidatable-compatible API
    def invalidate(self, obj: object | None = None) -> None:  # type: ignore[override]
        self.calls.append(obj)


@pytest.mark.parametrize(
    "adapter_factory",
    [
        lambda base: CasefoldSortAdapter(base),
        lambda base: CachedSortAdapter(base),
    ],
)
def test_adapter_invalidate_forwards_to_base(adapter_factory) -> None:
    spy = _SpyProvider()
    adapter = adapter_factory(spy)

    a = _ValueItem("A")

    # Forward single-item invalidation
    adapter.invalidate(a)
    # Forward full invalidation
    adapter.invalidate(None)

    assert spy.calls == [a, None]


def test_cached_sort_adapter_invalidate_forwards_and_recomputes() -> None:
    spy = _SpyProvider()
    adapter = CachedSortAdapter(spy)

    it = _ValueItem("B")
    # Populate cache
    key1 = adapter.sort_key(it)
    assert key1 == "b"

    # Change value; still cached until invalidated
    it.value = "Z"
    assert adapter.sort_key(it) == "b"

    # Invalidate and ensure base received invalidation, and key recomputed
    adapter.invalidate(it)
    assert spy.calls == [it]
    assert adapter.sort_key(it) == "z"


def test_custom_column_invalidate_cache_delegates_through_adapter() -> None:
    spy = _SpyProvider()
    adapter = CasefoldSortAdapter(spy)
    col = CustomColumn(
        title="T",
        key="k",
        provider=adapter,
        width=None,
        align=ColumnAlign.LEFT,
        sort_type=ColumnSortType.SORTKEY,
        always_visible=False,
    )

    a = _ValueItem("a")
    col.invalidate_cache(None)
    col.invalidate_cache(a)

    assert spy.calls == [None, a]

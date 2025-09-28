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

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from picard.item import Item
from picard.metadata import Metadata

import pytest

from picard.ui.columns import (
    ColumnAlign,
    ColumnSortType,
)
from picard.ui.itemviews.custom_columns import CustomColumn
from picard.ui.itemviews.custom_columns.protocols import ColumnValueProvider
from picard.ui.itemviews.custom_columns.script_provider import ChainedValueProvider
from picard.ui.itemviews.custom_columns.sorting_adapters import CachedSortAdapter


# --- Fixtures and helpers ----------------------------------------------------


@dataclass
class _FakeItem:
    values: dict[str, str]

    def column(self, key: str) -> str:
        return self.values.get(key, "")

    @property
    def metadata(self) -> Metadata:
        md = Metadata()
        for k, v in self.values.items():
            md[k] = v
        return md


class _NonWeakRefable:
    def __init__(self, artist: str) -> None:
        self.artist = artist

    def column(self, key: str) -> str:
        return self.artist if key == "artist" else ""

    @property
    def metadata(self) -> Metadata:
        md = Metadata()
        md["artist"] = self.artist
        return md


@pytest.fixture(params=["weak", "nonweak"])
def item_factory(request: pytest.FixtureRequest) -> Callable[[str], object]:
    def _make(initial_value: str) -> object:
        if request.param == "weak":
            return _FakeItem(values={"artist": initial_value})
        return _NonWeakRefable(initial_value)

    return _make


# --- Tests: provider invalidation --------------------------------------------


def test_chained_provider_invalidate_single_and_all(item_factory: Callable[[str], Item]) -> None:
    provider = ChainedValueProvider("%artist%", max_runtime_ms=1000)
    obj = item_factory("Artist A")

    # Initial evaluation and cache
    assert provider.evaluate(obj) == "Artist A"

    # Change underlying value; still cached until invalidated
    if isinstance(obj, _FakeItem):
        obj.values["artist"] = "Artist B"
    else:
        obj.artist = "Artist B"  # type: ignore[attr-defined]
    assert provider.evaluate(obj) == "Artist A"

    # Invalidate for this object only
    provider.invalidate(obj)
    assert provider.evaluate(obj) == "Artist B"

    # Cache again; change value to C
    if isinstance(obj, _FakeItem):
        obj.values["artist"] = "Artist C"
    else:
        obj.artist = "Artist C"  # type: ignore[attr-defined]
    assert provider.evaluate(obj) == "Artist B"

    # Invalidate all and confirm new value
    provider.invalidate(None)
    assert provider.evaluate(obj) == "Artist C"


# --- Tests: CustomColumn.invalidate_cache delegation -------------------------


class _SpyProvider(ChainedValueProvider):
    def __init__(self, script: str) -> None:
        super().__init__(script)
        self.calls: list[object | None] = []

    def invalidate(self, obj: object | None = None) -> None:  # type: ignore[override]
        self.calls.append(obj)
        super().invalidate(obj)  # keep behavior intact


def test_custom_column_invalidate_cache_delegates() -> None:
    spy = _SpyProvider("%artist%")
    col = CustomColumn(
        title="T",
        key="k",
        provider=spy,
        width=None,
        align=ColumnAlign.LEFT,
        sort_type=ColumnSortType.TEXT,
        always_visible=False,
    )

    # Call without obj and with obj
    col.invalidate_cache(None)
    fake = _FakeItem(values={"artist": "A"})
    col.invalidate_cache(fake)

    assert spy.calls == [None, fake]


# --- Tests: CachedSortAdapter invalidation -----------------------------------


class _ValueItem:
    def __init__(self, value: str) -> None:
        self.value = value


class _ValueProvider(ColumnValueProvider):
    def evaluate(self, obj: _ValueItem) -> str:
        return obj.value


def test_cached_sort_adapter_invalidate_single_and_all() -> None:
    provider = _ValueProvider()
    adapter = CachedSortAdapter(provider)
    a_item = _ValueItem("B")
    b_item = _ValueItem("a")

    # Populate cache
    assert adapter.sort_key(a_item) == "b"
    assert adapter.sort_key(b_item) == "a"

    # Change values; still cached
    a_item.value = "Z"
    b_item.value = "y"
    assert adapter.sort_key(a_item) == "b"
    assert adapter.sort_key(b_item) == "a"

    # Invalidate single
    adapter.invalidate(a_item)
    assert adapter.sort_key(a_item) == "z"
    # b still cached
    assert adapter.sort_key(b_item) == "a"

    # Invalidate all
    adapter.invalidate(None)
    assert adapter.sort_key(b_item) == "y"

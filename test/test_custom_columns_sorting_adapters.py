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
import dataclasses

import pytest

from picard.ui.columns import ColumnAlign, ColumnSortType
from picard.ui.itemviews.custom_columns import (
    ArticleInsensitiveAdapter,
    CachedSortAdapter,
    CasefoldSortAdapter,
    CompositeSortAdapter,
    CustomColumn,
    DescendingCasefoldSortAdapter,
    DescendingNumericSortAdapter,
    LengthSortAdapter,
    NullsFirstAdapter,
    NullsLastAdapter,
    NumericSortAdapter,
    RandomSortAdapter,
    ReverseAdapter,
    make_callable_column,
)


@dataclasses.dataclass
class _ValueItem:
    value: str


def _build_sorted_column(adapter_factory: Callable[[object], object]) -> CustomColumn:
    base_col = make_callable_column(
        title="Value",
        key="test_value_key",
        func=lambda obj: obj.value,
        sort_type=None,
        align=ColumnAlign.LEFT,
    )
    provider = adapter_factory(base_col.provider)
    return CustomColumn(
        title=base_col.title,
        key=base_col.key,
        provider=provider,
        width=None,
        align=ColumnAlign.LEFT,
        sort_type=ColumnSortType.SORTKEY,
    )


def _sorted_values(adapter_factory: Callable[[object], object], values: list[str]) -> list[str]:
    col = _build_sorted_column(adapter_factory)
    items = [_ValueItem(v) for v in values]
    # type: ignore[operator]
    sorted_items = sorted(items, key=lambda it: col.sortkey(it))
    return [col.provider.evaluate(it) for it in sorted_items]


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["b", "A", "c"], ["A", "b", "c"]),
        (["X", "x", "Y", "y"], ["X", "x", "Y", "y"]),
    ],
)
def test_casefold_sort_adapter(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(CasefoldSortAdapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["b", "A", "c"], ["c", "b", "A"]),
        (["X", "x", "Y", "y"], ["Y", "y", "X", "x"]),
    ],
)
def test_descending_casefold_sort_adapter(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(DescendingCasefoldSortAdapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["10", "2", "3.5", "x", "-1"], ["-1", "x", "2", "3.5", "10"]),
        (["000", "01", "1", "-0.5"], ["-0.5", "000", "01", "1"]),
    ],
)
def test_numeric_sort_adapter_default_parser(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(NumericSortAdapter, values)
    assert result == expected


def _mmss_parser(s: str) -> float:
    parts = s.split(":")
    total = 0
    for p in parts:
        total = total * 60 + int(p)
    return float(total)


def test_numeric_sort_adapter_custom_parser() -> None:
    def adapter(base):
        return NumericSortAdapter(base, parser=_mmss_parser)

    values = ["3:30", "2:05", "1:00", "x"]
    # "x" falls back to 0
    expected = ["x", "1:00", "2:05", "3:30"]
    result = _sorted_values(adapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["10", "2", "3.5", "x", "-1"], ["10", "3.5", "2", "x", "-1"]),
    ],
)
def test_descending_numeric_sort_adapter(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(DescendingNumericSortAdapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (['-2', '-10', '3', '0'], ['3', '0', '-2', '-10']),
        (['1.2', '1.10', '-0.5', 'x'], ['1.2', '1.10', 'x', '-0.5']),
    ],
)
def test_descending_numeric_sort_adapter_extended(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(DescendingNumericSortAdapter, values)
    assert result == expected


def test_descending_numeric_sort_adapter_with_custom_parser() -> None:
    def adapter(base):
        return DescendingNumericSortAdapter(base, parser=_mmss_parser)

    values = ['3:30', '2:05', '1:00', 'x']
    expected = ['3:30', '2:05', '1:00', 'x']
    result = _sorted_values(adapter, values)
    assert result == expected


def test_length_sort_adapter() -> None:
    values = ["aaa", "b", "cccc", "dd"]
    expected = ["b", "dd", "aaa", "cccc"]
    result = _sorted_values(LengthSortAdapter, values)
    assert result == expected


def test_random_sort_adapter_deterministic_per_seed() -> None:
    values = ["alpha", "beta", "gamma", "delta", "epsilon"]

    def adapter_seed_1(base):
        return RandomSortAdapter(base, seed=1)

    def adapter_seed_2(base):
        return RandomSortAdapter(base, seed=2)

    col1 = _build_sorted_column(adapter_seed_1)
    col2 = _build_sorted_column(adapter_seed_1)
    col3 = _build_sorted_column(adapter_seed_2)

    items = [_ValueItem(v) for v in values]
    order1 = [col1.provider.evaluate(it) for it in sorted(items, key=lambda it: col1.sortkey(it))]
    order2 = [col2.provider.evaluate(it) for it in sorted(items, key=lambda it: col2.sortkey(it))]
    order3 = [col3.provider.evaluate(it) for it in sorted(items, key=lambda it: col3.sortkey(it))]

    # Same seed -> same order; different seeds -> likely different order
    assert order1 == order2
    assert order1 != order3


def test_article_insensitive_adapter() -> None:
    values = ["The Beatles", "Beatles", "An Artist", "Artist"]
    expected = ["An Artist", "Artist", "Beatles", "The Beatles"]
    result = _sorted_values(ArticleInsensitiveAdapter, values)
    assert result == expected


def test_composite_sort_adapter() -> None:
    # Primary by length, secondary by casefold
    def factory(base):
        return CompositeSortAdapter(base, key_funcs=[lambda it: len(it.value), lambda it: it.value.casefold()])

    values = ["bb", "a", "B", "aa", "c"]
    expected = ["a", "B", "c", "aa", "bb"]
    result = _sorted_values(factory, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["", "a", "", "b"], ["a", "b", "", ""]),
        (["", "A", "b"], ["A", "b", ""]),
        ([" ", "a", "\t", "b"], ["a", "b", " ", "\t"]),
        (["\u200b", "A", "\ufeff"], ["A", "\u200b", "\ufeff"]),
        (["\xa0", "b", "\u2060"], ["b", "\xa0", "\u2060"]),
    ],
)
def test_nulls_last_adapter(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(NullsLastAdapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["", "a", "", "b"], ["", "", "a", "b"]),
        (["", "A", "b"], ["", "A", "b"]),
        ([" ", "a", "\t", "b"], [" ", "\t", "a", "b"]),
        (["\u200b", "A", "\ufeff"], ["\u200b", "\ufeff", "A"]),
        (["\xa0", "b", "\u2060"], ["\xa0", "\u2060", "b"]),
    ],
)
def test_nulls_first_adapter(values: list[str], expected: list[str]) -> None:
    result = _sorted_values(NullsFirstAdapter, values)
    assert result == expected


def test_cached_sort_adapter() -> None:
    calls: dict[str, int] = {}

    def key_func(it: _ValueItem, provider) -> object:
        s = provider.evaluate(it)
        calls[s] = calls.get(s, 0) + 1
        return s.casefold()

    def factory(base):
        return CachedSortAdapter(base, key_func=key_func)

    values = ["B", "a", "b", "A"]
    # First run: compute and cache
    _ = _sorted_values(factory, values)
    # Second run: should hit the cache for same object instances in sort
    _ = _sorted_values(factory, values)

    # Each distinct value should have been computed at least once
    assert set(calls.keys()) == {"A", "a", "B", "b"}
    # But not necessarily recomputed on the second call for same items
    assert all(count >= 1 for count in calls.values())


def test_reverse_adapter() -> None:
    values = ["a", "B", "c"]
    asc = _sorted_values(CasefoldSortAdapter, values)

    def factory(base):
        # Reverse the underlying casefold sort; ties resolved by original case
        return ReverseAdapter(CasefoldSortAdapter(base))

    desc = _sorted_values(factory, values)
    assert asc == ["a", "B", "c"]
    # Reverse order of case-insensitive ascending becomes descending
    # Case-insensitive compare: 'a' == 'A', but we reverse based on key,
    # so 'B' (from 'B') will come before 'a'
    assert desc == ["c", "B", "a"]

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

from picard.const.sys import IS_WIN
from picard.i18n import setup_gettext

import pytest

from picard.ui.columns import (
    ColumnAlign,
    ColumnSortType,
)
from picard.ui.itemviews.custom_columns import (
    ArticleInsensitiveAdapter,
    CachedSortAdapter,
    CasefoldSortAdapter,
    CompositeSortAdapter,
    CustomColumn,
    LengthSortAdapter,
    NaturalSortAdapter,
    NullsFirstAdapter,
    NullsLastAdapter,
    NumericSortAdapter,
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
    setup_gettext(None, 'en')
    result = _sorted_values(CasefoldSortAdapter, values)
    assert result == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["10", "2", "3.5", "x", "-1"], ["-1", "2", "3.5", "10", "x"]),
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
    # "x" is non-numeric and sorts after numeric values
    expected = ["1:00", "2:05", "3:30", "x"]
    result = _sorted_values(adapter, values)
    assert result == expected


def test_length_sort_adapter() -> None:
    values = ["aaa", "b", "cccc", "dd"]
    expected = ["b", "dd", "aaa", "cccc"]
    result = _sorted_values(LengthSortAdapter, values)
    assert result == expected


@pytest.mark.skipif(IS_WIN, reason="QCollator not used on Windows")
def test_article_insensitive_adapter() -> None:
    setup_gettext(None, 'en')
    values = ["The Beatles", "Beatles", "An Artist", "Artist"]
    expected = ["An Artist", "Artist", "The Beatles", "Beatles"]
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


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        # Basic natural sorting - numbers within text
        (["item10", "item2", "item1"], ["item1", "item2", "item10"]),
        (["track1", "track10", "track2"], ["track1", "track2", "track10"]),
        # Mixed text and pure numbers
        (["10", "2", "item3", "09 item", "item10"], ["2", "09 item", "10", "item3", "item10"]),
        # Same text, different numbers
        (["version 1.10", "version 1.2", "version 1.1"], ["version 1.1", "version 1.2", "version 1.10"]),
        # Pure text (fallback to regular sorting)
        (["zebra", "apple", "banana"], ["apple", "banana", "zebra"]),
    ],
)
def test_natural_sort_adapter(values: list[str], expected: list[str]) -> None:
    setup_gettext(None, 'en')
    result = _sorted_values(NaturalSortAdapter, values)
    assert result == expected


def test_natural_sort_adapter_basic_functionality() -> None:
    """Test that natural sorting works for basic cases."""
    setup_gettext(None, 'en')
    values = ["item1", "item10", "item2"]
    result = _sorted_values(NaturalSortAdapter, values)
    expected = ["item1", "item2", "item10"]
    assert result == expected


def test_natural_sort_adapter_vs_regular_sorting() -> None:
    """Test that natural sorting differs from regular text sorting for numeric content."""
    setup_gettext(None, 'en')
    values = ["file1.txt", "file10.txt", "file2.txt", "file20.txt"]

    # Regular casefold sorting (lexicographic)
    regular_result = _sorted_values(CasefoldSortAdapter, values)
    assert regular_result == ["file1.txt", "file10.txt", "file2.txt", "file20.txt"]

    # Natural sorting (numeric-aware)
    natural_result = _sorted_values(NaturalSortAdapter, values)
    assert natural_result == ["file1.txt", "file2.txt", "file10.txt", "file20.txt"]

    # They should be different for this case
    assert regular_result != natural_result


def test_natural_sort_adapter_empty_handling() -> None:
    """Test natural sort adapter handles empty strings."""
    values = ["", "item1", "item"]
    result = _sorted_values(NaturalSortAdapter, values)
    # Empty string should be handled consistently
    assert "" in result
    assert len(result) == 3


def test_natural_sort_adapter_unicode_handling() -> None:
    """Test natural sorting with unicode characters."""
    values = ["ñ1", "n10", "ñ2", "n1"]
    # Natural sort should handle unicode properly
    result = _sorted_values(NaturalSortAdapter, values)
    # Order may depend on locale, but should be consistent
    assert len(result) == 4
    assert set(result) == set(values)

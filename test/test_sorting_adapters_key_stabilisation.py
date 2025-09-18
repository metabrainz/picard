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

"""Tests for custom column sorting adapters' key normalization and stability.

This module verifies that sorting adapters always return comparable sort keys
to avoid cross-type comparisons that previously caused crashes during UI
sorting (e.g. comparing ``QCollatorSortKey`` vs ``float`` inside
``TreeItem.__lt__`` leading to ``TypeError: '<' not supported between
instances of 'QCollatorSortKey' and 'float'``).

Specifically, we test:
    - NumericSortAdapter and DescendingNumericSortAdapter produce tuple keys
      with a category flag and a homogeneous secondary component, so mixed
      numeric/non-numeric values sort without raising ``TypeError`` and with
      numeric-first ordering.
    - CompositeSortAdapter normalizes each component and returns a composite
      tuple made of normalized sub-keys, preventing mixed-type comparisons
      across items.
    - CachedSortAdapter normalizes keys when a custom ``key_func`` returns
      mixed types, ensuring stable ordering and no cross-type errors.
    - ReverseAdapter normalizes and inverts keys deterministically; it also
      preserves tuple keys (e.g. when wrapping NumericSortAdapter) to avoid
      introducing new mixed-type comparisons or semantic changes.

These tests are focused on the normalization behavior introduced to fix the
crash and complement (not duplicate) the broader behavioral tests in
``test_custom_columns_sorting_adapters.py``.
"""

from picard.item import Item

import pytest

from picard.ui.itemviews.custom_columns.protocols import ColumnValueProvider
from picard.ui.itemviews.custom_columns.sorting_adapters import (
    CachedSortAdapter,
    CompositeSortAdapter,
    NumericSortAdapter,
    ReverseAdapter,
)


class StubProvider:
    def __init__(self, value: str):
        self._value = value

    def evaluate(self, _obj) -> str:
        return self._value


@pytest.mark.parametrize(
    "value, expect_flag",
    [
        ("10", 0),
        ("-2.5", 0),
        ("", 1),
        ("abc", 1),
        ("7a", 1),
        ("  12  ", 0),
    ],
)
def test_numeric_sort_adapter_key_shape_and_category(value: str, expect_flag: int) -> None:
    base = StubProvider(value)
    adapter = NumericSortAdapter(base)

    class Dummy(Item):
        pass

    key = adapter.sort_key(Dummy())
    assert isinstance(key, tuple)
    assert key[0] in (0, 1)
    assert key[0] == expect_flag


def test_numeric_sort_adapter_mixed_values_no_typeerror_and_ordering() -> None:
    values = ["10", "abc", "2", "", "7a", "-3.5"]

    class Dummy(Item):
        pass

    adapters = [NumericSortAdapter(StubProvider(v)) for v in values]
    keys = [a.sort_key(Dummy()) for a in adapters]
    # Should not raise TypeError
    sorted_pairs = sorted(zip(values, keys, strict=True), key=lambda p: p[1])
    sorted_values = [v for v, _ in sorted_pairs]
    # Numbers first, ascending; then non-numeric by natural order
    assert sorted_values[:3] == ["-3.5", "2", "10"]


class WeirdKeyProvider(ColumnValueProvider):
    def __init__(self, value: str):
        self._value = value

    def evaluate(self, _obj) -> str:
        return self._value

    # Simulate an inconsistent sort_key source for ReverseAdapter tests by
    # attaching a dynamic method later when needed


def test_composite_sort_adapter_mixed_component_types_no_typeerror() -> None:
    class Dummy(Item):
        def __init__(self, s: str):
            super().__init__()
            self.value = s

    def key_primary(obj: Dummy) -> object:
        # Return number if numeric, else original string (mixed types)
        s = obj.value
        try:
            return float(s)
        except Exception:
            return s

    def key_secondary(obj: Dummy) -> object:
        return obj.value.casefold()

    adapter = CompositeSortAdapter(base=StubProvider(""), key_funcs=[key_primary, key_secondary])

    values = ["10", "abc", "2", "A"]
    items = [Dummy(v) for v in values]
    keys = [adapter.sort_key(it) for it in items]
    # Should not raise TypeError when sorting
    sorted_pairs = sorted(zip(values, keys, strict=True), key=lambda p: p[1])
    sorted_values = [v for v, _ in sorted_pairs]
    # Numbers first (ascending), then strings (case-insensitive order)
    assert sorted_values == ["2", "10", "A", "abc"]


def test_cached_sort_adapter_key_func_mixed_types_normalized() -> None:
    def key_func(_obj, provider: ColumnValueProvider) -> object:
        s = provider.evaluate(_obj)
        return int(s) if s.isdigit() else s

    adapters = [CachedSortAdapter(StubProvider(v), key_func=key_func) for v in ["10", "abc", "2"]]

    class Dummy(Item):
        pass

    keys = [a.sort_key(Dummy()) for a in adapters]
    sorted_pairs = sorted(zip(["10", "abc", "2"], keys, strict=True), key=lambda p: p[1])
    sorted_values = [v for v, _ in sorted_pairs]
    # Numbers first (ascending), then strings
    assert sorted_values == ["2", "10", "abc"]


def test_reverse_adapter_normalizes_mixed_types_from_custom_sort_key() -> None:
    # Provide a SortKeyProvider-like object with mixed numeric / string outputs
    class MixedSortKeyProvider(WeirdKeyProvider):
        def sort_key(self, _obj):  # type: ignore[override]
            s = self._value
            try:
                return float(s)
            except Exception:
                return s

    providers = [MixedSortKeyProvider(v) for v in ["10", "abc", "2"]]
    adaptered = [ReverseAdapter(p) for p in providers]

    class Dummy(Item):
        pass

    keys = [a.sort_key(Dummy()) for a in adaptered]
    # Should not raise TypeError when sorting
    sorted_pairs = sorted(zip(["10", "abc", "2"], keys, strict=True), key=lambda p: p[1])
    sorted_values = [v for v, _ in sorted_pairs]
    # Numbers first in descending due to reverse: 10, 2, then strings
    assert sorted_values == ["10", "2", "abc"]


def test_reverse_adapter_over_numeric_adapter_leaves_order_intact() -> None:
    values = ["10", "abc", "2"]

    class Dummy(Item):
        pass

    base_adapters = [NumericSortAdapter(StubProvider(v)) for v in values]
    base_keys = [a.sort_key(Dummy()) for a in base_adapters]
    base_sorted = [v for v, _ in sorted(zip(values, base_keys, strict=True), key=lambda p: p[1])]

    rev_adapters = [ReverseAdapter(a) for a in base_adapters]
    rev_keys = [a.sort_key(Dummy()) for a in rev_adapters]
    rev_sorted = [v for v, _ in sorted(zip(values, rev_keys, strict=True), key=lambda p: p[1])]

    # ReverseAdapter keeps tuple keys from NumericSortAdapter as-is; ordering remains identical
    assert rev_sorted == base_sorted

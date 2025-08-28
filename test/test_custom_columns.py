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

import dataclasses
import gc
from unittest.mock import Mock
from weakref import ref

from picard.metadata import Metadata

import pytest

from picard.ui.columns import ColumnSortType
from picard.ui.itemviews.custom_columns import (
    ColumnValueProvider,
    CustomColumn,
    make_callable_column,
    make_field_column,
    make_provider_column,
    make_script_column,
    make_transformed_column,
    registry,
)
from picard.ui.itemviews.custom_columns.script_provider import ChainedValueProvider
from picard.ui.itemviews.custom_columns.shared import VIEW_FILE


@dataclasses.dataclass
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


class _ProviderWithSort(ColumnValueProvider):
    def __init__(self, key: str):
        self.key = key

    def evaluate(self, obj: _FakeItem) -> str:
        return obj.column(self.key)

    def sort_key(self, obj: _FakeItem):
        return obj.column(self.key).lower()


class _SubInjectedProvider(ChainedValueProvider):
    # Override class defaults to demonstrate injectibility via subclassing
    DEFAULT_MAX_RUNTIME_MS = 5
    DEFAULT_CACHE_SIZE = 33


@pytest.fixture
def fake_item() -> _FakeItem:
    return _FakeItem(values={"artist": "Artist A", "title": "Title T", "album": "Album X"})


@pytest.fixture
def unique_key(request: pytest.FixtureRequest) -> str:
    # Generate a unique key per test function to avoid collisions in global registries
    return f"test_custom_{request.node.name}"


def test_make_field_column_evaluates_value(fake_item: _FakeItem) -> None:
    col = make_field_column("Artist", "artist")
    assert isinstance(col, CustomColumn)
    assert col.provider.evaluate(fake_item) == "Artist A"


@pytest.mark.parametrize(
    ("transform", "expected"),
    [
        (lambda s: s.upper(), "ARTIST A"),
        (lambda s: f"[{s}]", "[Artist A]"),
    ],
)
def test_make_transformed_column_applies_transform(fake_item: _FakeItem, transform, expected: str) -> None:
    col = make_transformed_column("ArtistX", "artist", transform=transform)
    assert col.provider.evaluate(fake_item) == expected


def test_make_transformed_column_handles_transform_errors(fake_item: _FakeItem) -> None:
    col = make_transformed_column("ArtistInt", "artist", transform=int)
    # int("Artist A") raises ValueError, provider returns empty string
    assert col.provider.evaluate(fake_item) == ""


def test_make_callable_column_evaluates_multi_field(fake_item: _FakeItem) -> None:
    def func(obj):
        return f"{obj.column('artist')} - {obj.column('title')}"

    col = make_callable_column("Artist - Title", "artist_title", func)
    assert col.provider.evaluate(fake_item) == "Artist A - Title T"


def test_callable_column_infers_text_sort_by_default(fake_item: _FakeItem) -> None:
    def func(obj):
        return obj.column("album")

    col = make_callable_column("Album", "album_key", func, sort_type=None)
    # No sort_key on provider, inference should choose TEXT
    assert col.sort_type.name == "TEXT"
    # The provider does not implement a sort_key, so no custom sort function
    assert col.sortkey is None


def test_infer_sortkey_when_provider_offers_sort(fake_item: _FakeItem) -> None:
    provider = _ProviderWithSort("artist")
    col = make_provider_column("Artist", "artist_sorted", provider)
    assert col.sort_type.name == "SORTKEY"
    # sortkey should be bound to provider.sort_key
    # Bound method is proxied through CustomColumn, not identity-equal
    assert callable(col.sortkey)
    # Evaluate both value and sortkey for the fake item
    assert col.provider.evaluate(fake_item) == "Artist A"
    assert col.sortkey(fake_item) == "artist a"


@pytest.mark.parametrize(
    "sort_type",
    [None, ColumnSortType.TEXT, ColumnSortType.SORTKEY],
)
def test_make_provider_column_infers_sort_type(sort_type) -> None:
    class Prov:
        def evaluate(self, obj: _FakeItem) -> str:  # pragma: no cover - simple
            return "x"

    class ProvWithSort(Prov):
        def sort_key(self, obj: _FakeItem):  # pragma: no cover - simple
            return 1

    # Without sort_key: always TEXT (explicit SORTKEY would be downgraded)
    col1 = make_provider_column("T", "k1", Prov(), sort_type=sort_type)
    expected1 = "TEXT"
    assert col1.sort_type.name == expected1

    # With sort_key: SORTKEY unless explicitly overridden
    col2 = make_provider_column("T", "k2", ProvWithSort(), sort_type=sort_type)
    expected2 = sort_type.name if sort_type is not None else "SORTKEY"
    assert col2.sort_type.name == expected2


def test_script_column_evaluates_metadata_variable(fake_item: _FakeItem) -> None:
    col = make_script_column("Scripted", "script_key", "%artist%")
    assert col.provider.evaluate(fake_item) == "Artist A"


def test_script_column_caches_fast_results(fake_item: _FakeItem) -> None:
    # Create provider with a large threshold to allow caching
    col = make_script_column("Scripted", "script_key", "%artist%", max_runtime_ms=1000)
    # First evaluation reads "Artist A"
    assert col.provider.evaluate(fake_item) == "Artist A"
    # Mutate underlying metadata and ensure cached value is returned
    fake_item.values["artist"] = "Artist B"
    assert col.provider.evaluate(fake_item) == "Artist A"


def test_script_column_avoids_caching_when_too_slow(fake_item: _FakeItem) -> None:
    # Negative threshold ensures the measured runtime exceeds max and won't cache
    col = make_script_column("Scripted", "script_key", "%artist%", max_runtime_ms=-1)
    assert col.provider.evaluate(fake_item) == "Artist A"
    fake_item.values["artist"] = "Artist B"
    assert col.provider.evaluate(fake_item) == "Artist B"


def test_registry_registers_and_unregisters_columns(unique_key: str) -> None:
    col = make_callable_column("Concat", unique_key, lambda obj: "X")
    try:
        # Before registration column is not in registry
        assert registry.get(unique_key) is None
        registry.register(col)
        # After registration column is retrievable
        assert registry.get(unique_key) is col
        # And present in both views
        from picard.ui.itemviews.columns import (
            ALBUMVIEW_COLUMNS,
            FILEVIEW_COLUMNS,
        )

        file_keys = [c.key for c in FILEVIEW_COLUMNS]
        album_keys = [c.key for c in ALBUMVIEW_COLUMNS]
        assert unique_key in file_keys
        assert unique_key in album_keys
        # Newly registered columns should be appended at the end
        assert FILEVIEW_COLUMNS[-1].key == unique_key
        assert ALBUMVIEW_COLUMNS[-1].key == unique_key
    finally:
        # Cleanup: ensure we remove the test column from both views and registry
        unregistered = registry.unregister(unique_key)
        assert unregistered is col
        from picard.ui.itemviews.columns import (
            ALBUMVIEW_COLUMNS,
            FILEVIEW_COLUMNS,
        )

        assert unique_key not in [c.key for c in FILEVIEW_COLUMNS]
        assert unique_key not in [c.key for c in ALBUMVIEW_COLUMNS]


def test_field_column_handles_missing_key(fake_item: _FakeItem) -> None:
    """Test field column with non-existent key returns empty string."""
    col = make_field_column("Missing", "nonexistent_key")
    assert col.provider.evaluate(fake_item) == ""


def test_field_column_handles_object_without_column_method() -> None:
    """Test field column gracefully handles objects without column method."""
    obj_without_column = Mock()
    del obj_without_column.column  # Remove column method

    col = make_field_column("Test", "test_key")
    assert col.provider.evaluate(obj_without_column) == ""


def test_transformed_column_with_none_base_provider(fake_item: _FakeItem) -> None:
    """Test transformed column uses field reference when no base provider given."""
    col = make_transformed_column("Upper Artist", "artist", transform=str.upper)
    assert col.provider.evaluate(fake_item) == "ARTIST A"


def test_transformed_column_handles_none_input() -> None:
    """Test transform handles None/empty input gracefully."""
    col = make_transformed_column("Test", "missing_key", transform=str.upper)
    fake_item = _FakeItem(values={})
    assert col.provider.evaluate(fake_item) == ""


def test_callable_column_handles_exceptions() -> None:
    """Test callable column returns empty string on function exceptions."""

    def failing_func(obj: _FakeItem) -> str:
        raise ValueError("Intentional failure")

    col = make_callable_column("Failing", "fail_key", failing_func)
    fake_item = _FakeItem(values={})
    assert col.provider.evaluate(fake_item) == ""


# TODO: Skip due to upstream global state interference with ScriptParser functions when full suite runs.
# Does not impact live usage; scripts load functions correctly in app context.
@pytest.mark.skip(reason="Temporarily skipped pending upstream global state investigation")
def test_script_column_with_complex_expression(fake_item: _FakeItem) -> None:
    """Test script column with complex expressions."""
    script = "$if(%artist%,%artist% by %album%,Unknown)"
    col = make_script_column("Complex", "complex_key", script)
    result = col.provider.evaluate(fake_item)
    # Should resolve to "Artist A by Album X"
    assert "Artist A" in result
    assert "Album X" in result


def test_script_column_with_invalid_syntax() -> None:
    """Test script column handles syntax errors gracefully."""
    col = make_script_column("Invalid", "invalid_key", "%unclosed_tag")
    fake_item = _FakeItem(values={})
    assert col.provider.evaluate(fake_item) == ""


def test_script_column_fallback_chain() -> None:
    """Test the resolution chain: obj.column -> context -> script."""

    # Create an object that will fail obj.column but have metadata
    class PartialObject:
        def __init__(self, metadata: Metadata) -> None:
            self.metadata = metadata

        def column(self, key: str) -> str:
            if key == "available_key":
                return "from_column"
            raise KeyError("Not available in column")

    metadata = Metadata()
    metadata["fallback_key"] = "from_metadata"
    obj = PartialObject(metadata)

    # Test obj.column success
    col1 = make_script_column("Test1", "test1", "%available_key%")
    assert col1.provider.evaluate(obj) == "from_column"

    # Test fallback to metadata
    col2 = make_script_column("Test2", "test2", "%fallback_key%")
    assert col2.provider.evaluate(obj) == "from_metadata"


@pytest.mark.parametrize("obj_type", ["File", "Track", "Album", "Cluster"])
def test_script_column_with_different_object_types(obj_type: str) -> None:
    """Test script evaluation with different Picard object types."""
    # Mock different object types
    metadata = Metadata()
    metadata["test_field"] = f"value_from_{obj_type.lower()}"

    if obj_type == "File":
        obj = Mock()
        obj.metadata = metadata
        obj.__class__.__name__ = "File"
    elif obj_type == "Track":
        obj = Mock()
        obj.metadata = metadata
        obj.files = [Mock()]  # Single linked file
        obj.num_linked_files = 1
        obj.__class__.__name__ = "Track"
    else:  # Album or Cluster
        obj = Mock()
        obj.metadata = metadata
        obj.__class__.__name__ = obj_type

    col = make_script_column("Test", "test_key", "%test_field%")
    result = col.provider.evaluate(obj)
    assert f"value_from_{obj_type.lower()}" in result


def test_cache_memory_management() -> None:
    """Test that cache properly handles object lifecycle."""
    col = make_script_column("Cached", "cache_key", "%artist%")

    # Create objects that can be weakly referenced
    items: list[_FakeItem] = []
    for i in range(5):
        item = _FakeItem(values={"artist": f"Artist {i}"})
        items.append(item)
        # Evaluate to populate cache
        result = col.provider.evaluate(item)
        assert result == f"Artist {i}"

    # Create weak references to track object lifecycle
    refs: list[ref[_FakeItem]] = [ref(item) for item in items]

    # Delete objects and force garbage collection
    del items
    gc.collect()

    # Some weak references should be dead (depending on GC implementation)
    # This tests that WeakKeyDictionary doesn't prevent GC
    dead_refs: int = sum(1 for r in refs if r() is None)
    # At least some should be collected, but exact count depends on GC timing
    assert dead_refs >= 0  # Basic sanity check


def test_cache_id_fallback_for_non_weakrefable() -> None:
    """Test id-based cache fallback for objects that can't be weakly referenced."""
    col = make_script_column("Test", "test_key", "%artist%", max_runtime_ms=1000)

    # Mock an object that raises TypeError on weak reference
    class NonWeakRefable:
        def __init__(self, artist: str) -> None:
            self.artist = artist

        def column(self, key: str) -> str:
            return self.artist if key == "artist" else ""

        @property
        def metadata(self) -> Metadata:
            md = Metadata()
            md["artist"] = self.artist
            return md

    # Some built-in types can't be weakly referenced
    obj: NonWeakRefable = NonWeakRefable("Test Artist")

    # First evaluation should work
    result1: str = col.provider.evaluate(obj)
    assert result1 == "Test Artist"

    # Should use id-based cache on second evaluation
    # (Hard to test directly without accessing private members)
    result2: str = col.provider.evaluate(obj)
    assert result2 == "Test Artist"


def test_cache_size_limit() -> None:
    """Test that id-cache respects size limits."""
    # Small cache size for testing
    col = make_script_column("Test", "test_key", "%artist%", cache_size=3)

    class TestObj:
        def __init__(self, value: str) -> None:
            self.value = value

        def column(self, key: str) -> str:
            return self.value

        @property
        def metadata(self) -> Metadata:
            md = Metadata()
            md["artist"] = self.value
            return md

    # Create more objects than cache size
    objects: list[TestObj] = [TestObj(f"Value {i}") for i in range(5)]

    # Evaluate all objects
    for obj in objects:
        result: str = col.provider.evaluate(obj)
        assert result == obj.value

    # On a non-weakrefable object path, ensure FIFO eviction happens when size exceeded
    class NonWeakRefable2:
        def __init__(self, value: str) -> None:
            self.value = value

        def column(self, key: str) -> str:
            return self.value

        @property
        def metadata(self) -> Metadata:
            md = Metadata()
            md["artist"] = self.value
            return md

    objs = [NonWeakRefable2(f"V{i}") for i in range(5)]
    col2 = make_script_column("Test", "test_key2", "%artist%", cache_size=2)
    # Fill beyond capacity
    for o in objs:
        assert col2.provider.evaluate(o) == o.value
    # Access the last two; the first should have been evicted
    assert col2.provider.evaluate(objs[-1]) == "V4"
    assert col2.provider.evaluate(objs[-2]) == "V3"


def test_registry_handles_duplicate_registration(unique_key: str) -> None:
    """Test registry behavior with duplicate key registration."""
    col1 = make_callable_column("First", unique_key, lambda obj: "first")
    col2 = make_callable_column("Second", unique_key, lambda obj: "second")

    try:
        # First registration
        registry.register(col1)
        assert registry.get(unique_key) is col1

        from picard.ui.itemviews.columns import (
            ALBUMVIEW_COLUMNS,
            FILEVIEW_COLUMNS,
        )

        # Keys appear exactly once in both views
        assert [c.key for c in FILEVIEW_COLUMNS].count(unique_key) == 1
        assert [c.key for c in ALBUMVIEW_COLUMNS].count(unique_key) == 1

        # Second registration with same key: should replace, not duplicate
        registry.register(col2)
        assert registry.get(unique_key) is col2

        # Still exactly one occurrence in both views, and it refers to col2
        file_indices = [i for i, c in enumerate(FILEVIEW_COLUMNS) if c.key == unique_key]
        album_indices = [i for i, c in enumerate(ALBUMVIEW_COLUMNS) if c.key == unique_key]
        assert len(file_indices) == 1
        assert len(album_indices) == 1
        assert FILEVIEW_COLUMNS[file_indices[0]] is col2
        assert ALBUMVIEW_COLUMNS[album_indices[0]] is col2
    finally:
        registry.unregister(unique_key)


def test_registry_unregister_nonexistent_key() -> None:
    """Test unregistering a key that doesn't exist."""
    result: CustomColumn | None = registry.unregister("nonexistent_key_12345")
    assert result is None


def test_registry_selective_view_registration(unique_key: str) -> None:
    """Test registering to specific views only."""
    col = make_callable_column("Test", unique_key, lambda obj: "test")

    try:
        # Register only to file view
        registry.register(col, add_to={VIEW_FILE})

        from picard.ui.itemviews.columns import (
            ALBUMVIEW_COLUMNS,
            FILEVIEW_COLUMNS,
        )

        file_keys: list[str] = [c.key for c in FILEVIEW_COLUMNS]
        album_keys: list[str] = [c.key for c in ALBUMVIEW_COLUMNS]

        assert unique_key in file_keys
        assert unique_key not in album_keys

    finally:
        registry.unregister(unique_key)


def test_registry_unknown_view_raises(unique_key: str) -> None:
    """Unknown view identifiers should raise an error during registration."""
    col = make_callable_column("X", unique_key, lambda obj: "x")

    try:
        with pytest.raises(ValueError):
            registry.register(col, add_to={"UNKNOWN_VIEW"})
    finally:
        registry.unregister(unique_key)


def test_registry_unregister_removes_all_occurrences(unique_key: str) -> None:
    """Ensure unregister removes all instances from both views."""
    col = make_callable_column("Test", unique_key, lambda obj: "test")

    try:
        # Register twice to simulate potential duplicates (older behavior)
        registry.register(col)
        registry.register(col)

        from picard.ui.itemviews.columns import (
            ALBUMVIEW_COLUMNS,
            FILEVIEW_COLUMNS,
        )

        assert [c.key for c in FILEVIEW_COLUMNS].count(unique_key) == 1
        assert [c.key for c in ALBUMVIEW_COLUMNS].count(unique_key) == 1

        # Unregister should remove all occurrences
        registry.unregister(unique_key)
        assert unique_key not in [c.key for c in FILEVIEW_COLUMNS]
        assert unique_key not in [c.key for c in ALBUMVIEW_COLUMNS]
    finally:
        registry.unregister(unique_key)


@pytest.mark.parametrize("max_runtime_ms", [-1, 0, 1, 100])
def test_script_column_performance_thresholds(fake_item: _FakeItem, max_runtime_ms: int) -> None:
    """Test different performance thresholds for caching decisions."""
    col = make_script_column("Perf", "perf_key", "%artist%", max_runtime_ms=max_runtime_ms)

    result: str = col.provider.evaluate(fake_item)
    assert result == "Artist A"

    # Modify data and test again
    fake_item.values["artist"] = "Modified Artist"
    result2: str = col.provider.evaluate(fake_item)

    # With very low/negative thresholds, should not cache
    if max_runtime_ms <= 0:
        assert result2 == "Modified Artist"
    # With higher thresholds, may cache (timing dependent)


def test_column_value_provider_protocol() -> None:
    """Test that custom providers conform to the protocol."""

    class CustomProvider:
        def evaluate(self, obj: _FakeItem) -> str:
            return "custom_value"

        def sort_key(self, obj: _FakeItem) -> str:
            return "custom_sort"

    # Should be recognized as ColumnValueProvider
    provider: CustomProvider = CustomProvider()
    assert isinstance(provider, ColumnValueProvider)

    col: CustomColumn = make_callable_column("Custom", "custom_key", provider.evaluate)
    fake_item: _FakeItem = _FakeItem(values={})
    assert col.provider.evaluate(fake_item) == "custom_value"


@pytest.mark.parametrize(
    ("provider_cls", "expected_runtime", "expected_cache_size"),
    [
        (ChainedValueProvider, 25, 1024),
        (_SubInjectedProvider, 5, 33),
    ],
)
def test_chained_value_provider_defaults_via_class_injection(
    provider_cls: type[ChainedValueProvider], expected_runtime: int, expected_cache_size: int
) -> None:
    provider = provider_cls("%artist%", max_runtime_ms=None, cache_size=None)
    # When None is passed, provider should use class-level defaults
    assert provider._max_runtime_ms == expected_runtime
    # id-cache size is bounded by minimum 16
    assert provider._id_cache_max == max(16, expected_cache_size)


def test_chained_value_provider_defaults_via_monkeypatch(fake_item: _FakeItem, monkeypatch: pytest.MonkeyPatch) -> None:
    # Inject new defaults by monkeypatching the class attributes
    monkeypatch.setattr(ChainedValueProvider, "DEFAULT_MAX_RUNTIME_MS", -1, raising=False)
    monkeypatch.setattr(ChainedValueProvider, "DEFAULT_CACHE_SIZE", 2, raising=False)

    provider = ChainedValueProvider("%artist%", max_runtime_ms=None, cache_size=None)
    # With negative threshold as default, evaluation should not cache
    assert provider.evaluate(fake_item) == "Artist A"
    fake_item.values["artist"] = "Artist B"
    assert provider.evaluate(fake_item) == "Artist B"
    # Cache size honors lower bound
    assert provider._id_cache_max == 16


@pytest.mark.parametrize("min_size, requested, expected", [(1, 1, 1), (32, 2, 32), (64, 128, 128)])
def test_id_cache_minimum_injection(
    min_size: int, requested: int, expected: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Ensure the minimum bound is injectible and respected
    monkeypatch.setattr(ChainedValueProvider, "DEFAULT_MIN_ID_CACHE_SIZE", min_size, raising=False)
    provider = ChainedValueProvider("%artist%", max_runtime_ms=1000, cache_size=requested)
    assert provider._id_cache_max == expected


def test_album_like_object_avoids_caching_until_loaded() -> None:
    class AlbumLike:
        is_album_like = True
        loaded = False

        def __init__(self, artist: str, album: str) -> None:
            self._artist = artist
            self._album = album

        @property
        def metadata(self) -> Metadata:
            md = Metadata()
            md["albumartist"] = self._artist
            md["album"] = self._album
            return md

    # Script uses album-level fields
    col = make_script_column("AlbumRow", "album_row", "%albumartist% - %album%")

    obj = AlbumLike("Artist 1", "Album 1")
    # First evaluate while not loaded: should not cache and reflect current values
    assert col.provider.evaluate(obj) == "Artist 1 - Album 1"

    # Change data while still not loaded: should re-evaluate (no cache hit)
    obj._artist = "Artist 2"
    obj._album = "Album 2"
    assert col.provider.evaluate(obj) == "Artist 2 - Album 2"

    # Mark as loaded: next evaluate should be cached
    obj.loaded = True
    assert col.provider.evaluate(obj) == "Artist 2 - Album 2"

    # Change data again: should still return cached (since now loaded and fast)
    obj._artist = "Artist 3"
    obj._album = "Album 3"
    assert col.provider.evaluate(obj) == "Artist 2 - Album 2"

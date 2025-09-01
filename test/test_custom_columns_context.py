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

"""Test context extraction strategies for custom columns."""

from __future__ import annotations

from typing import Any

import pytest

from picard.ui.itemviews.custom_columns import context as context_mod


class DummyFile:
    def __init__(self, metadata: Any = None):
        self.metadata = metadata


class DummyTrack:
    def __init__(
        self,
        metadata: Any = None,
        files: Any = None,
        num_linked_files: int = 0,
    ):
        self.metadata = metadata
        self.files = files
        self.num_linked_files = num_linked_files


class DummyMetadataItem:
    pass


@pytest.fixture(autouse=True)
def patch_context_classes(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure strategies use dummy classes via isinstance checks
    monkeypatch.setattr(context_mod, "File", DummyFile, raising=True)
    monkeypatch.setattr(context_mod, "Track", DummyTrack, raising=True)
    monkeypatch.setattr(context_mod, "MetadataItem", DummyMetadataItem, raising=True)


@pytest.fixture()
def file_strategy() -> context_mod.FileContextStrategy:
    return context_mod.FileContextStrategy()


@pytest.fixture()
def track_strategy() -> context_mod.TrackContextStrategy:
    return context_mod.TrackContextStrategy()


@pytest.fixture()
def default_strategy() -> context_mod.DefaultContextStrategy:
    return context_mod.DefaultContextStrategy()


@pytest.fixture()
def manager() -> context_mod.ContextStrategyManager:
    return context_mod.ContextStrategyManager()


def test_file_strategy_can_handle(file_strategy: context_mod.FileContextStrategy) -> None:
    assert file_strategy.can_handle(DummyFile()) is True
    assert file_strategy.can_handle(object()) is False


def test_file_strategy_make_context(file_strategy: context_mod.FileContextStrategy) -> None:
    dummy_file = DummyFile(metadata={"k": "v"})
    metadata, file_obj = file_strategy.make_context(dummy_file)
    assert metadata == {"k": "v"}
    assert file_obj is dummy_file


def test_track_strategy_can_handle(track_strategy: context_mod.TrackContextStrategy) -> None:
    assert track_strategy.can_handle(DummyTrack()) is True
    assert track_strategy.can_handle(object()) is False


@pytest.mark.parametrize(
    ("files", "num_linked", "expected_file"),
    [
        (["F1"], 1, "F1"),
        (("F1", "F2"), 1, "F1"),
        ([], 0, None),
        (["F1", "F2"], 2, None),
        (None, 0, None),
        ("not-a-sequence", 1, None),
    ],
)
def test_track_strategy_make_context(
    track_strategy: context_mod.TrackContextStrategy,
    files: Any,
    num_linked: int,
    expected_file: Any,
) -> None:
    dummy_track = DummyTrack(metadata={"m": 1}, files=files, num_linked_files=num_linked)
    metadata, file_obj = track_strategy.make_context(dummy_track)
    assert metadata == {"m": 1}
    assert file_obj == expected_file


def test_default_strategy_can_handle_by_metadata_attr(
    default_strategy: context_mod.DefaultContextStrategy,
) -> None:
    class WithMetadata:
        def __init__(self) -> None:
            self.metadata = {"a": 1}

    assert default_strategy.can_handle(WithMetadata()) is True


def test_default_strategy_can_handle_by_metadata_item_instance(
    default_strategy: context_mod.DefaultContextStrategy,
) -> None:
    assert default_strategy.can_handle(DummyMetadataItem()) is True


def test_default_strategy_cannot_handle_without_metadata_or_type(
    default_strategy: context_mod.DefaultContextStrategy,
) -> None:
    assert default_strategy.can_handle(object()) is False


def test_default_strategy_make_context_returns_metadata_and_none(
    default_strategy: context_mod.DefaultContextStrategy,
) -> None:
    class WithMetadata:
        def __init__(self) -> None:
            self.metadata = {"x": 2}

    metadata, file_obj = default_strategy.make_context(WithMetadata())
    assert metadata == {"x": 2}
    assert file_obj is None


def test_manager_uses_file_strategy_first(manager: context_mod.ContextStrategyManager) -> None:
    dummy_file = DummyFile(metadata={"f": 1})
    metadata, file_obj = manager.make_context(dummy_file)
    assert metadata == {"f": 1}
    assert file_obj is dummy_file


def test_manager_uses_track_strategy_then_default(manager: context_mod.ContextStrategyManager) -> None:
    # One linked file picked by track strategy
    dummy_track = DummyTrack(metadata={"t": 1}, files=["F1"], num_linked_files=1)
    metadata, file_obj = manager.make_context(dummy_track)
    assert metadata == {"t": 1}
    assert file_obj == "F1"

    # Multiple linked files -> no single file, falls back to default behavior (still track strategy; returns None)
    dummy_track_multi = DummyTrack(metadata={"t": 2}, files=["F1", "F2"], num_linked_files=2)
    metadata2, file_obj2 = manager.make_context(dummy_track_multi)
    assert metadata2 == {"t": 2}
    assert file_obj2 is None


def test_manager_uses_default_when_only_metadata_present(
    manager: context_mod.ContextStrategyManager,
) -> None:
    class WithMetadata:
        def __init__(self) -> None:
            self.metadata = {"d": 3}

    metadata, file_obj = manager.make_context(WithMetadata())
    assert metadata == {"d": 3}
    assert file_obj is None


def test_manager_returns_none_tuple_when_unhandled(manager: context_mod.ContextStrategyManager) -> None:
    metadata, file_obj = manager.make_context(object())
    assert metadata is None
    assert file_obj is None

#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the GNU General Public License Foundation; either version 2
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

import pytest

from picard.ui.itemviews import TreeItem
from picard.ui.itemviews.columns import (
    ALBUMVIEW_COLUMNS,
    FILEVIEW_COLUMNS,
)
from picard.ui.itemviews.custom_columns import DelegateColumn


@pytest.fixture
def album_keys() -> list[str]:
    return [c.key for c in ALBUMVIEW_COLUMNS]


@pytest.fixture
def file_keys() -> list[str]:
    return [c.key for c in FILEVIEW_COLUMNS]


@pytest.mark.parametrize(
    ("key", "expected_present"),
    [
        ("~match_quality", True),
        ("title", True),
        ("albumartist", True),
    ],
)
def test_album_view_expected_columns(album_keys: list[str], key: str, expected_present: bool) -> None:
    assert (key in album_keys) is expected_present


@pytest.mark.parametrize(
    ("key", "expected_present"),
    [
        ("~match_quality", False),
        ("title", True),
        ("albumartist", True),
    ],
)
def test_file_view_expected_columns(file_keys: list[str], key: str, expected_present: bool) -> None:
    assert (key in file_keys) is expected_present


def _index_of(columns_keys: list[str], key: str) -> int:
    return next(i for i, k in enumerate(columns_keys) if k == key)


def test_album_view_match_after_albumartist(album_keys: list[str]) -> None:
    idx_albumartist: int = _index_of(album_keys, "albumartist")
    idx_match: int = _index_of(album_keys, "~match_quality")
    assert idx_match == idx_albumartist + 1


def test_album_view_match_is_delegate_column_type() -> None:
    # Ensure the actual column instance at the expected index is DelegateColumn
    keys: list[str] = [c.key for c in ALBUMVIEW_COLUMNS]
    idx_match: int = _index_of(keys, "~match_quality")
    assert isinstance(ALBUMVIEW_COLUMNS[idx_match], DelegateColumn)


class _DummyObj:
    # Minimal object to satisfy TreeItem expectations
    ui_item: TreeItem | None = None

    def column(self, key: str) -> str:
        return ""


def test_treeitem_columns_fallback_when_detached() -> None:
    # When item is not attached to any view, it should safely fall back to FILEVIEW_COLUMNS
    item: TreeItem = TreeItem(_DummyObj(), parent=None)
    # Force detach simulation: ensure treeWidget() returns None
    assert item.treeWidget() is None
    assert item.columns is FILEVIEW_COLUMNS


def test_treeitem_columns_uses_tree_widget_columns() -> None:
    # When item is attached (or treeWidget returns a holder with a 'columns' attr), it should use those
    item: TreeItem = TreeItem(_DummyObj(), parent=None)

    class _Holder:
        def __init__(self, cols):
            self.columns = cols

    # Monkeypatch instance method treeWidget to return our holder
    item.treeWidget = lambda: _Holder(ALBUMVIEW_COLUMNS)  # type: ignore[method-assign]
    assert item.columns is ALBUMVIEW_COLUMNS


@pytest.mark.parametrize(
    ("keys", "must_exist"),
    [
        (["title", "~length", "artist", "albumartist"], True),
        (["~bitrate", "genre"], True),
    ],
)
def test_required_keys_present(keys: list[str], must_exist: bool, album_keys: list[str], file_keys: list[str]) -> None:
    for key in keys:
        assert (key in album_keys) is must_exist
        assert (key in file_keys) is must_exist

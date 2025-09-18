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

"""Test synchronization between column visibility and context menu checkboxes.

Tests the fix for the issue where newly registered columns appear in the table
but their checkboxes in the context menu remain unchecked.
"""

import pytest


class _MockColumn:
    """Mock column for testing."""

    def __init__(self, title: str, always_visible: bool = False) -> None:
        self.title = title
        self.always_visible = always_visible


class _MockColumns:
    """Mock columns collection for testing."""

    def __init__(self, columns: list[_MockColumn]) -> None:
        self._columns = columns

    def __iter__(self):
        return iter(self._columns)

    def __len__(self) -> int:
        return len(self._columns)

    def __getitem__(self, index: int) -> _MockColumn:
        return self._columns[index]

    def always_visible_columns(self) -> list[int]:
        """Return indices of always visible columns."""
        return [i for i, col in enumerate(self._columns) if col.always_visible]


class _MockParent:
    """Mock parent widget for testing."""

    def __init__(self) -> None:
        self._hidden_columns: set[int] = set()

    def setColumnHidden(self, column: int, hidden: bool) -> None:
        """Set column visibility."""
        if hidden:
            self._hidden_columns.add(column)
        else:
            self._hidden_columns.discard(column)

    def isColumnHidden(self, column: int) -> bool:
        """Check if column is hidden."""
        return column in self._hidden_columns


class _MockHeader:
    """Mock header with sync logic for testing."""

    def __init__(self, columns: _MockColumns, parent: _MockParent) -> None:
        self._columns = columns
        self._parent = parent
        self._always_visible_columns = set(columns.always_visible_columns())
        self._visible_columns = set(self._always_visible_columns)

    def sync_visible_columns(self) -> None:
        """Synchronize _visible_columns with actual column visibility state."""
        # Update always visible columns in case they changed
        self._always_visible_columns = set(self._columns.always_visible_columns())

        # For each column, check if it's actually visible in the table
        for i in range(len(self._columns)):
            if i in self._always_visible_columns:
                # Always visible columns should always be in _visible_columns
                self._visible_columns.add(i)
            else:
                # For other columns, check if they're actually hidden
                is_hidden = self._parent.isColumnHidden(i)
                if not is_hidden:
                    self._visible_columns.add(i)
                else:
                    self._visible_columns.discard(i)

    def show_column(self, column: int, show: bool) -> None:
        """Show or hide a column."""
        if column in self._always_visible_columns:
            # Always visible
            # Still execute following to ensure it is shown
            show = True
        self._parent.setColumnHidden(column, not show)
        if show:
            self._visible_columns.add(column)
        else:
            self._visible_columns.discard(column)


@pytest.fixture
def mock_parent() -> _MockParent:
    """Provide a mock parent widget."""
    return _MockParent()


@pytest.fixture
def basic_columns() -> _MockColumns:
    """Provide basic columns: one always visible, one regular."""
    columns = [
        _MockColumn("Title", always_visible=True),  # Always visible
        _MockColumn("Artist", always_visible=False),  # Regular column
    ]
    return _MockColumns(columns)


@pytest.fixture
def three_columns() -> _MockColumns:
    """Provide three columns: one always visible, two regular."""
    columns = [
        _MockColumn("Title", always_visible=True),  # Always visible
        _MockColumn("Artist", always_visible=False),  # Regular column
        _MockColumn("Album", always_visible=False),  # Regular column
    ]
    return _MockColumns(columns)


@pytest.fixture
def header_basic(basic_columns: _MockColumns, mock_parent: _MockParent) -> _MockHeader:
    """Provide a header with basic columns."""
    return _MockHeader(basic_columns, mock_parent)


@pytest.fixture
def header_three(three_columns: _MockColumns, mock_parent: _MockParent) -> _MockHeader:
    """Provide a header with three columns."""
    return _MockHeader(three_columns, mock_parent)


def test_initial_always_visible_columns(header_basic: _MockHeader) -> None:
    """Test that always visible columns are initially in _visible_columns."""
    assert header_basic._always_visible_columns == {0}  # Title column
    assert header_basic._visible_columns == {0}  # Only always visible column


def test_initial_regular_columns_not_visible(header_basic: _MockHeader) -> None:
    """Test that regular columns are not initially in _visible_columns."""
    assert 1 not in header_basic._visible_columns  # Artist column


@pytest.mark.parametrize("column_index", [1, 2])
def test_sync_adds_visible_regular_column(
    header_three: _MockHeader, mock_parent: _MockParent, column_index: int
) -> None:
    """Test that sync adds regular columns that are visible in parent."""
    # Initially, regular column is not in _visible_columns
    assert column_index not in header_three._visible_columns

    # Make column visible in parent
    mock_parent.setColumnHidden(column_index, False)

    # Sync the visible columns
    header_three.sync_visible_columns()

    # Column should now be in _visible_columns
    assert column_index in header_three._visible_columns


@pytest.mark.parametrize("column_index", [1, 2])
def test_sync_removes_hidden_regular_column(
    header_three: _MockHeader, mock_parent: _MockParent, column_index: int
) -> None:
    """Test that sync removes regular columns that are hidden in parent."""
    # Add column to _visible_columns first
    header_three._visible_columns.add(column_index)
    assert column_index in header_three._visible_columns

    # Hide column in parent
    mock_parent.setColumnHidden(column_index, True)

    # Sync the visible columns
    header_three.sync_visible_columns()

    # Column should no longer be in _visible_columns
    assert column_index not in header_three._visible_columns


def test_sync_preserves_always_visible_when_hidden(header_basic: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that always visible columns remain in _visible_columns even when hidden."""
    # Title column (index 0) is always visible
    assert 0 in header_basic._always_visible_columns
    assert 0 in header_basic._visible_columns

    # Try to hide the always visible column
    mock_parent.setColumnHidden(0, True)

    # Sync the visible columns
    header_basic.sync_visible_columns()

    # Always visible column should still be in _visible_columns
    assert 0 in header_basic._visible_columns


def test_sync_updates_always_visible_columns_when_changed(header_basic: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that sync updates _always_visible_columns when columns change."""
    # Initially, only column 0 is always visible
    assert header_basic._always_visible_columns == {0}

    # Create new columns with different always visible settings
    new_columns = [
        _MockColumn("Title", always_visible=True),  # Still always visible
        _MockColumn("Artist", always_visible=True),  # Now always visible
    ]
    header_basic._columns = _MockColumns(new_columns)

    # Sync the visible columns
    header_basic.sync_visible_columns()

    # _always_visible_columns should be updated
    assert header_basic._always_visible_columns == {0, 1}


def test_show_column_adds_to_visible_columns(header_basic: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that show_column adds regular columns to _visible_columns."""
    # Initially, column 1 is not visible
    assert 1 not in header_basic._visible_columns

    # Show column 1
    header_basic.show_column(1, True)

    # Column 1 should now be in _visible_columns
    assert 1 in header_basic._visible_columns
    # Parent should have column 1 visible
    assert not mock_parent.isColumnHidden(1)


def test_show_column_removes_from_visible_columns(header_basic: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that show_column removes regular columns from _visible_columns."""
    # Add column 1 to _visible_columns first
    header_basic._visible_columns.add(1)
    assert 1 in header_basic._visible_columns

    # Hide column 1
    header_basic.show_column(1, False)

    # Column 1 should no longer be in _visible_columns
    assert 1 not in header_basic._visible_columns
    # Parent should have column 1 hidden
    assert mock_parent.isColumnHidden(1)


def test_show_column_forces_always_visible_to_show(header_basic: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that show_column forces always visible columns to be shown."""
    # Title column (index 0) is always visible
    assert 0 in header_basic._always_visible_columns

    # Try to hide the always visible column
    header_basic.show_column(0, False)

    # Column should still be visible in parent (forced to show)
    assert not mock_parent.isColumnHidden(0)
    # Column should still be in _visible_columns
    assert 0 in header_basic._visible_columns


@pytest.mark.parametrize("show_value", [True, False])
def test_show_column_always_visible_ignores_show_parameter(
    header_basic: _MockHeader, mock_parent: _MockParent, show_value: bool
) -> None:
    """Test that show_column ignores show parameter for always visible columns."""
    # Title column (index 0) is always visible
    assert 0 in header_basic._always_visible_columns

    # Try to show/hide the always visible column
    header_basic.show_column(0, show_value)

    # Column should always be visible regardless of show_value
    assert not mock_parent.isColumnHidden(0)
    assert 0 in header_basic._visible_columns


def test_sync_handles_multiple_columns_correctly(header_three: _MockHeader, mock_parent: _MockParent) -> None:
    """Test that sync handles multiple columns with mixed visibility correctly."""
    # Set up mixed visibility: column 1 visible, column 2 hidden
    mock_parent.setColumnHidden(1, False)  # Visible
    mock_parent.setColumnHidden(2, True)  # Hidden

    # Sync the visible columns
    header_three.sync_visible_columns()

    # Check final state
    expected_visible = {0, 1}  # Always visible (0) + visible regular (1)
    assert header_three._visible_columns == expected_visible

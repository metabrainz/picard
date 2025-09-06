# -*- coding: utf-8 -*-
# pyright: reportMissingImports=false
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

"""List model for CustomColumnSpec entries."""

from collections.abc import Iterable

from PyQt6 import QtCore  # type: ignore[unresolved-import]

from picard.ui.itemviews.custom_columns.shared import DEFAULT_NEW_COLUMN_NAME
from picard.ui.itemviews.custom_columns.storage import CustomColumnSpec


class SpecListModel(QtCore.QAbstractListModel):
    """List model of CustomColumnSpec entries displaying titles."""

    def __init__(self, specs: list[CustomColumnSpec], parent: QtCore.QObject | None = None) -> None:
        """Initialize the model with specifications.

        Parameters
        ----------
        specs : list[CustomColumnSpec]
            Initial list of specifications.
        parent : QtCore.QObject | None, optional
            Parent object, by default None.
        """
        super().__init__(parent)
        self._specs: list[CustomColumnSpec] = specs

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        """Return number of rows for the model.

        Parameters
        ----------
        parent : QtCore.QModelIndex | QtCore.QPersistentModelIndex | None, optional
            Parent index for tree models (unused), by default None.

        Returns
        -------
        int
            Number of rows in the model.
        """
        return 0 if (parent and parent.isValid()) else len(self._specs)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        """Return data for a given index and role.

        Parameters
        ----------
        index : QtCore.QModelIndex
            Index to retrieve data for.
        role : int, optional
            Data role, by default Qt.DisplayRole.

        Returns
        -------
        object
            Value for the role; None if not applicable.
        """
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._specs):
            return None
        spec = self._specs[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return spec.title or DEFAULT_NEW_COLUMN_NAME
        return None

    # Helpers
    def specs(self) -> list[CustomColumnSpec]:
        """Return a copy of the current specifications.

        Returns
        -------
        list[CustomColumnSpec]
            Copy of internal spec list.
        """
        return list(self._specs)

    def spec_at(self, row: int) -> CustomColumnSpec:
        """Return the specification at a row.

        Parameters
        ----------
        row : int
            Row index.

        Returns
        -------
        CustomColumnSpec
            Specification at the given row.
        """
        return self._specs[row]

    def set_specs(self, specs: list[CustomColumnSpec]) -> None:
        """Replace the model's specifications and reset the model.

        Parameters
        ----------
        specs : list[CustomColumnSpec]
            New list of specifications.
        """
        self.beginResetModel()
        self._specs = specs
        self.endResetModel()

    def insert_spec(self, spec: CustomColumnSpec) -> int:
        """Insert a specification at the end and return its row.

        Parameters
        ----------
        spec : CustomColumnSpec
            Specification to insert.

        Returns
        -------
        int
            Row index of the inserted item.
        """
        self.beginInsertRows(QtCore.QModelIndex(), len(self._specs), len(self._specs))
        self._specs.append(spec)
        self.endInsertRows()
        return len(self._specs) - 1

    def update_spec(self, row: int, spec: CustomColumnSpec) -> None:
        """Update an existing specification.

        Parameters
        ----------
        row : int
            Row to update.
        spec : CustomColumnSpec
            New specification value.
        """
        self._specs[row] = spec
        idx = self.index(row)
        self.dataChanged.emit(idx, idx)

    def remove_row(self, row: int) -> None:
        """Remove a row from the model.

        Parameters
        ----------
        row : int
            Row index to remove.
        """
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._specs[row]
        self.endRemoveRows()

    def remove_rows(self, rows: Iterable[int]) -> None:
        """Remove multiple rows from the model efficiently.

        Parameters
        ----------
        rows : Iterable[int]
            Sorted or unsorted Iterable of row indices to remove.
        """
        if not rows:
            return
        # Remove in descending order to keep indices stable
        for row in sorted(set(rows), reverse=True):
            self.remove_row(row)

    def find_row_by_key(self, key: str) -> int:
        """Find the first row with the given key.

        Parameters
        ----------
        key : str
            Column key to search for.

        Returns
        -------
        int
            Row index if found, otherwise -1.
        """
        for i, s in enumerate(self._specs):
            if s.key == key:
                return i
        return -1

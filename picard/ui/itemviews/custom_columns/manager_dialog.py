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

"""Dialog to manage user-defined custom columns.

This dialog lists all persisted custom columns and allows the user to add,
edit, duplicate and delete entries. It delegates expression editing to
``CustomColumnExpressionDialog`` for SRP / SOC.
"""

from __future__ import annotations

from dataclasses import replace
from enum import IntEnum

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import gettext as _

from picard.ui.itemviews.custom_columns.expression_dialog import CustomColumnExpressionDialog
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnRegistrar,
    CustomColumnSpec,
    add_or_update_spec,
    load_specs_from_config,
    save_specs_to_config,
)


class _SpecsTableModel(QtCore.QAbstractTableModel):
    """Table model for custom column specs.

    Parameters
    ----------
    specs
        Initial list of specs to display.
    parent
        Parent QObject.
    """

    class ColumnIndex(IntEnum):
        TITLE = 0
        TYPE = 1
        EXPRESSION = 2
        ALIGN = 3
        WIDTH = 4

    HEADERS: dict[ColumnIndex, str] = {
        ColumnIndex.TITLE: _("Field Name"),
        ColumnIndex.TYPE: _("Type"),
        ColumnIndex.EXPRESSION: _("Expression"),
        ColumnIndex.ALIGN: _("Align"),
        ColumnIndex.WIDTH: _("Width"),
    }

    def __init__(self, specs: list[CustomColumnSpec], parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._specs: list[CustomColumnSpec] = specs

    # --- Model API ---------------------------------------------------------
    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        return 0 if (parent and parent.isValid()) else len(self._specs)

    def columnCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        return len(self.HEADERS)

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> object:
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            try:
                return self.HEADERS[self.ColumnIndex(section)]
            except (ValueError, KeyError):
                return None
        return None

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or index.row() >= len(self._specs):
            return None
        spec = self._specs[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            try:
                col = self.ColumnIndex(index.column())
            except ValueError:
                return None
            if col == self.ColumnIndex.TITLE:
                return spec.title
            if col == self.ColumnIndex.TYPE:
                return spec.kind.value
            if col == self.ColumnIndex.EXPRESSION:
                return spec.expression
            if col == self.ColumnIndex.ALIGN:
                return spec.align
            if col == self.ColumnIndex.WIDTH:
                return "" if spec.width is None else str(spec.width)
        return None

    # --- Helpers -----------------------------------------------------------
    def specs(self) -> list[CustomColumnSpec]:
        return list(self._specs)

    def spec_at(self, row: int) -> CustomColumnSpec:
        return self._specs[row]

    def set_specs(self, specs: list[CustomColumnSpec]) -> None:
        self.beginResetModel()
        self._specs = specs
        self.endResetModel()

    def insert_spec(self, spec: CustomColumnSpec) -> None:
        self.beginInsertRows(QtCore.QModelIndex(), len(self._specs), len(self._specs))
        self._specs.append(spec)
        self.endInsertRows()

    def update_spec(self, row: int, spec: CustomColumnSpec) -> None:
        self._specs[row] = spec
        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)

    def remove_row(self, row: int) -> None:
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._specs[row]
        self.endRemoveRows()


class CustomColumnsManagerDialog(QtWidgets.QDialog):
    """Management dialog for custom columns.

    The dialog is a thin controller view that delegates persistence to
    :mod:`picard.ui.itemviews.custom_columns.storage` and expression editing to
    :class:`~picard.ui.itemviews.custom_columns.expression_dialog.CustomColumnExpressionDialog`.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent=parent)
        # Renamed this to `Manage Columns` because we want to use the API for all columns, i.e. 'custom' columns == columns
        self.setWindowTitle(_("Manage Columns"))

        # Table + model
        self._table = QtWidgets.QTableView(self)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._on_double_clicked)

        self._model = _SpecsTableModel(load_specs_from_config(), parent=self)
        self._table.setModel(self._model)
        # Tweak header/section sizes
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        self._table.verticalHeader().setVisible(False)
        header.setDefaultSectionSize(100)
        header.resizeSection(_SpecsTableModel.ColumnIndex.TITLE, 150)
        header.setSectionResizeMode(_SpecsTableModel.ColumnIndex.TITLE, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.resizeSection(_SpecsTableModel.ColumnIndex.TYPE, 100)
        header.setSectionResizeMode(_SpecsTableModel.ColumnIndex.TYPE, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.resizeSection(_SpecsTableModel.ColumnIndex.EXPRESSION, 160)
        header.setSectionResizeMode(_SpecsTableModel.ColumnIndex.EXPRESSION, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.resizeSection(_SpecsTableModel.ColumnIndex.ALIGN, 80)
        header.setSectionResizeMode(_SpecsTableModel.ColumnIndex.ALIGN, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.resizeSection(_SpecsTableModel.ColumnIndex.WIDTH, 60)
        header.setSectionResizeMode(_SpecsTableModel.ColumnIndex.WIDTH, QtWidgets.QHeaderView.ResizeMode.Fixed)

        # Buttons
        self._btn_add = QtWidgets.QPushButton(_("Add…"), self)
        self._btn_edit = QtWidgets.QPushButton(_("Edit…"), self)
        self._btn_duplicate = QtWidgets.QPushButton(_("Duplicate"), self)
        self._btn_delete = QtWidgets.QPushButton(_("Delete"), self)
        self._btn_apply = QtWidgets.QPushButton(_("Make It So!"), self)
        self._btn_close = QtWidgets.QPushButton(_("Close"), self)

        self._btn_add.clicked.connect(self._on_add)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_duplicate.clicked.connect(self._on_duplicate)
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_apply.clicked.connect(self._on_apply)
        # Persist immediately on window close if there are unapplied changes
        self.finished.connect(lambda _: self._on_apply() if self._dirty else None)
        self._btn_close.clicked.connect(self.close)

        # Layout
        buttons = QtWidgets.QHBoxLayout()
        for b in (self._btn_add, self._btn_edit, self._btn_duplicate, self._btn_delete):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_apply)
        buttons.addWidget(self._btn_close)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._table)
        layout.addLayout(buttons)

        self.resize(800, 400)
        self._dirty = False
        self._deleted_keys: set[str] = set()
        self._update_apply()

    # --- Actions ------------------------------------------------------------
    def _selected_row(self) -> int:
        idxs = self._table.selectionModel().selectedRows()
        return idxs[0].row() if idxs else -1

    def _on_double_clicked(self, index: QtCore.QModelIndex) -> None:
        if index.isValid():
            self._on_edit()

    def _on_add(self) -> None:
        dlg = CustomColumnExpressionDialog(parent=self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            spec = dlg.result_spec
            if spec:
                # Persist only; defer UI registration to Apply
                add_or_update_spec(spec)
                self._model.insert_spec(spec)
                save_specs_to_config(self._model.specs())
                self._mark_dirty()

    def _on_edit(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        dlg = CustomColumnExpressionDialog(existing_spec=spec, parent=self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_spec = dlg.result_spec
            if not new_spec:
                return
            # Persist update (key change handled by upsert); defer UI updates to Apply
            add_or_update_spec(new_spec)
            self._model.update_spec(row, new_spec)
            if new_spec.key != spec.key:
                # Track old key for robust unregister on apply
                self._deleted_keys.add(spec.key)
                # Ensure old column hides immediately if present
                self._make_column_nondefault(spec.key)
                self._refresh_all_views()
            save_specs_to_config(self._model.specs())
            self._mark_dirty()

    def _on_duplicate(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        dup = replace(spec)
        # Create a new unique key and title suffix
        base_key = spec.key
        suffix = 1
        keys = {s.key for s in self._model.specs()}
        while f"{base_key}_{suffix}" in keys:
            suffix += 1
        dup.key = f"{base_key}_{suffix}"
        dup.title = f"{spec.title} ({suffix})"
        dlg = CustomColumnExpressionDialog(existing_spec=dup, parent=self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            result = dlg.result_spec
            if result:
                add_or_update_spec(result)
                self._model.insert_spec(result)
                save_specs_to_config(self._model.specs())
                self._mark_dirty()

    def _on_delete(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        confirm = QtWidgets.QMessageBox.question(
            self,
            _("Delete Custom Column"),
            _("Are you sure you want to delete the column ‘{title}’?").format(title=spec.title),
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            # Defer deletion to Apply: track key, update model/config, mark dirty
            self._deleted_keys.add(spec.key)
            self._model.remove_row(row)
            save_specs_to_config(self._model.specs())
            self._mark_dirty()

    def _on_apply(self) -> None:
        # First ensure any deleted keys are unregistered live
        if self._deleted_keys:
            registrar = CustomColumnRegistrar()
            # Hide deleted columns first to avoid lingering default visibility
            for key in list(self._deleted_keys):
                self._make_column_nondefault(key)
            self._refresh_all_views()
            for key in list(self._deleted_keys):
                registrar.unregister_column(key)
            self._deleted_keys.clear()

        save_specs_to_config(self._model.specs())
        # Best-effort to ensure live registry matches persisted specs
        registrar = CustomColumnRegistrar()
        for spec in self._model.specs():
            registrar.register_column(spec)
        cfg = get_config()
        if cfg is not None:
            cfg.sync()
        self._dirty = False
        self._update_apply()
        self._refresh_all_views()

    def _refresh_current_view(self) -> None:
        """Refresh the header of the view that opened this dialog.

        This ensures changes to the columns list are reflected immediately
        (section count, labels, visibility menu) without requiring restart.
        """
        parent = self.parent()
        # The manager is opened from ConfigurableColumnsHeader context menu
        # where the header is passed as parent. The corresponding view is
        # the header's parent widget.
        if parent is None:
            return
        header = parent
        from picard.ui.widgets.configurablecolumnsheader import ConfigurableColumnsHeader

        if isinstance(header, ConfigurableColumnsHeader):
            view = header.parent()
            if hasattr(view, 'restore_default_columns'):
                view.restore_default_columns()

    def _refresh_all_views(self) -> None:
        """Refresh headers for all open views that use recognized columns."""
        from PyQt6 import QtWidgets

        from picard.ui.itemviews.custom_columns.shared import get_recognized_view_columns

        app = QtWidgets.QApplication.instance()
        if not app:
            return
        recognized = set(get_recognized_view_columns().values())
        for widget in app.allWidgets():
            if getattr(widget, 'columns', None) in recognized and hasattr(widget, 'restore_default_columns'):
                widget.restore_default_columns()

    def _make_column_nondefault(self, key: str) -> None:
        """Set is_default to False for any live column matching key across views."""
        from picard.ui.itemviews.custom_columns.shared import get_recognized_view_columns

        for cols in get_recognized_view_columns().values():
            try:
                pos = cols.pos(key)
            except KeyError:
                continue
            col = cols[pos]
            col.is_default = False

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._update_apply()

    def _update_apply(self) -> None:
        self._btn_apply.setEnabled(self._dirty)

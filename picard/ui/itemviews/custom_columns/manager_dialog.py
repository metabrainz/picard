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

"""Manage user-defined custom columns in a single dialog.

The dialog shows three panes:
- Left: a list of existing custom column definitions
- Middle: editor for the selected definition
- Right: scripting documentation (functions and tags)

The UI does not expose a column "type"; all user-created columns are Script
columns. Internally, storage still supports multiple kinds.
"""

from __future__ import annotations

from dataclasses import replace

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.i18n import gettext as _

from picard.ui.itemviews.custom_columns.shared import (
    DEFAULT_ADD_TO,
    format_add_to,
    get_align_options,
    get_ordered_view_presentations,
    normalize_align_name,
    parse_add_to,
)
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnRegistrar,
    CustomColumnSpec,
    load_specs_from_config,
    save_specs_to_config,
)
from picard.ui.util import StandardButton
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget
from picard.ui.widgets.scripttextedit import ScriptTextEdit


class _SpecListModel(QtCore.QAbstractListModel):
    """List model of CustomColumnSpec entries displaying titles."""

    def __init__(self, specs: list[CustomColumnSpec], parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._specs: list[CustomColumnSpec] = specs

    def rowCount(self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None) -> int:
        return 0 if (parent and parent.isValid()) else len(self._specs)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._specs):
            return None
        spec = self._specs[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return spec.title or spec.key
        return None

    # Helpers
    def specs(self) -> list[CustomColumnSpec]:
        return list(self._specs)

    def spec_at(self, row: int) -> CustomColumnSpec:
        return self._specs[row]

    def set_specs(self, specs: list[CustomColumnSpec]) -> None:
        self.beginResetModel()
        self._specs = specs
        self.endResetModel()

    def insert_spec(self, spec: CustomColumnSpec) -> int:
        self.beginInsertRows(QtCore.QModelIndex(), len(self._specs), len(self._specs))
        self._specs.append(spec)
        self.endInsertRows()
        return len(self._specs) - 1

    def update_spec(self, row: int, spec: CustomColumnSpec) -> None:
        self._specs[row] = spec
        idx = self.index(row)
        self.dataChanged.emit(idx, idx)

    def remove_row(self, row: int) -> None:
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._specs[row]
        self.endRemoveRows()

    def find_row_by_key(self, key: str) -> int:
        for i, s in enumerate(self._specs):
            if s.key == key:
                return i
        return -1


class CustomColumnsManagerDialog(QtWidgets.QDialog):
    """Single-window UI to manage custom columns."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(_("Manage Custom Columns"))

        # Left: list + controls (Duplicate/Delete)
        self._list = QtWidgets.QListView(self)
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self._model = _SpecListModel(load_specs_from_config(), parent=self)
        self._list.setModel(self._model)
        self._btn_duplicate = QtWidgets.QPushButton(_("Duplicate"), self)
        self._btn_delete = QtWidgets.QPushButton(_("Delete"), self)
        self._btn_duplicate.clicked.connect(self._on_duplicate)
        self._btn_delete.clicked.connect(self._on_delete)
        left_panel = QtWidgets.QWidget(self)
        left_v = QtWidgets.QVBoxLayout(left_panel)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.addWidget(self._list)
        left_buttons = QtWidgets.QHBoxLayout()
        left_buttons.addWidget(self._btn_duplicate)
        left_buttons.addWidget(self._btn_delete)
        left_v.addLayout(left_buttons)

        # Middle: editor
        self._editor_panel = QtWidgets.QWidget(self)
        form = QtWidgets.QFormLayout(self._editor_panel)

        self._title = QtWidgets.QLineEdit(self._editor_panel)
        self._key = QtWidgets.QLineEdit(self._editor_panel)
        self._key.setPlaceholderText(_("Auto-derived from Column Title"))
        self._expression = ScriptTextEdit(self._editor_panel)
        self._expression.setPlaceholderText("%artist% - %title%")
        self._width = QtWidgets.QSpinBox(self._editor_panel)
        self._width.setRange(0, 9999)
        self._width.setSpecialValueText("")
        self._width.setValue(100)
        self._align = QtWidgets.QComboBox(self._editor_panel)
        for label, enum_val in get_align_options():
            self._align.addItem(label, enum_val)

        views_layout = QtWidgets.QHBoxLayout()
        self._view_checkboxes: dict[str, QtWidgets.QCheckBox] = {}
        for vp in get_ordered_view_presentations():
            cb = QtWidgets.QCheckBox(_(vp.title), self._editor_panel)
            cb.setChecked(True)
            if vp.tooltip:
                cb.setToolTip(_(vp.tooltip))
            self._view_checkboxes[vp.id] = cb
            views_layout.addWidget(cb)

        form.addRow(_("Column Title") + "*", self._title)
        form.addRow(_("Key"), self._key)
        form.addRow(_("Expression") + "*", self._expression)
        form.addRow(_("Width"), self._width)
        form.addRow(_("Align"), self._align)
        form.addRow(_("Add to views"), views_layout)
        # Add button at bottom of middle pane
        self._btn_add = QtWidgets.QPushButton(_("Add"), self._editor_panel)
        self._btn_add.clicked.connect(self._on_add)
        add_row = QtWidgets.QHBoxLayout()
        add_row.addStretch(1)
        add_row.addWidget(self._btn_add)
        form.addRow(add_row)

        # Right: docs
        self._docs = ScriptingDocumentationWidget(include_link=True, parent=self)

        # Splitter
        self._splitter = QtWidgets.QSplitter(self)
        self._splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.addWidget(self._docs)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 2)
        self._splitter.setStretchFactor(2, 2)

        # Buttons (OK/Cancel only in dialog button box)
        self._buttonbox = QtWidgets.QDialogButtonBox(self)
        ok = StandardButton(StandardButton.OK)
        ok.setText(_("Make It So!"))
        self._buttonbox.addButton(ok, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self._buttonbox.addButton(
            StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.ButtonRole.RejectRole
        )
        self._btn_apply = ok

        self._buttonbox.accepted.connect(self.accept)
        self._buttonbox.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._splitter)
        layout.addWidget(self._buttonbox)

        self.resize(1024, 540)
        self._dirty = False
        self._deleted_keys: set[str] = set()
        self._populating: bool = False
        self._current_row: int = -1
        self._update_apply()

        # Selection and bindings
        sel = self._list.selectionModel()
        sel.selectionChanged.connect(self._on_selection_changed)
        self._title.textChanged.connect(self._on_form_changed)
        self._key.textChanged.connect(self._on_form_changed)
        self._expression.textChanged.connect(self._on_form_changed)
        self._width.valueChanged.connect(self._on_form_changed)
        self._align.currentIndexChanged.connect(self._on_form_changed)
        for cb in self._view_checkboxes.values():
            cb.stateChanged.connect(self._on_form_changed)

        # If no columns exist yet, enable editing immediately for quick entry
        if self._model.rowCount() > 0:
            self._list.setCurrentIndex(self._model.index(0))
        else:
            # Enable inputs with sensible defaults, so users can type then click Add
            self._prepare_editor_for_new_entry()

    # --- Actions
    def accept(self) -> None:
        self._commit_form_to_model()
        self._on_apply()
        super().accept()

    def reject(self) -> None:
        self._dirty = False
        super().reject()

    # List / form coordination
    def _selected_row(self) -> int:
        indexes = self._list.selectionModel().selectedIndexes()
        return indexes[0].row() if indexes else -1

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        del selected, deselected
        self._commit_form_to_model()
        self._current_row = self._selected_row()
        spec = self._model.spec_at(self._current_row) if self._current_row >= 0 else None
        self._populate_form(spec)

    def _populate_form(self, spec: CustomColumnSpec | None) -> None:
        self._populating = True
        try:
            enabled = spec is not None
            for w in (self._title, self._key, self._expression, self._width, self._align):
                w.setEnabled(enabled)
            for cb in self._view_checkboxes.values():
                cb.setEnabled(enabled)
            if not spec:
                self._title.clear()
                self._key.clear()
                self._expression.setPlainText("")
                self._width.setValue(100)
                idx = self._align.findData(normalize_align_name("LEFT"))
                if idx >= 0:
                    self._align.setCurrentIndex(idx)
                for cb in self._view_checkboxes.values():
                    cb.setChecked(True)
                return

            self._title.setText(spec.title)
            self._key.setText(spec.key)
            self._expression.setPlainText(spec.expression)
            self._width.setValue(int(spec.width) if spec.width is not None else 0)
            idx = self._align.findData(normalize_align_name(spec.align))
            if idx >= 0:
                self._align.setCurrentIndex(idx)
            views = parse_add_to(getattr(spec, 'add_to', DEFAULT_ADD_TO))
            for view_id, cb in self._view_checkboxes.items():
                cb.setChecked(view_id in views)
        finally:
            self._populating = False

    def _on_form_changed(self, *args) -> None:  # type: ignore[no-untyped-def]
        del args
        if self._populating:
            return
        derived = self._derive_key_from_title(self._title.text())
        self._key.setPlaceholderText(derived or _("Auto-derived from Column Title"))
        self._mark_dirty()

    def _collect_form(self) -> CustomColumnSpec | None:
        if self._current_row < 0:
            return None
        title = self._title.text().strip()
        key_input = self._key.text().strip()
        key = key_input or self._derive_key_from_title(title)
        expr = self._expression.toPlainText().strip()
        width = int(self._width.value()) or None
        align = "RIGHT" if normalize_align_name(self._align.currentData()).name == "RIGHT" else "LEFT"
        selected_views: list[str] = [vid for vid, cb in self._view_checkboxes.items() if cb.isChecked()]
        add_to = format_add_to(selected_views)
        old = self._model.spec_at(self._current_row)
        kind = CustomColumnKind.SCRIPT if old.kind != CustomColumnKind.SCRIPT else old.kind
        return CustomColumnSpec(
            title=title,
            key=key,
            kind=kind,
            expression=expr,
            width=width,
            align=align,
            always_visible=False,
            add_to=add_to,
            transform=None,
        )

    def _commit_form_to_model(self) -> None:
        # Only commit when editing a valid, existing row
        if self._populating or self._current_row < 0 or self._current_row >= self._model.rowCount():
            return
        new_spec = self._collect_form()
        if new_spec is None:
            return
        old = self._model.spec_at(self._current_row)
        if new_spec.key and old.key and new_spec.key != old.key:
            self._deleted_keys.add(old.key)
        self._model.update_spec(self._current_row, new_spec)

    def _on_add(self) -> None:
        # Create a new spec from the form values and insert it
        # Works both when editing an existing item or preparing a new one
        title = self._title.text().strip()
        expr = self._expression.toPlainText().strip()
        if not title or not expr:
            QtWidgets.QMessageBox.warning(self, _("Invalid"), _("Both Title and Expression are required."))
            return
        key_input = self._key.text().strip()
        key = key_input or self._derive_key_from_title(title)
        width = int(self._width.value()) or None
        align = "RIGHT" if normalize_align_name(self._align.currentData()).name == "RIGHT" else "LEFT"
        selected_views: list[str] = [vid for vid, cb in self._view_checkboxes.items() if cb.isChecked()]
        add_to = format_add_to(selected_views)
        spec = CustomColumnSpec(
            title=title,
            key=key,
            kind=CustomColumnKind.SCRIPT,
            expression=expr,
            width=width,
            align=align,
            always_visible=False,
            add_to=add_to,
            transform=None,
        )
        # If an entry with this key exists, update it; otherwise insert new
        existing_row = self._model.find_row_by_key(spec.key)
        if existing_row >= 0:
            self._model.update_spec(existing_row, spec)
        else:
            self._model.insert_spec(spec)
        self._mark_dirty()
        # Prepare a fresh entry for subsequent adds so the key auto-derives
        self._list.clearSelection()
        self._prepare_editor_for_new_entry()

    def _on_duplicate(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        dup = replace(spec)
        base_key = spec.key
        suffix = 1
        keys = {s.key for s in self._model.specs()}
        while f"{base_key}_{suffix}" in keys:
            suffix += 1
        dup.key = f"{base_key}_{suffix}"
        dup.title = f"{spec.title} ({suffix})"
        new_row = self._model.insert_spec(dup)
        self._list.setCurrentIndex(self._model.index(new_row))
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
            self._deleted_keys.add(spec.key)
            self._model.remove_row(row)
            # Update selection to a valid row (next or previous) and clear editor if none
            count = self._model.rowCount()
            if count > 0:
                new_row = min(row, count - 1)
                self._list.setCurrentIndex(self._model.index(new_row))
            else:
                self._list.clearSelection()
                self._prepare_editor_for_new_entry()
            self._mark_dirty()

    def _on_apply(self) -> None:
        self._commit_form_to_model()

        # Validate specs before persisting
        for idx, spec in enumerate(self._model.specs()):
            if not spec.title.strip():
                QtWidgets.QMessageBox.warning(self, _("Invalid"), _("Column Title is required."))
                self._list.setCurrentIndex(self._model.index(idx))
                return
            if not spec.expression.strip():
                QtWidgets.QMessageBox.warning(self, _("Invalid"), _("Expression is required."))
                self._list.setCurrentIndex(self._model.index(idx))
                return
            if not spec.key.strip():
                spec.key = self._derive_key_from_title(spec.title)
                self._model.update_spec(idx, spec)

        if self._deleted_keys:
            registrar = CustomColumnRegistrar()
            for key in list(self._deleted_keys):
                registrar.unregister_column(key)
            self._deleted_keys.clear()

        # De-duplicate by key, keeping last occurrence
        specs = self._model.specs()
        seen: set[str] = set()
        dedup_reversed: list[CustomColumnSpec] = []
        for s in reversed(specs):
            if s.key in seen:
                continue
            seen.add(s.key)
            dedup_reversed.append(s)
        dedup_specs = list(reversed(dedup_reversed))
        if len(dedup_specs) != len(specs):
            self._model.set_specs(dedup_specs)

        save_specs_to_config(self._model.specs())
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
        parent = self.parent()
        if parent is None:
            return
        header = parent
        from picard.ui.widgets.configurablecolumnsheader import ConfigurableColumnsHeader

        if isinstance(header, ConfigurableColumnsHeader):
            view = header.parent()
            set_header = getattr(view, 'setHeaderLabels', None)
            set_count = getattr(view, 'setColumnCount', None)
            if callable(set_header):
                labels = tuple(_(c.title) for c in view.columns)
                if callable(set_count):
                    set_count(len(view.columns))
                set_header(labels)

    def _refresh_all_views(self) -> None:
        from picard.ui.columns import Columns as _Columns
        from picard.ui.itemviews.custom_columns.shared import get_recognized_view_columns

        app = QtWidgets.QApplication.instance() if hasattr(QtWidgets, 'QApplication') else None
        if not app:
            return
        recognized = set(get_recognized_view_columns().values())
        for widget in QtWidgets.QApplication.allWidgets():
            cols = getattr(widget, 'columns', None)
            set_header = getattr(widget, 'setHeaderLabels', None)
            set_count = getattr(widget, 'setColumnCount', None)
            if cols in recognized and callable(set_header):
                if isinstance(cols, _Columns):
                    labels = tuple(_(c.title) for c in cols)
                    if callable(set_count):
                        set_count(len(cols))
                    set_header(labels)

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._update_apply()

    def _update_apply(self) -> None:
        self._btn_apply.setEnabled(self._dirty)

    @staticmethod
    def _derive_key_from_title(name: str) -> str:
        import re

        text = name.strip().lower().replace(" ", "_")
        text = re.sub(r"[^a-z0-9_-]", "_", text)
        text = re.sub(r"_+", "_", text)
        return text

    # New helper to enable and clear editor for quick new entry
    def _prepare_editor_for_new_entry(self) -> None:
        self._current_row = -1
        self._populating = True
        try:
            for w in (self._title, self._key, self._expression, self._width, self._align):
                w.setEnabled(True)
            for cb in self._view_checkboxes.values():
                cb.setEnabled(True)
            self._title.clear()
            self._key.clear()
            # Reset placeholder for auto-derived behavior
            self._key.setPlaceholderText(_("Auto-derived from Column Title"))
            self._expression.setPlainText("")
            self._width.setValue(100)
            idx = self._align.findData(normalize_align_name("LEFT"))
            if idx >= 0:
                self._align.setCurrentIndex(idx)
            for cb in self._view_checkboxes.values():
                cb.setChecked(True)
        finally:
            self._populating = False

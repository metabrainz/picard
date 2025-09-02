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

from contextlib import contextmanager
from dataclasses import dataclass, replace
import itertools

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
from picard.ui.itemviews.custom_columns.validation import (
    ColumnSpecValidator,
    ValidationContext,
)
from picard.ui.util import StandardButton
from picard.ui.widgets.scriptdocumentation import ScriptingDocumentationWidget
from picard.ui.widgets.scripttextedit import ScriptTextEdit


@dataclass(frozen=True)
class DialogConfig:
    """Configuration constants for the dialog UI and defaults."""

    DEFAULT_WIDTH: int = 100
    MIN_WIDTH: int = 0
    MAX_WIDTH: int = 9999
    DIALOG_WIDTH: int = 1024
    DIALOG_HEIGHT: int = 540


class ViewSelector(QtWidgets.QWidget):
    """Widget for selecting which views to add the column to."""

    changed = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the view selector.

        Parameters
        ----------
        parent : QtWidgets.QWidget | None, optional
            Parent widget, by default None.
        """
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._checkboxes: dict[str, QtWidgets.QCheckBox] = {}
        for vp in get_ordered_view_presentations():
            cb = QtWidgets.QCheckBox(_(vp.title), self)
            cb.setChecked(True)
            if vp.tooltip:
                cb.setToolTip(_(vp.tooltip))
            cb.stateChanged.connect(self.changed.emit)
            self._checkboxes[vp.id] = cb
            layout.addWidget(cb)

    def get_selected(self) -> list[str]:
        """Return the list of selected view identifiers.

        Returns
        -------
        list[str]
            Selected view identifiers.
        """
        return [vid for vid, cb in self._checkboxes.items() if cb.isChecked()]

    def set_selected(self, view_ids: set[str]) -> None:
        """Set the selection state of views by identifiers.

        Parameters
        ----------
        view_ids : set[str]
            Identifiers of views to mark as selected; others will be unselected.
        """
        for vid, cb in self._checkboxes.items():
            cb.setChecked(vid in view_ids)

    def select_all(self) -> None:
        """Select all available views."""
        for cb in self._checkboxes.values():
            cb.setChecked(True)


class ViewRefresher:
    """Handles refreshing column headers across relevant views."""

    @staticmethod
    def refresh_all_views() -> None:
        """Refresh headers for all recognized column views.

        Notes
        -----
        Iterates over all application widgets and updates header labels for
        recognized column sets.
        """
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


class _SpecListModel(QtCore.QAbstractListModel):
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
            return spec.title or spec.key
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


class CustomColumnsManagerDialog(QtWidgets.QDialog):
    """Single-window UI to manage custom columns."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the custom columns manager dialog.

        Parameters
        ----------
        parent : QtWidgets.QWidget | None, optional
            Parent widget, by default None.
        """
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
        self._width.setRange(DialogConfig.MIN_WIDTH, DialogConfig.MAX_WIDTH)
        self._width.setSpecialValueText("")
        self._width.setValue(DialogConfig.DEFAULT_WIDTH)
        self._align = QtWidgets.QComboBox(self._editor_panel)
        for label, enum_val in get_align_options():
            self._align.addItem(label, enum_val)

        self._view_selector = ViewSelector(self._editor_panel)

        form.addRow(_("Column Title") + "*", self._title)
        form.addRow(_("Key"), self._key)
        form.addRow(_("Expression") + "*", self._expression)
        form.addRow(_("Width"), self._width)
        form.addRow(_("Align"), self._align)
        form.addRow(_("Add to views"), self._view_selector)
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

        self.resize(DialogConfig.DIALOG_WIDTH, DialogConfig.DIALOG_HEIGHT)
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
        self._view_selector.changed.connect(self._on_form_changed)

        # If no columns exist yet, enable editing immediately for quick entry
        if self._model.rowCount() > 0:
            self._list.setCurrentIndex(self._model.index(0))
        else:
            # Enable inputs with sensible defaults, so users can type then click Add
            self._prepare_editor_for_new_entry()

    # --- Actions
    def accept(self) -> None:
        """Apply changes and close the dialog with acceptance."""
        self._commit_form_to_model()
        self._on_apply()
        super().accept()

    def reject(self) -> None:
        """Close the dialog discarding unsaved changes."""
        self._dirty = False
        super().reject()

    # List / form coordination
    def _selected_row(self) -> int:
        """Return the currently selected row index.

        Returns
        -------
        int
            Selected row index, or -1 if none is selected.
        """
        indexes = self._list.selectionModel().selectedIndexes()
        return indexes[0].row() if indexes else -1

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        """Handle selection change in the list and populate the editor.

        Parameters
        ----------
        selected : QtCore.QItemSelection
            Newly selected indexes (unused).
        deselected : QtCore.QItemSelection
            Deselected indexes (unused).
        """
        del selected, deselected
        self._commit_form_to_model()
        self._current_row = self._selected_row()
        spec = self._model.spec_at(self._current_row) if self._current_row >= 0 else None
        self._populate_form(spec)

    def _populate_form(self, spec: CustomColumnSpec | None) -> None:
        """Populate the editor form with the given specification.

        Parameters
        ----------
        spec : CustomColumnSpec | None
            Specification to populate, or None to clear for new entry.
        """
        with self._populating_context():
            enabled = spec is not None
            for w in (self._title, self._key, self._expression, self._width, self._align):
                w.setEnabled(enabled)
            self._view_selector.setEnabled(enabled)
            if not spec:
                self._title.clear()
                self._key.clear()
                self._expression.setPlainText("")
                self._width.setValue(DialogConfig.DEFAULT_WIDTH)
                idx = self._align.findData(normalize_align_name("LEFT"))
                if idx >= 0:
                    self._align.setCurrentIndex(idx)
                self._view_selector.select_all()
                return

            self._title.setText(spec.title)
            self._key.setText(spec.key)
            self._expression.setPlainText(spec.expression)
            self._width.setValue(int(spec.width) if spec.width is not None else 0)
            idx = self._align.findData(normalize_align_name(spec.align))
            if idx >= 0:
                self._align.setCurrentIndex(idx)
            views = parse_add_to(getattr(spec, 'add_to', DEFAULT_ADD_TO))
            self._view_selector.set_selected(set(views))

    def _on_form_changed(self, *args) -> None:  # type: ignore[no-untyped-def]
        """Mark dialog as dirty and update derived key placeholder."""
        del args
        if self._populating:
            return
        derived = self._derive_key_from_title(self._title.text())
        self._key.setPlaceholderText(derived or _("Auto-derived from Column Title"))
        self._mark_dirty()

    def _collect_form(self) -> CustomColumnSpec | None:
        """Collect editor form values into a `CustomColumnSpec`.

        Returns
        -------
        CustomColumnSpec | None
            The collected spec if editing an existing row; otherwise None.
        """
        if self._current_row < 0:
            return None
        title = self._title.text().strip()
        key_input = self._key.text().strip()
        key = key_input or self._derive_key_from_title(title)
        expr = self._expression.toPlainText().strip()
        width = int(self._width.value()) or None
        align = "RIGHT" if normalize_align_name(self._align.currentData()).name == "RIGHT" else "LEFT"
        selected_views: list[str] = self._view_selector.get_selected()
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
        """Commit current editor values to the selected model row if valid."""
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
        """Create or update a specification based on editor form values."""
        # Create a new spec from the form values and insert it
        # Works both when editing an existing item or preparing a new one
        title = self._title.text().strip()
        expr = self._expression.toPlainText().strip()
        key_input = self._key.text().strip()
        key = key_input or self._derive_key_from_title(title)
        width = int(self._width.value()) or None
        align = "RIGHT" if normalize_align_name(self._align.currentData()).name == "RIGHT" else "LEFT"
        selected_views: list[str] = self._view_selector.get_selected()
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

        # Validate using centralized validation
        validator = ColumnSpecValidator()
        existing_keys = {s.key for s in self._model.specs() if s.key}
        context = ValidationContext(existing_keys - {spec.key})
        report = validator.validate(spec, context)
        if not report.is_valid:
            error_messages = [result.message for result in report.errors]
            QtWidgets.QMessageBox.warning(self, _("Invalid"), "\n".join(error_messages))
            return

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
        """Duplicate the selected specification with a unique key and title."""
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        dup = replace(spec)
        base_key = spec.key
        unique_key = self._generate_unique_key(base_key)
        dup.key = unique_key
        suffix_text = "1"
        prefix = f"{base_key}_"
        if unique_key.startswith(prefix):
            remainder = unique_key[len(prefix) :]
            if remainder.isdigit():
                suffix_text = remainder
        dup.title = f"{spec.title} ({suffix_text})"
        new_row = self._model.insert_spec(dup)
        self._list.setCurrentIndex(self._model.index(new_row))
        self._mark_dirty()

    def _on_delete(self) -> None:
        """Delete the currently selected specification after confirmation."""
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
        """Validate, persist, and register custom column specifications."""
        self._commit_form_to_model()

        # Validate specs before persisting
        all_specs = self._model.specs()
        validator = ColumnSpecValidator()
        reports = validator.validate_multiple(all_specs)

        # Find first invalid spec
        invalid_specs = [(key, report) for key, report in reports.items() if not report.is_valid]
        if invalid_specs:
            first_key, first_report = invalid_specs[0]
            error_messages = [result.message for result in first_report.errors]
            QtWidgets.QMessageBox.warning(self, _("Invalid"), "\n".join(error_messages))

            # Find the index of the first invalid spec to select it
            for idx, spec in enumerate(all_specs):
                spec_key = spec.key or f"<unnamed:{id(spec)}>"
                if spec_key == first_key:
                    self._list.setCurrentIndex(self._model.index(idx))
                    break
            return

        # Fill missing keys after validation
        for idx, spec in enumerate(all_specs):
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
        ViewRefresher.refresh_all_views()

    def _mark_dirty(self) -> None:
        """Mark the dialog state as modified and update Apply button."""
        self._dirty = True
        self._update_apply()

    def _update_apply(self) -> None:
        """Enable or disable the Apply button based on dirty state."""
        self._btn_apply.setEnabled(self._dirty)

    @staticmethod
    def _derive_key_from_title(name: str) -> str:
        """Derive a normalized key from a column title.

        Parameters
        ----------
        name : str
            Column title to derive the key from.

        Returns
        -------
        str
            ASCII-only, lowercase, underscore-separated key.
        """
        import re
        import unicodedata

        normalized = unicodedata.normalize('NFKD', name.strip().lower())
        ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
        key = re.sub(r'[^a-z0-9]+', '_', ascii_text)
        return key.strip('_')

    def _generate_unique_key(self, base_key: str) -> str:
        """Generate a unique key based on a base key.

        Parameters
        ----------
        base_key : str
            Desired base key.

        Returns
        -------
        str
            Unique key not currently used by any specification.
        """
        existing_keys = {s.key for s in self._model.specs()}
        if base_key not in existing_keys:
            return base_key
        for suffix in itertools.count(1):
            candidate = f"{base_key}_{suffix}"
            if candidate not in existing_keys:
                return candidate
        # Fallback (should not be reached)
        return base_key

    # New helper to enable and clear editor for quick new entry
    def _prepare_editor_for_new_entry(self) -> None:
        """Prepare the editor for quickly adding a new entry."""
        self._current_row = -1
        with self._populating_context():
            for w in (self._title, self._key, self._expression, self._width, self._align):
                w.setEnabled(True)
            self._view_selector.setEnabled(True)
            self._title.clear()
            self._key.clear()
            # Reset placeholder for auto-derived behavior
            self._key.setPlaceholderText(_("Auto-derived from Column Title"))
            self._expression.setPlainText("")
            self._width.setValue(DialogConfig.DEFAULT_WIDTH)
            idx = self._align.findData(normalize_align_name("LEFT"))
            if idx >= 0:
                self._align.setCurrentIndex(idx)
            self._view_selector.select_all()

    @contextmanager
    def _populating_context(self):
        """Context manager to suppress change handling during form population."""
        old = self._populating
        self._populating = True
        try:
            yield
        finally:
            self._populating = old

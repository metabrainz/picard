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
from dataclasses import (
    dataclass,
    replace,
)

from PyQt6 import (  # type: ignore[unresolved-import]
    QtCore,
    QtWidgets,
)

from picard.i18n import gettext as _

from picard.ui import PicardDialog
from picard.ui.itemviews.custom_columns.column_controller import (
    ColumnController,
    analyze_first_invalid,
)
from picard.ui.itemviews.custom_columns.column_form_handler import ColumnFormHandler
from picard.ui.itemviews.custom_columns.column_spec_service import ColumnSpecService
from picard.ui.itemviews.custom_columns.shared import (
    COLUMN_INPUT_FIELD_NAMES,
    DEFAULT_NEW_COLUMN_NAME,
    ColumnIndex,
    get_align_options,
    get_sorting_adapter_options,
)
from picard.ui.itemviews.custom_columns.spec_list_model import SpecListModel
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnSpec,
    load_specs_from_config,
)
from picard.ui.itemviews.custom_columns.user_dialog_service import UserDialogService
from picard.ui.itemviews.custom_columns.validation import ColumnSpecValidator
from picard.ui.itemviews.custom_columns.view_selector import ViewSelector
from picard.ui.itemviews.events import header_events
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
    STYLESHEET_ERROR: str = "QLabel { color : red; }"


def broadcast_headers_updated() -> None:
    """Broadcast a refresh request to all views."""
    header_events.headers_updated.emit()


class CustomColumnsManagerDialog(PicardDialog):
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
        self._spec_service = ColumnSpecService()
        self._spec_controller = ColumnController(
            self._spec_service,
            ColumnSpecValidator(),
        )

        # Left: list + controls (Duplicate/Delete)
        self._list = QtWidgets.QListView(self)
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self._model = SpecListModel(load_specs_from_config(), parent=self)
        self._list.setModel(self._model)
        self._btn_add = QtWidgets.QPushButton(_("New"), self)
        self._btn_add.clicked.connect(self._on_add)
        self._btn_duplicate = QtWidgets.QPushButton(_("Duplicate"), self)
        self._btn_delete = QtWidgets.QPushButton(_("Delete"), self)
        # Initially disable Duplicate and Delete buttons until an item is selected
        self._btn_duplicate.setEnabled(False)
        self._btn_delete.setEnabled(False)
        self._btn_duplicate.clicked.connect(self._on_duplicate)
        self._btn_delete.clicked.connect(self._on_delete)
        left_panel = QtWidgets.QWidget(self)
        left_v = QtWidgets.QVBoxLayout(left_panel)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.addWidget(self._list)
        left_buttons = QtWidgets.QHBoxLayout()
        left_buttons.addWidget(self._btn_add)
        left_buttons.addWidget(self._btn_duplicate)
        left_buttons.addWidget(self._btn_delete)
        left_v.addLayout(left_buttons)

        # Middle: editor
        self._editor_panel = QtWidgets.QWidget(self)
        form = QtWidgets.QFormLayout(self._editor_panel)

        self._title = QtWidgets.QLineEdit(self._editor_panel)
        # Set "New Custom Column" as ALWAYS the placeholder
        self._title.setPlaceholderText(DEFAULT_NEW_COLUMN_NAME)
        self._expression = ScriptTextEdit(self._editor_panel)
        self._expression.setPlaceholderText("%artist% - %title%")
        self._width = QtWidgets.QSpinBox(self._editor_panel)
        self._width.setRange(DialogConfig.MIN_WIDTH, DialogConfig.MAX_WIDTH)
        self._width.setSpecialValueText("")
        self._width.setValue(DialogConfig.DEFAULT_WIDTH)
        self._width.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self._width.setMaximumWidth(100)
        self._width.setSuffix(_(' px'))
        self._align = QtWidgets.QComboBox(self._editor_panel)
        for label, enum_val in get_align_options():
            self._align.addItem(_(label), enum_val)
        self._align.setMaximumWidth(100)

        # Sorting adapter dropdown
        self._sorting_adapter = QtWidgets.QComboBox(self._editor_panel)
        for i, (class_name, display_info) in enumerate(get_sorting_adapter_options()):
            self._sorting_adapter.addItem(_(display_info.display_name), class_name)
            self._sorting_adapter.setItemData(i, _(display_info.tooltip), QtCore.Qt.ItemDataRole.ToolTipRole)
        self._sorting_adapter.setMaximumWidth(200)

        self._view_selector = ViewSelector(self._editor_panel)
        self._form_handler = ColumnFormHandler(
            self._title,
            self._expression,
            self._width,
            self._align,
            self._view_selector,
            self._sorting_adapter,
        )

        form.addRow(_(COLUMN_INPUT_FIELD_NAMES[ColumnIndex.TITLE]) + "*", self._title)
        form.addRow(_(COLUMN_INPUT_FIELD_NAMES[ColumnIndex.EXPRESSION]) + "*", self._expression)
        form.addRow(_(COLUMN_INPUT_FIELD_NAMES[ColumnIndex.WIDTH]), self._width)
        form.addRow(_(COLUMN_INPUT_FIELD_NAMES[ColumnIndex.ALIGN]), self._align)
        form.addRow(_("Sorting"), self._sorting_adapter)
        form.addRow(_("Add to views"), self._view_selector)

        # Display an error message to the user
        self._error_message_display = QtWidgets.QLabel(self._editor_panel)
        self._error_message_display.setStyleSheet(DialogConfig.STYLESHEET_ERROR)
        self._error_message_display.setWordWrap(True)
        self._error_message_display.setText("")

        form.addRow(self._error_message_display)

        # Right: docs
        self._docs = ScriptingDocumentationWidget(include_link=True, parent=self)

        # Splitter
        self._splitter = QtWidgets.QSplitter(self)
        self._splitter.setObjectName('column_manager_splitter')
        self._splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self._splitter.addWidget(left_panel)
        self._splitter.addWidget(self._editor_panel)
        self._splitter.addWidget(self._docs)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 2)
        self._splitter.setStretchFactor(2, 2)

        # Buttons (OK/Cancel only in dialog button box)
        self._buttonbox = QtWidgets.QDialogButtonBox(self)
        self._btn_apply = self._buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self._buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Help)

        self._buttonbox.accepted.connect(self.accept)
        self._buttonbox.rejected.connect(self.reject)
        self._buttonbox.helpRequested.connect(self.help_requested)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._splitter)
        layout.addWidget(self._buttonbox)

        self.resize(DialogConfig.DIALOG_WIDTH, DialogConfig.DIALOG_HEIGHT)
        self._dirty = False
        self._deleted_keys: set[str] = set()
        self._populating: bool = False
        self._deleting: bool = False
        self._current_row: int = -1
        self._awaiting_update: bool = False
        self._has_uncommitted_changes: bool = False
        self._update_apply()

        # Selection and bindings
        sel = self._list.selectionModel()
        sel.selectionChanged.connect(self._on_selection_changed)
        self._title.textChanged.connect(self._on_form_changed)
        self._expression.textChanged.connect(self._on_form_changed)
        self._width.valueChanged.connect(self._on_form_changed)
        self._align.currentIndexChanged.connect(self._on_form_changed)
        self._sorting_adapter.currentIndexChanged.connect(self._on_form_changed)
        self._view_selector.changed.connect(self._on_form_changed)

        # Dialog service to keep manager dialog thin
        self._user_dialog_service = UserDialogService(self)

        # If no columns exist yet, keep Add enabled but form DISABLED
        if self._model.rowCount() > 0:
            self._list.setCurrentIndex(self._model.index(0))
        else:
            # Disable form initially; user must click Add first
            self._prepare_editor_for_new_entry(enable_form=False)
            self._awaiting_update = False  # Don't await update initially
        self._update_form_actions()

    # --- Actions
    def accept(self) -> None:
        """Apply changes and close the dialog with acceptance."""
        # Check for uncommitted changes and ask user what to do
        if self._has_uncommitted_changes:
            reply = self._user_dialog_service.ask_unsaved_changes(
                _("You have unsaved changes. Do you want to save them?")
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return  # Don't close dialog
            elif reply == QtWidgets.QMessageBox.StandardButton.Save:
                # Try to save changes first
                self._on_update()
                # If update failed (validation error), don't close
                if self._has_uncommitted_changes:
                    return
            # If reply is Discard, just continue without committing

        # Apply changes and check if successful
        if not self._on_apply():
            return  # Don't close dialog if apply failed

        self._has_uncommitted_changes = False
        super().accept()

    def reject(self) -> None:
        """Close the dialog discarding unsaved changes."""
        self._dirty = False
        super().reject()

    def help_requested(self) -> None:
        """Show help for custom columns."""
        self.show_help('/usage/custom_columns.html')

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

    def _selected_rows(self) -> list[int]:
        """Return all currently selected row indices sorted ascending.

        Returns
        -------
        list[int]
            Sorted list of selected row indices.
        """
        return sorted({idx.row() for idx in self._list.selectionModel().selectedIndexes()})

    def _live_spec_check(self) -> None:
        """Handle changes in the expression field to provide live validation feedback."""
        if self._populating:
            return

        expression = self._expression.toPlainText()
        if not expression.strip():
            self._error_message_display.setText("")
            return

        # Get the curernt spec from the form to validate
        spec = self._spec_from_form()

        existing_keys = {s.key for s in self._model.specs() if s.key} - {spec.key}
        report = self._spec_controller.validate_single(spec, existing_keys)
        if report.is_valid:
            self._error_message_display.setText("")
        else:
            error_messages = [_(result.message) for result in report.errors]
            self._error_message_display.setText("\n".join(error_messages))

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

        # Check for uncommitted changes before changing selection
        if not self._populating:
            allowed = self._user_dialog_service.can_change_selection(self._has_uncommitted_changes)
            if not allowed:
                # User cancelled, revert selection
                self._revert_selection()
                return

        # If we were in new-entry mode, cancel it and proceed with the new selection
        if self._awaiting_update:
            self._awaiting_update = False

        # Only commit if there are no uncommitted changes (normal case)
        # If there were uncommitted changes and user chose to discard, skip commit
        if not self._has_uncommitted_changes:
            self._commit_form_to_model()

        selected_rows = self._selected_rows()

        if len(selected_rows) == 1:
            self._current_row = selected_rows[0]
            spec = self._model.spec_at(self._current_row) if self._current_row >= 0 else None
            self._populate_form(spec)
        else:
            # Disable editor when multiple or none are selected
            self._current_row = -1
            with self._populating_context():
                self._form_handler.set_enabled(False)
        self._has_uncommitted_changes = False
        self._update_form_actions()

    def _populate_form(self, spec: CustomColumnSpec | None) -> None:
        """Populate the editor form with the given specification.

        Parameters
        ----------
        spec : CustomColumnSpec | None
            Specification to populate, or None to clear for new entry.
        """
        with self._populating_context():
            if spec is None:
                self._form_handler.clear_for_new(DialogConfig.DEFAULT_WIDTH)
            else:
                self._form_handler.populate(spec)
        # Reset uncommitted changes flag after populating form
        self._has_uncommitted_changes = False

    def _on_form_changed(self, *args) -> None:  # type: ignore[no-untyped-def]
        """Handle form changes by automatically updating the selected row."""
        if self._populating:
            return
        self._has_uncommitted_changes = True
        self._live_spec_check()

        # Stage the changes automatically (but not persist them)
        # Persistence is handled by the Apply button (Make It So!)
        self._on_update()

    def _spec_from_form(self) -> CustomColumnSpec:
        """Create a CustomColumnSpec from current form widget values."""
        spec = self._form_handler.read_spec(CustomColumnKind.SCRIPT)
        if 0 <= self._current_row < self._model.rowCount():
            existing = self._model.spec_at(self._current_row)
            spec = replace(spec, key=existing.key)
        else:
            spec = replace(spec, key=self._spec_service.allocate_new_key())
        return spec

    def _collect_form(self) -> CustomColumnSpec | None:
        """Collect editor form values into a `CustomColumnSpec`.

        Returns
        -------
        CustomColumnSpec | None
            The collected spec if editing an existing row; otherwise None.
        """
        if self._current_row < 0:
            return None
        return self._spec_from_form()

    def _commit_form_to_model(self) -> None:
        """Commit current editor values to the selected model row if valid."""
        # Only commit when editing a valid, existing row
        # Don't commit during deletion operations to prevent stale form data corruption
        if self._populating or self._deleting:
            return

        # Always sync _current_row with actual selection before commit
        current_row = self._selected_row()
        if current_row < 0 or current_row >= self._model.rowCount():
            return

        new_spec = self._collect_form()
        if new_spec is None:
            return

        old = self._model.spec_at(current_row)

        # Sanity check - if form data doesn't match the current row, don't commit
        if old and new_spec and old.title != new_spec.title:
            # Re-populate form with correct data instead of committing wrong data
            self._populate_form(old)
            self._has_uncommitted_changes = False
            return

        if new_spec.key and old.key and new_spec.key != old.key:
            self._deleted_keys.add(old.key)

        self._model.update_spec(current_row, new_spec)

    def _on_add(self) -> None:
        """Create a new placeholder specification and insert it into the model."""
        # Check for uncommitted changes before starting new entry
        if not self._user_dialog_service.can_change_selection(self._has_uncommitted_changes):
            return  # User cancelled, don't start new entry

        # Create a placeholder specification with blank expression
        # Pass current specs to ensure unique title generation
        current_specs = self._model.specs()
        placeholder_spec = ColumnSpecService.create_placeholder_spec(DialogConfig.DEFAULT_WIDTH, current_specs)

        # Insert the placeholder spec into the model
        new_row = self._model.insert_spec(placeholder_spec)
        self._list.setCurrentIndex(self._model.index(new_row))

        # Explicitly populate the form with the new placeholder spec
        self._current_row = new_row
        self._populate_form(placeholder_spec)
        self._has_uncommitted_changes = False
        self._mark_dirty()
        # Focus title input for immediate editing
        self._title.setFocus()

    def _on_duplicate(self) -> None:
        """Duplicate the selected specification with an auto-incremented title."""
        row = self._selected_row()
        if row < 0:
            return
        spec = self._model.spec_at(row)
        dup = self._spec_service.duplicate_with_new_title_and_key(spec, self._model.specs())
        new_row = self._model.insert_spec(dup)
        self._list.setCurrentIndex(self._model.index(new_row))
        self._has_uncommitted_changes = False
        self._mark_dirty()

    def _on_delete(self) -> None:
        """Delete the selected specification(s) after confirmation."""
        rows = self._selected_rows()
        if not rows:
            return

        # Check for uncommitted changes first
        if self._has_uncommitted_changes:
            reply = self._user_dialog_service.ask_unsaved_changes(
                _("You have unsaved changes. Do you want to save them before deleting this column?")
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return  # User cancelled
            elif reply == QtWidgets.QMessageBox.StandardButton.Save:
                # Try to save changes first
                self._on_update()
                # If update failed (validation error), don't proceed with delete
                if self._has_uncommitted_changes:
                    return

        if len(rows) == 1:
            spec = self._model.spec_at(rows[0])
            confirmed = self._user_dialog_service.confirm_delete_column(spec.title)
        else:
            confirmed = self._user_dialog_service.confirm_delete_columns(len(rows))

        if not confirmed:
            return

        # Set deleting flag to prevent form commits during selection changes
        self._deleting = True
        try:
            # Track deleted keys
            for r in rows:
                spec = self._model.spec_at(r)
                self._deleted_keys.add(spec.key)

            # Remove rows (model handles ordering)
            if len(rows) == 1:
                self._model.remove_row(rows[0])
            else:
                # Batch remove
                try:
                    self._model.remove_rows(rows)
                except AttributeError:
                    # Fallback if running against older model without remove_rows
                    for r in sorted(rows, reverse=True):
                        self._model.remove_row(r)

            # Update selection to a valid row and clear editor if none
            count = self._model.rowCount()
            if count > 0:
                new_row = min(rows[0], count - 1)
                self._list.setCurrentIndex(self._model.index(new_row))
            else:
                self._list.clearSelection()
                self._prepare_editor_for_new_entry(enable_form=False)
            self._mark_dirty()

            # Deleting cancels pending add state and clears uncommitted changes
            self._awaiting_update = False
            self._has_uncommitted_changes = False
            self._update_form_actions()
        finally:
            # Always clear the deleting flag
            self._deleting = False

            # Force update current_row and form refresh to prevent stale data commits
            self._current_row = self._selected_row()

            if self._current_row >= 0:
                spec = self._model.spec_at(self._current_row)
                self._populate_form(spec)
                # Ensure no uncommitted changes after refresh
                self._has_uncommitted_changes = False

    def _on_apply(self) -> bool:
        """Validate, persist, and register custom column specifications."""
        # Only commit if there are no uncommitted changes (normal case)
        if not self._has_uncommitted_changes:
            self._commit_form_to_model()

        # Validate specs before persisting
        all_specs = self._model.specs()
        reports = self._spec_controller.validate_specs(all_specs)

        # Auto-fix KeyRequiredRule errors by assigning new keys silently
        has_key_errors = any(
            any(r.code in {"KEY_REQUIRED", "KEY_DUPLICATE"} for r in rep.errors) for rep in reports.values()
        )
        if has_key_errors:
            self._spec_service.ensure_unique_nonempty_keys_in_model(self._model)
            # Recompute after fixing keys
            all_specs = self._model.specs()
            reports = self._spec_controller.validate_specs(all_specs)

        analysis = analyze_first_invalid(reports)
        if analysis is not None:
            # Locate the spec and select it to give user context
            spec_title: str | None = None
            for idx, spec in enumerate(all_specs):
                spec_key = spec.key or f"<unnamed:{id(spec)}>"
                if spec_key == analysis.key:
                    spec_title = spec.title if spec.title and spec.title.strip() else None
                    self._list.setCurrentIndex(self._model.index(idx))
                    break

            proceed, focus_field = self._user_dialog_service.handle_apply_validation(analysis, spec_title)
            if not proceed:
                if focus_field == "title":
                    self._title.setFocus()
                elif focus_field == "expression":
                    self._expression.setFocus()
                return False

        # Unregister any columns explicitly deleted during this session

        if self._deleted_keys:
            self._spec_service.unregister_keys(self._deleted_keys)
            self._deleted_keys.clear()

        # Apply changes via controller (deduplicate, persist, register)
        self._spec_controller.apply_all(self._model)

        # Deduplication and persistence are handled by controller
        self._dirty = False
        self._update_apply()
        broadcast_headers_updated()
        return True

    # New helper to enable and clear editor for quick new entry
    def _prepare_editor_for_new_entry(self, enable_form: bool = True) -> None:
        """Prepare the editor for quickly adding a new entry."""
        self._current_row = -1
        with self._populating_context():
            if enable_form:
                self._form_handler.clear_for_new(DialogConfig.DEFAULT_WIDTH)
            else:
                # Clear form but keep it disabled
                self._form_handler.clear_for_new(DialogConfig.DEFAULT_WIDTH)
                self._form_handler.set_enabled(False)
        self._has_uncommitted_changes = False
        self._update_form_actions()

    def _update_apply(self) -> None:
        """Update the Apply button state based on dirty state."""
        self._btn_apply.setEnabled(self._dirty)

    def _mark_dirty(self) -> None:
        """Mark the dialog state as modified and update Apply button."""
        self._dirty = True
        self._update_apply()

    def _update_form_actions(self) -> None:
        """Update the form actions based on the current row and state."""
        sel_count = len(self._list.selectionModel().selectedIndexes()) if self._list.selectionModel() else 0
        has_any_selection = sel_count >= 1
        has_single_selection = sel_count == 1 and self._current_row >= 0
        # Add is disabled when multiple selected or awaiting update
        self._btn_add.setEnabled((not self._awaiting_update) and (sel_count <= 1))
        # Duplicate only enabled for exactly one selected item
        self._btn_duplicate.setEnabled(has_single_selection)
        # Delete enabled when at least one item is selected
        self._btn_delete.setEnabled(has_any_selection)

    def _revert_selection(self) -> None:
        """Revert selection back to the current row when user cancels selection change."""
        if self._current_row >= 0 and self._current_row < self._model.rowCount():
            # Temporarily disconnect to avoid recursion
            sel = self._list.selectionModel()
            sel.selectionChanged.disconnect(self._on_selection_changed)
            self._list.setCurrentIndex(self._model.index(self._current_row))
            sel.selectionChanged.connect(self._on_selection_changed)
        else:
            # If no valid current row, clear selection
            self._list.clearSelection()

    def _on_update(self) -> None:
        """Save changes to the selected row without persisting."""
        # Two modes: update existing row or insert a new row in new-entry mode
        if self._awaiting_update and self._current_row < 0:
            # Build spec from the form and assign a fresh unique key
            base_spec = self._form_handler.read_spec(CustomColumnKind.SCRIPT)
            new_key = self._spec_service.allocate_new_key()
            spec = replace(base_spec, key=new_key)

            # Insert and select the new row
            new_row = self._model.insert_spec(spec)
            # Set current_row before changing selection to prevent confusion in selection handler
            self._current_row = new_row
            # Clear uncommitted changes flag BEFORE changing selection to prevent warning dialog
            self._has_uncommitted_changes = False
            # Re-enable Add after saving changes if we were awaiting save
            if self._awaiting_update:
                self._awaiting_update = False
            self._list.setCurrentIndex(self._model.index(new_row))
            self._mark_dirty()
            self._update_form_actions()
            return

        if self._current_row < 0 or self._current_row >= self._model.rowCount():
            return
        spec = self._spec_from_form()

        # Update the model without persisting
        self._model.update_spec(self._current_row, spec)
        self._mark_dirty()

        # Clear uncommitted changes flag after successful update
        self._has_uncommitted_changes = False
        # Re-enable Add after saving changes if we were awaiting save
        if self._awaiting_update:
            self._awaiting_update = False
        self._update_form_actions()

    @contextmanager
    def _populating_context(self):
        """Context manager to suppress change handling during form population."""
        old = self._populating
        self._populating = True
        try:
            yield
        finally:
            self._populating = old

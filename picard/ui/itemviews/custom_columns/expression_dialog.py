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

"""Dialog to create or edit a custom column specification.

Supports three modes: Field, Script and Transform. The dialog only collects
data and returns a :class:`CustomColumnSpec` value; it does not perform
registration or persistence (SRP/SOC).
"""

from __future__ import annotations


try:
    from PyQt6 import (
        QtCore,
        QtWidgets,
    )
except ImportError:  # pragma: no cover - allow static analysis without Qt installed
    from typing import Any as _Any

    QtCore = _Any  # type: ignore[assignment]
    QtWidgets = _Any  # type: ignore[assignment]

from picard.i18n import gettext as _

from picard.ui.itemviews.custom_columns.shared import (
    DEFAULT_ADD_TO,
    VIEW_ALBUM,
    VIEW_FILE,
    format_add_to,
    parse_add_to,
)
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnSpec,
    TransformName,
)


class CustomColumnExpressionDialog(QtWidgets.QDialog):
    """Expression editor for a single custom column.

    Parameters
    ----------
    existing_spec
        Optional existing spec to edit; if omitted a new spec is created.
    parent
        Parent widget.
    """

    def __init__(self, existing_spec: CustomColumnSpec | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle(_("Edit Column"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self._existing = existing_spec
        self.result_spec: CustomColumnSpec | None = None

        # Inputs
        self._title = QtWidgets.QLineEdit(self)
        # Optional key field: if left empty we derive from Field Name
        self._key = QtWidgets.QLineEdit(self)
        if hasattr(self._key, 'setPlaceholderText'):
            self._key.setPlaceholderText(_("Auto-derived from Field Name"))
        # Explain behavior: optional, defaulting and update on conflict
        if hasattr(self._key, 'setToolTip'):
            self._key.setToolTip(
                _(
                    "Optional internal identifier. If left empty, a key will be "
                    "derived from the Field Name. If a column with this key already "
                    "exists, it will be updated instead of duplicated."
                )
            )
        if hasattr(self._key, 'setWhatsThis'):
            self._key.setWhatsThis(
                _(
                    "Optional internal identifier used to uniquely reference this column.\n"
                    "Leave blank to auto-derive from the Field Name. If another column "
                    "with the same key exists, your changes will update that column."
                )
            )
        self._kind = QtWidgets.QComboBox(self)
        self._kind.addItems([CustomColumnKind.SCRIPT.value, CustomColumnKind.FIELD.value])

        self._expression = QtWidgets.QPlainTextEdit(self)
        if hasattr(self._expression, 'setPlaceholderText'):
            self._expression.setPlaceholderText("%artist% - %title%")
        self._width = QtWidgets.QSpinBox(self)
        self._width.setRange(0, 9999)
        self._width.setSpecialValueText("")
        self._width.setValue(100)
        self._align = QtWidgets.QComboBox(self)
        self._align.addItems(["LEFT", "RIGHT"])
        self._always_visible = QtWidgets.QCheckBox(_("Always visible"), self)
        self._always_visible.setChecked(False)
        self._always_visible.setVisible(False)
        self._file_view = QtWidgets.QCheckBox(_("File view"), self)
        self._file_view.setChecked(True)
        self._album_view = QtWidgets.QCheckBox(_("Album view"), self)
        self._album_view.setChecked(True)

        # Transform selection (only visible for Transform kind)
        self._transform_label = QtWidgets.QLabel(_("Transform"), self)
        self._transform = QtWidgets.QComboBox(self)
        self._transform.addItems([t.value for t in TransformName])

        # Buttons
        self._ok = QtWidgets.QPushButton(_("OK"), self)
        self._cancel = QtWidgets.QPushButton(_("Cancel"), self)
        self._ok.clicked.connect(self._accept)
        self._cancel.clicked.connect(self.reject)

        # Layout
        form = QtWidgets.QFormLayout()
        form.addRow(_("Field Name") + "*", self._title)
        form.addRow(_("Key"), self._key)
        form.addRow(_("Type") + "*", self._kind)
        form.addRow(_("Expression") + "*", self._expression)
        # Keep transform widgets hidden and not user-selectable for now
        form.addRow(self._transform_label, self._transform)
        form.addRow(_("Width"), self._width)
        form.addRow(_("Align"), self._align)
        # Always Visible is hidden and defaults to False; preserve value only when populating
        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(self._file_view)
        hl.addWidget(self._album_view)
        form.addRow(_("Add to views"), hl)
        # Removed insert-after placement option per upstream API

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self._ok)
        buttons.addWidget(self._cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self._kind.currentTextChanged.connect(self._on_kind_changed)
        # Initialize visibility state for transform controls
        self._transform_label.setVisible(False)
        self._transform.setVisible(False)
        self._on_kind_changed(self._kind.currentText())

        # Keep key placeholder roughly in sync with title
        self._title.textChanged.connect(self._on_title_changed)

        if existing_spec:
            self._populate(existing_spec)

        self.resize(520, 420)

    # --- Behavior ----------------------------------------------------------
    def _on_kind_changed(self, text: str) -> None:
        is_transform = text == CustomColumnKind.TRANSFORM.value
        # Show transform selector only for Transform kind
        self._transform.setEnabled(is_transform)
        self._transform.setVisible(is_transform)
        self._transform_label.setVisible(is_transform)

    def _populate(self, spec: CustomColumnSpec) -> None:
        self._title.setText(spec.title)
        self._key.setText(spec.key)
        self._kind.setCurrentText(spec.kind.value)
        self._expression.setPlainText(spec.expression)
        if spec.width is not None:
            self._width.setValue(int(spec.width))
        self._align.setCurrentText(spec.align)
        self._always_visible.setChecked(spec.always_visible)
        views = parse_add_to(getattr(spec, 'add_to', DEFAULT_ADD_TO))
        self._file_view.setChecked(VIEW_FILE in views)
        self._album_view.setChecked(VIEW_ALBUM in views)
        if spec.transform:
            self._transform.setCurrentText(spec.transform.value)
        # Update derived key placeholder to reflect current title
        self._on_title_changed(self._title.text())

    def _accept(self) -> None:
        title = self._title.text().strip()
        kind = CustomColumnKind(self._kind.currentText())
        expression = self._expression.toPlainText().strip()
        width = int(self._width.value()) or None
        align = self._align.currentText().strip()
        always_visible = self._always_visible.isChecked()
        file_view = self._file_view.isChecked()
        album_view = self._album_view.isChecked()
        transform = TransformName(self._transform.currentText()) if kind == CustomColumnKind.TRANSFORM else None

        if not title:
            QtWidgets.QMessageBox.warning(self, _("Invalid"), _("Field Name is required."))
            return
        if not expression:
            QtWidgets.QMessageBox.warning(self, _("Invalid"), _("Expression is required."))
            return

        # Use provided key if given; otherwise derive from Field Name
        key_input = self._key.text().strip()
        key = key_input or self._derive_key_from_field_name(title)
        selected = []
        if file_view:
            selected.append(VIEW_FILE)
        if album_view:
            selected.append(VIEW_ALBUM)
        add_to = format_add_to(selected)
        self.result_spec = CustomColumnSpec(
            title=title,
            key=key,
            kind=kind,
            expression=expression,
            width=width,
            align=align,
            always_visible=always_visible,
            add_to=add_to,
            transform=transform,
        )
        self.accept()

    def _on_title_changed(self, text: str) -> None:
        # Update placeholder to show how the key will be derived if left empty
        derived = self._derive_key_from_field_name(text)
        if hasattr(self._key, 'setPlaceholderText'):
            self._key.setPlaceholderText(derived or _("Auto-derived from Field Name"))

    @staticmethod
    def _derive_key_from_field_name(name: str) -> str:
        """Derive an internal key from a user-facing field name.

        Rules
        -----
        - Lowercase
        - Replace spaces with underscores
        - Keep ASCII letters, digits, hyphen and underscore; replace others with underscore
        - Collapse repeated underscores
        """
        import re

        text = name.strip().lower().replace(" ", "_")
        text = re.sub(r"[^a-z0-9_-]", "_", text)
        text = re.sub(r"_+", "_", text)
        return text

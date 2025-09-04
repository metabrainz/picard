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

"""Form handler for custom column creation and editing.

Manages form inputs for custom column specifications including
title, expression, width, alignment, and view selection.
"""

from contextlib import suppress

from PyQt6 import QtWidgets

from picard.ui.itemviews.custom_columns.shared import (
    ALIGN_LEFT_NAME,
    DEFAULT_ADD_TO,
    format_add_to,
    normalize_align_name,
    parse_add_to,
)
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnKind,
    CustomColumnSpec,
)


class ColumnFormHandler:
    """Handler for custom column form inputs.

    Manages form state and data binding between UI inputs and
    CustomColumnSpec objects.
    """

    def __init__(
        self,
        title_input: QtWidgets.QLineEdit,
        expression_input: QtWidgets.QPlainTextEdit,
        width_input: QtWidgets.QSpinBox,
        align_input: QtWidgets.QComboBox,
        view_selector: QtWidgets.QWidget,
        sorting_adapter_input: QtWidgets.QComboBox,
    ):
        """Initialize form handler with UI input widgets.

        Parameters
        ----------
        title_input : QtWidgets.QLineEdit
            Input for column title.
        expression_input : QtWidgets.QPlainTextEdit
            Input for column expression.
        width_input : QtWidgets.QSpinBox
            Input for column width.
        align_input : QtWidgets.QComboBox
            Dropdown for text alignment.
        view_selector : QtWidgets.QWidget
            Widget for selecting views.
        sorting_adapter_input : QtWidgets.QComboBox
            Dropdown for selecting sorting adapter.
        """
        self._title_input = title_input
        self._expression_input = expression_input
        self._width_input = width_input
        self._align_input = align_input
        self._view_selector = view_selector
        self._sorting_adapter_input = sorting_adapter_input

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all form inputs."""
        for w in (
            self._title_input,
            self._expression_input,
            self._width_input,
            self._align_input,
            self._view_selector,
            self._sorting_adapter_input,
        ):
            w.setEnabled(enabled)

    def populate(self, spec: CustomColumnSpec | None) -> None:
        """Populate form with existing specification data.

        Parameters
        ----------
        spec : CustomColumnSpec | None
            Specification to populate, or None to clear form.
        """
        if not spec:
            self.set_enabled(False)
            self._title_input.clear()
            self._expression_input.setPlainText("")
            self._width_input.setValue(0)
            idx = self._align_input.findData(normalize_align_name(ALIGN_LEFT_NAME))
            if idx >= 0:
                self._align_input.setCurrentIndex(idx)

            # Reset sorting adapter to default (first item)
            self._sorting_adapter_input.setCurrentIndex(0)

            # Select all views by default
            with suppress(AttributeError):
                self._view_selector.select_all()
            return

        self.set_enabled(True)
        self._title_input.setText(spec.title)
        self._expression_input.setPlainText(spec.expression)
        self._width_input.setValue(int(spec.width) if spec.width is not None else 0)
        idx = self._align_input.findData(normalize_align_name(spec.align))
        if idx >= 0:
            self._align_input.setCurrentIndex(idx)

        # Set sorting adapter
        sorting_adapter = getattr(spec, 'sorting_adapter', '')
        adapter_idx = self._sorting_adapter_input.findData(sorting_adapter)
        if adapter_idx >= 0:
            self._sorting_adapter_input.setCurrentIndex(adapter_idx)
        else:
            self._sorting_adapter_input.setCurrentIndex(0)  # Default to first item

        views = parse_add_to(getattr(spec, 'add_to', DEFAULT_ADD_TO))
        with suppress(AttributeError):
            self._view_selector.set_selected(set(views))

    def clear_for_new(self, default_width: int) -> None:
        """Clear form for new column creation.

        Parameters
        ----------
        default_width : int
            Default width value to set for the new column.
        """
        self.set_enabled(True)
        self._title_input.clear()
        self._expression_input.setPlainText("")
        self._width_input.setValue(default_width)
        idx = self._align_input.findData(normalize_align_name(ALIGN_LEFT_NAME))
        if idx >= 0:
            self._align_input.setCurrentIndex(idx)

        # Reset sorting adapter to default (first item)
        self._sorting_adapter_input.setCurrentIndex(0)

        # Select all views by default
        with suppress(AttributeError):
            self._view_selector.select_all()

    def read_spec(self, kind: CustomColumnKind = CustomColumnKind.SCRIPT) -> CustomColumnSpec:
        """Read current form values into a CustomColumnSpec.

        Parameters
        ----------
        kind : CustomColumnKind, optional
            Type of custom column, by default CustomColumnKind.SCRIPT.

        Returns
        -------
        CustomColumnSpec
            Specification object with current form values.
        """
        title = self._title_input.text().strip()
        expr = self._expression_input.toPlainText().strip()
        width = int(self._width_input.value()) or None
        align: str = normalize_align_name(self._align_input.currentData()).name
        sorting_adapter = self._sorting_adapter_input.currentData() or ""

        try:
            selected_views: tuple[str, ...] = self._view_selector.get_selected()
        except AttributeError:
            selected_views = tuple(DEFAULT_ADD_TO.split(","))
        add_to = format_add_to(selected_views)

        return CustomColumnSpec(
            title=title,
            key="",  # Key assigned by dialog/controller
            kind=kind,
            expression=expr,
            width=width,
            align=align,
            always_visible=False,
            add_to=add_to,
            sorting_adapter=sorting_adapter,
        )

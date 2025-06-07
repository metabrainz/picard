# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Francisco Lisboa
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

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.i18n import (
    N_,
    gettext as _,
)
from picard.tags import (
    ALL_TAGS,
    filterable_tag_names,
)


class Filter(QtWidgets.QWidget):

    filterChanged = QtCore.pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.default_filter_button_label = N_("Filters")

        # filter button
        self.filter_button = QtWidgets.QPushButton(self.default_filter_button_label, self)
        self.filter_button.setMaximumWidth(120)
        self.filter_button.clicked.connect(self._show_filter_dialog)
        layout.addWidget(self.filter_button)

        self.filterable_tags = self.get_filterable_tags()
        self.selected_filters = []  # Start with no filters selected

        # filter input
        self.filter_query_box = QtWidgets.QLineEdit(self)
        self.filter_query_box.setPlaceholderText(_("Type to filter..."))
        self.filter_query_box.setClearButtonEnabled(True)
        self.filter_query_box.textChanged.connect(self._query_changed)
        layout.addWidget(self.filter_query_box)

    def _show_filter_dialog(self):
        """Show dialog to select multiple filters"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(_("Select Filters"))
        dialog.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Scroll area for tags
        scroll = QtWidgets.QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget(scroll)
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        checkboxes = {}

        # Add checkboxes for all tags
        for tag in sorted(self.filterable_tags, key=lambda t: ALL_TAGS.display_name(t).lower()):
            checkbox = QtWidgets.QCheckBox(ALL_TAGS.display_name(str(tag)), scroll_content)
            checkbox.setChecked(str(tag) in self.selected_filters)
            scroll_layout.addWidget(checkbox)
            checkboxes[str(tag)] = checkbox

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog and process result
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.selected_filters = []
            for tag, checkbox in checkboxes.items():
                if checkbox.isChecked():
                    self.selected_filters.append(tag)

            if not self.selected_filters:
                self.selected_filters = []

            # Update button text
            self.set_filter_button_label(self.make_button_text(self.selected_filters))

            self._query_changed(self.filter_query_box.text())

    @classmethod
    def get_filterable_tags(cls) -> set:
        return set(filterable_tag_names())

    @classmethod
    def make_button_text(cls, selected_filters):
        if not selected_filters:
            return None

        if len(selected_filters) == 1:
            return _(ALL_TAGS.display_name(selected_filters[0]))

        return _("{num} filters").format(num=len(selected_filters))

    def set_filter_button_label(self, label=None):
        if label is None:
            label = _(self.default_filter_button_label)
        self.filter_button.setText(label)

    def _query_changed(self, text):
        self.filterChanged.emit(text, self.selected_filters)

    def clear(self):
        self.filter_query_box.clear()
        self.selected_filters = []
        self.set_filter_button_label()

    def set_focus(self):
        self.filter_query_box.setFocus()

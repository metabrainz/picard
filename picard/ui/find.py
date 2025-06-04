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

from picard.tags import preserved_tag_names


class FindBox(QtWidgets.QWidget):
    findChanged = QtCore.pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # find icon
        self.find_icon = QtWidgets.QLabel()
        find_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView)
        self.find_icon.setPixmap(find_icon.pixmap(16, 16))
        layout.addWidget(self.find_icon)

        self.filter_button = QtWidgets.QPushButton("Filters", self)
        self.filter_button.setMaximumWidth(120)
        self.filter_button.clicked.connect(self._show_filter_dialog)
        layout.addWidget(self.filter_button)

        self.valid_tags = set(preserved_tag_names())
        self.selected_filters = []  # Start with "All" selected

        # find input
        self.find_query_box = QtWidgets.QLineEdit(self)
        self.find_query_box.setPlaceholderText("Find")
        self.find_query_box.setClearButtonEnabled(True)
        self.find_query_box.textChanged.connect(self._query_changed)
        layout.addWidget(self.find_query_box)

    def _show_filter_dialog(self):
        """Show dialog to select multiple filters"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Select Filters")
        dialog.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Scroll area for tags
        scroll = QtWidgets.QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget(scroll)
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        label = QtWidgets.QLabel("File Filters", scroll_content)
        scroll_layout.addWidget(label)

        # Add a horizontal separator
        line = QtWidgets.QFrame(scroll_content)
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)

        checkboxes = {}
        for file_filter in ["filename", "filepath"]:
            checkbox = QtWidgets.QCheckBox(file_filter, scroll_content)
            checkbox.setChecked(file_filter in self.selected_filters)
            scroll_layout.addWidget(checkbox)
            checkboxes[file_filter] = checkbox

        scroll_layout.addItem(QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        label = QtWidgets.QLabel("Tag Filters", scroll_content)
        scroll_layout.addWidget(label)

        # Add a horizontal separator
        line = QtWidgets.QFrame(scroll_content)
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)

        # Add checkboxes for all tags
        for tag in sorted(self.valid_tags):
            checkbox = QtWidgets.QCheckBox(tag, scroll_content)
            checkbox.setChecked(tag in self.selected_filters)
            scroll_layout.addWidget(checkbox)
            checkboxes[tag] = checkbox

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

            # Update button text
            if not self.selected_filters or self.selected_filters == []:
                self.selected_filters = []
                self.filter_button.setText("Filters")

            elif len(self.selected_filters) <= 2:
                self.filter_button.setText(", ".join(self.selected_filters))
            else:
                self.filter_button.setText(f"{len(self.selected_filters)} filters")

            # Update find with new filters
            self._query_changed(self.find_query_box.text())

    def _query_changed(self, text):
        self.findChanged.emit(text, self.selected_filters)

    def clear(self):
        self.find_query_box.clear()
        self.selected_filters = []
        self.filter_button.setText("Filters")

    def set_focus(self):
        self.find_query_box.setFocus()

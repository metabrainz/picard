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


class FindBox(QtWidgets.QWidget):

    findChanged = QtCore.pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.default_filter_button_label = N_("Filters")

        # find icon
        self.find_icon = QtWidgets.QLabel()
        find_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView)
        self.find_icon.setPixmap(find_icon.pixmap(16, 16))
        layout.addWidget(self.find_icon)

        self.filter_button = QtWidgets.QPushButton(_("Filters"), self)
        self.filter_button.setMaximumWidth(120)
        self.filter_button.clicked.connect(self._show_filter_dialog)
        layout.addWidget(self.filter_button)

        self.filterable_tags = self.get_filterable_tags()
        self.selected_filters = []  # Start with no filters selected

        # find input
        self.find_query_box = QtWidgets.QLineEdit(self)
        self.find_query_box.setPlaceholderText(_("Find"))
        self.find_query_box.setClearButtonEnabled(True)
        self.find_query_box.textChanged.connect(self._query_changed)
        layout.addWidget(self.find_query_box)

    file_filters = {
        'filename': N_("Filename"),
        'filepath': N_("Filepath"),
    }

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

        label = QtWidgets.QLabel(_("File Filters"), scroll_content)
        scroll_layout.addWidget(label)

        # Add a horizontal separator
        line = QtWidgets.QFrame(scroll_content)
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)

        checkboxes = {}
        for file_filter in ["filename", "filepath"]:
            checkbox = QtWidgets.QCheckBox(_(self.file_filters[file_filter]), scroll_content)
            checkbox.setChecked(file_filter in self.selected_filters)
            scroll_layout.addWidget(checkbox)
            checkboxes[file_filter] = checkbox

        scroll_layout.addItem(QtWidgets.QSpacerItem(0, 10, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        label = QtWidgets.QLabel(_("Tag Filters"), scroll_content)
        scroll_layout.addWidget(label)

        # Add a horizontal separator
        line = QtWidgets.QFrame(scroll_content)
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        scroll_layout.addWidget(line)

        # Add checkboxes for all tags
        for tag in sorted(self.filterable_tags, key=lambda t: ALL_TAGS.display_name(str(t)).lower()):
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

            self._query_changed(self.find_query_box.text())

    @classmethod
    def get_filterable_tags(cls) -> set:
        return set(filterable_tag_names())

    @classmethod
    def make_button_text(cls, selected_filters):
        if not selected_filters:
            return None

        if len(selected_filters) == 1:
            if selected_filters[0] not in cls.file_filters.keys():
                return ALL_TAGS.display_name(selected_filters[0])
            else:
                return _(cls.file_filters[selected_filters[0]])

        return _("{num} filters").format(num=len(selected_filters))

    def set_filter_button_label(self, label=None):
        if label is None:
            label = _(self.default_filter_button_label)
        self.filter_button.setText(label)

    def _query_changed(self, text):
        self.findChanged.emit(text, self.selected_filters)

    def clear(self):
        self.find_query_box.clear()
        self.selected_filters = []
        self.set_filter_button_label()

    def set_focus(self):
        self.find_query_box.setFocus()

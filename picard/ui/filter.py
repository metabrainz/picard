# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 João Sousa
# Copyright (C) 2025 Francisco Lisboa
# Copyright (C) 2025 Bob Swift
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


# When set to True, this will add a test button and a filter item that is not
# normally used (TEST_TAG) to allow testing of the filterable tags reloading.
# The TEST_TAG item will be toggled from the filterable items dialog when the
# test button is clicked.
TEST_RELOAD_FILTERABLE_TAGS = True
TEST_TAG = '~filesize'


class Filter(QtWidgets.QWidget):

    filterChanged = QtCore.pyqtSignal(str, list)
    filterable_tags = set()
    instances = set()

    def __init__(self, parent=None):
        super().__init__(parent)
        Filter.instances.add(self)
        self.initializing = True
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.default_filter_button_label = N_("Filters")

        # filter button
        self.filter_button = QtWidgets.QPushButton(self.default_filter_button_label, self)
        self.filter_button.setMaximumWidth(120)
        self.filter_button.clicked.connect(self._show_filter_dialog)
        layout.addWidget(self.filter_button)

        self.selected_filters = []  # Start with no filters selected
        self.load_filterable_tags()
        if TEST_RELOAD_FILTERABLE_TAGS:
            Filter.filterable_tags.add('~filesize')
            self.checkboxes = {}
        self.filter_dialog = self._build_filter_dialog()

        # filter input
        self.filter_query_box = QtWidgets.QLineEdit(self)
        self.filter_query_box.setPlaceholderText(_("Type to filter..."))
        self.filter_query_box.setClearButtonEnabled(True)
        self.filter_query_box.textChanged.connect(self._query_changed)
        layout.addWidget(self.filter_query_box)

        if TEST_RELOAD_FILTERABLE_TAGS:
            # test button
            self.test_button = QtWidgets.QPushButton('Testing On', self)
            self.test_button.setMaximumWidth(120)
            self.test_button.clicked.connect(self.test_tag_reload)
            layout.addWidget(self.test_button)

        self.initializing = False

    def __del__(self):
        Filter.instances.discard(self)

    def _build_filter_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(_("Select Filters"))
        dialog.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Scroll area for tags
        scroll = QtWidgets.QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget(scroll)
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        self.checkboxes = {}

        # Add checkboxes for all tags
        for tag in sorted(Filter.filterable_tags, key=lambda t: ALL_TAGS.display_name(t).lower()):
            checkbox = QtWidgets.QCheckBox(ALL_TAGS.display_name(str(tag)), scroll_content)
            checkbox.setChecked(str(tag) in self.selected_filters)
            checkbox.setToolTip(ALL_TAGS.display_tooltip(tag))
            scroll_layout.addWidget(checkbox)
            self.checkboxes[str(tag)] = checkbox

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        return dialog

    def _show_filter_dialog(self):
        """Show dialog to select multiple filters"""
        # Show dialog and process result
        if self.filter_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.selected_filters = []
            for tag, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    self.selected_filters.append(tag)

            # Update button text
            self.set_filter_button_label(self.make_button_text(self.selected_filters))

            self._query_changed(self.filter_query_box.text())

    def test_tag_reload(self):
        # Used for testing of the filterable tags reloading.
        new_state = 'Off' if TEST_TAG in Filter.filterable_tags else 'On'
        for item in Filter.instances:
            item.test_button.setText(f'Testing {new_state}')
        if TEST_TAG in Filter.filterable_tags:
            self.load_filterable_tags(force=True)
        else:
            Filter.filterable_tags.add(TEST_TAG)
            for item in Filter.instances:
                item.filterable_tags_updated()

    @classmethod
    def load_filterable_tags(cls, force: bool = False):
        if cls.filterable_tags and not force:
            return
        old_filterable_tags = cls.filterable_tags.copy()
        cls.filterable_tags = set(filterable_tag_names())
        if cls.filterable_tags == old_filterable_tags:
            return
        for item in cls.instances:
            item.filterable_tags_updated()

    def filterable_tags_updated(self):
        if self.initializing:
            return
        self.filter_dialog = self._build_filter_dialog()

        # Check if selected filters were removed and re-apply the filter
        old_filters = set(self.selected_filters)
        temp = old_filters.difference(Filter.filterable_tags)
        if temp:
            new = old_filters - temp
            self.selected_filters = list(new)
            self.set_filter_button_label(self.make_button_text(self.selected_filters))
            self._query_changed(self.filter_query_box.text())

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

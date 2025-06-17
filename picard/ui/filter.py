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

from picard import log
from picard.config import get_config
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.tags import (
    ALL_TAGS,
    filterable_tag_names,
)


class Filter(QtWidgets.QWidget):

    filterChanged = QtCore.pyqtSignal(str, set)
    filterable_tags = set()
    instances = set()
    suspended = False

    def __init__(self, parent=None):
        super().__init__(parent)
        Filter.instances.add(self)
        self.saved_filters_key = f"filters_{type(parent).__name__}"
        self.initializing = True
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.default_filter_button_label = N_("Filters")

        self.load_filterable_tags()
        self.default_filters = set()    # Default to selecting no filters
        self.selected_filters = self._get_saved_selected_filters()

        # filter button
        self.filter_button = QtWidgets.QPushButton(Filter.make_button_text(self.selected_filters), self)
        self.filter_button.setMaximumWidth(120)
        self.filter_button.clicked.connect(self._show_filter_dialog)
        layout.addWidget(self.filter_button)

        self.filter_dialog = self._build_filter_dialog()

        # filter input
        self.filter_query_box = QtWidgets.QLineEdit(self)
        self.filter_query_box.setPlaceholderText(_("Type to filter..."))
        self.filter_query_box.setClearButtonEnabled(True)
        self.filter_query_box.textChanged.connect(self._query_changed)
        layout.addWidget(self.filter_query_box)

        self.initializing = False

    def _get_saved_selected_filters(self):
        config = get_config()
        temp = config.persist[self.saved_filters_key]
        if temp is not None:
            temp = set(temp).intersection(Filter.filterable_tags)
        return temp or self.default_filters.copy()

    def __del__(self):
        Filter.instances.discard(self)

    def _build_filter_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(_("Select Filters"))
        dialog.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(dialog)

        header_layout = QtWidgets.QHBoxLayout()

        # Offset to line up checkbox with checkboxes in scroll area below
        spacer = QtWidgets.QSpacerItem(9, 0, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
        header_layout.addItem(spacer)

        self.check_all_box = QtWidgets.QCheckBox(_('Select / clear all filters'))
        self.check_all_box.setChecked(Filter.filterable_tags == self.selected_filters)
        self.check_all_box.clicked.connect(self._check_all_box_clicked)
        header_layout.addWidget(self.check_all_box)
        layout.addLayout(header_layout)

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

        button_layout = QtWidgets.QHBoxLayout()

        # spacer
        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        button_layout.addItem(spacer)

        # OK
        self.ok_button = QtWidgets.QPushButton(_('OK'))
        ok_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOkButton)
        self.ok_button.setIcon(ok_icon)
        self.ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(self.ok_button)
        self.ok_button.setDefault(True)  # default selected button

        # Cancel
        self.cancel_button = QtWidgets.QPushButton(_('Cancel'))
        cancel_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton)
        self.cancel_button.setIcon(cancel_icon)
        self.cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        return dialog

    def _check_all_box_clicked(self):
        state = self.check_all_box.checkState() == QtCore.Qt.CheckState.Checked
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(state)

    def _uncheck_all_filters(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def _show_filter_dialog(self):
        """Show dialog to select multiple filters"""
        # Show dialog and process result
        if self.filter_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.selected_filters = set()
            for tag, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    self.selected_filters.add(tag)

            # Update persistent list of selected filters
            config = get_config()
            config.persist[self.saved_filters_key] = list(self.selected_filters)

            # Update button text
            self.set_filter_button_label(self.make_button_text(self.selected_filters))

            self._query_changed(self.filter_query_box.text())

        else:
            # Reset any changes to selected filters on dialog cancel
            for tag, checkbox in self.checkboxes.items():
                checkbox.setChecked(tag in self.selected_filters)

        self.check_all_box.setChecked(Filter.filterable_tags == self.selected_filters)

    @classmethod
    def apply_filters(cls):
        if cls.suspended:
            return
        for item in cls.instances:
            item: Filter
            text = item.filter_query_box.text()
            item._query_changed(text)

    @classmethod
    def load_filterable_tags(cls, force: bool = False):
        if cls.filterable_tags and not force:
            return
        old_filterable_tags = cls.filterable_tags.copy()
        cls.filterable_tags = set(filterable_tag_names())
        if cls.filterable_tags == old_filterable_tags:
            return
        log.debug("Loaded filterable tags: %r", cls.filterable_tags)
        for item in cls.instances:
            item.filterable_tags_updated()

    def filterable_tags_updated(self):
        if self.initializing:
            return
        self.filter_dialog = self._build_filter_dialog()

        # Check if selected filters were removed and re-apply the filter
        old_filters = self.selected_filters.copy()
        temp = old_filters.difference(Filter.filterable_tags)
        if temp:
            new = old_filters - temp
            self.selected_filters = new
            self.set_filter_button_label(self.make_button_text(self.selected_filters))
            self._query_changed(self.filter_query_box.text())

    @classmethod
    def make_button_text(cls, selected_filters):
        if not selected_filters:
            return None

        if len(selected_filters) == 1:
            return _(ALL_TAGS.display_name(list(selected_filters)[0]))

        return _("{num} filters").format(num=len(selected_filters))

    def set_filter_button_label(self, label=None):
        if label is None:
            label = _(self.default_filter_button_label)
        self.filter_button.setText(label)

    def _query_changed(self, text):
        self.filterChanged.emit(text, self.selected_filters)

    def clear(self):
        self.filter_query_box.clear()
        self.selected_filters = self._get_saved_selected_filters()
        self.set_filter_button_label(Filter.make_button_text(self.selected_filters))

    def set_focus(self):
        self.filter_query_box.setFocus()

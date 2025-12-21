# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
# Copyright (C) 2025 Philipp Wolfer
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

from PyQt6 import QtWidgets

from picard.i18n import gettext as _
from picard.plugin3.ref_item import RefItem


class RefSelectorWidget(QtWidgets.QWidget):
    """Widget for selecting git refs (tags, branches, or custom input)."""

    def __init__(self, parent=None, include_default=False):
        super().__init__(parent)
        self.include_default = include_default
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        tab_index = 0

        # Default tab (only for install dialog)
        if self.include_default:
            default_widget = QtWidgets.QWidget()
            default_layout = QtWidgets.QVBoxLayout(default_widget)
            self.default_label = QtWidgets.QLabel(_("Use the default ref (usually main/master branch)"))
            default_layout.addWidget(self.default_label)
            self.tab_widget.addTab(default_widget, _("Default"))
            self.default_tab_index = tab_index
            tab_index += 1

        # Tags tab
        self.tags_list = QtWidgets.QListWidget()
        self.tab_widget.addTab(self.tags_list, _("Tags"))
        self.tags_tab_index = tab_index
        tab_index += 1

        # Branches tab
        self.branches_list = QtWidgets.QListWidget()
        self.tab_widget.addTab(self.branches_list, _("Branches"))
        self.branches_tab_index = tab_index
        tab_index += 1

        # Custom tab
        custom_widget = QtWidgets.QWidget()
        custom_layout = QtWidgets.QVBoxLayout(custom_widget)
        custom_layout.addWidget(QtWidgets.QLabel(_("Enter custom ref (tag, branch, or commit):")))
        self.custom_edit = QtWidgets.QLineEdit()
        custom_layout.addWidget(self.custom_edit)
        self.tab_widget.addTab(custom_widget, _("Custom"))
        self.custom_tab_index = tab_index

    def load_refs(self, refs, current_ref=None, plugin_manager=None):
        """Load refs data into the widget."""
        # Clear existing items
        self.tags_list.clear()
        self.branches_list.clear()

        # Populate tags
        for ref in refs.get('tags', []):
            # Create RefItem object for formatting
            ref_item = RefItem(
                shortname=ref['name'],
                ref_type=RefItem.Type.TAG,
                commit=ref.get('commit', ''),
            )
            is_current = current_ref and ref['name'] == current_ref
            list_item = QtWidgets.QListWidgetItem(ref_item.format(is_current=is_current))
            list_item.setData(QtWidgets.QListWidgetItem.ItemType.UserType, ref_item)
            self.tags_list.addItem(list_item)

        # Populate branches
        for ref in refs.get('branches', []):
            # Create RefItem object for formatting
            ref_item = RefItem(
                shortname=ref['name'],
                ref_type=RefItem.Type.BRANCH,
                commit=ref.get('commit', ''),
            )
            is_current = current_ref and ref['name'] == current_ref
            list_item = QtWidgets.QListWidgetItem(ref_item.format(is_current=is_current))
            list_item.setData(QtWidgets.QListWidgetItem.ItemType.UserType, ref_item)
            self.branches_list.addItem(list_item)

    def set_default_ref_info(self, default_ref_name, description):
        """Update the default tab with specific ref information."""
        if self.include_default and hasattr(self, 'default_label') and default_ref_name:
            self.default_label.setText(_("Use default ref: {} ({})").format(default_ref_name, description))

    def get_selected_ref(self):
        """Get the currently selected ref."""
        current_tab = self.tab_widget.currentIndex()

        if self.include_default and current_tab == self.default_tab_index:
            return None
        elif current_tab == self.tags_tab_index:
            current_item = self.tags_list.currentItem()
            return current_item.data(QtWidgets.QListWidgetItem.ItemType.UserType) if current_item else None
        elif current_tab == self.branches_tab_index:
            current_item = self.branches_list.currentItem()
            return current_item.data(QtWidgets.QListWidgetItem.ItemType.UserType) if current_item else None
        elif current_tab == self.custom_tab_index:
            text = self.custom_edit.text().strip()
            return RefItem(shortname=text) if text else None

        return None

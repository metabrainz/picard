# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2022-2023 Philipp Wolfer
# Copyright (C) 2022-2024 Laurent Monin
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


from functools import partial
import uuid

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const.defaults import DEFAULT_PROFILE_NAME
from picard.i18n import (
    gettext as _,
    gettext_constants,
)
from picard.util import unique_numbered_title

from picard.ui import HashableListWidgetItem


class ProfileListWidget(QtWidgets.QListWidget):

    def contextMenuEvent(self, event):
        item = self.itemAt(event.x(), event.y())
        if item:
            menu = QtWidgets.QMenu(self)
            rename_action = QtGui.QAction(_("Rename profile"), self)
            rename_action.triggered.connect(partial(self.editItem, item))
            menu.addAction(rename_action)
            remove_action = QtGui.QAction(_("Remove profile"), self)
            remove_action.triggered.connect(partial(self.remove_profile, item))
            menu.addAction(remove_action)
            menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.StandardKey.Delete):
            self.remove_selected_profile()
        elif event.key() == QtCore.Qt.Key.Key_Insert:
            self.add_profile()
        else:
            super().keyPressEvent(event)

    def unique_profile_name(self, base_name=None):
        if base_name is None:
            base_name = gettext_constants(DEFAULT_PROFILE_NAME)
        existing_titles = [self.item(i).name for i in range(self.count())]
        return unique_numbered_title(base_name, existing_titles)

    def add_profile(self, name=None, profile_id=""):
        if name is None:
            name = self.unique_profile_name()
        list_item = ProfileListWidgetItem(name=name, profile_id=profile_id)
        list_item.setCheckState(QtCore.Qt.CheckState.Checked)
        self.insertItem(0, list_item)
        self.setCurrentItem(list_item, QtCore.QItemSelectionModel.SelectionFlag.Clear
            | QtCore.QItemSelectionModel.SelectionFlag.SelectCurrent)

    def remove_selected_profile(self):
        items = self.selectedItems()
        if items:
            self.remove_profile(items[0])

    def remove_profile(self, item):
        row = self.row(item)
        msg = _("Are you sure you want to remove this profile?")
        reply = QtWidgets.QMessageBox.question(self, _('Confirm Remove'), msg,
            QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if item and reply == QtWidgets.QMessageBox.StandardButton.Yes:
            item = self.takeItem(row)
            del item


class ProfileListWidgetItem(HashableListWidgetItem):
    """Holds a profile's list and text widget properties"""

    def __init__(self, name=None, enabled=True, profile_id=""):
        super().__init__(name)
        self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEditable)
        if name is None:
            name = gettext_constants(DEFAULT_PROFILE_NAME)
        self.setText(name)
        self.setCheckState(QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked)
        if not profile_id:
            profile_id = str(uuid.uuid4())
        self.profile_id = profile_id

    @property
    def pos(self):
        return self.listWidget().row(self)

    @property
    def name(self):
        return self.text()

    @property
    def enabled(self):
        return self.checkState() == QtCore.Qt.CheckState.Checked

    def get_all(self):
        # tuples used to get pickle dump of settings to work
        return (self.pos, self.name, self.enabled, self.profile_id)

    def get_dict(self):
        return {
            'position': self.pos,
            'title': self.name,
            'enabled': self.enabled,
            'id': self.profile_id,
        }

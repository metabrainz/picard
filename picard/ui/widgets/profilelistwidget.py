# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const import (
    DEFAULT_NUMBERED_PROFILE_NAME,
    DEFAULT_PROFILE_NAME,
)

from picard.ui import HashableListWidgetItem


class ProfileListWidget(QtWidgets.QListWidget):

    def contextMenuEvent(self, event):
        item = self.itemAt(event.x(), event.y())
        if item:
            menu = QtWidgets.QMenu(self)
            rename_action = QtWidgets.QAction(_("Rename profile"), self)
            rename_action.triggered.connect(partial(self.editItem, item))
            menu.addAction(rename_action)
            remove_action = QtWidgets.QAction(_("Remove profile"), self)
            remove_action.triggered.connect(partial(self.remove_profile, item))
            menu.addAction(remove_action)
            menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Delete):
            self.remove_selected_profile()
        elif event.key() == QtCore.Qt.Key_Insert:
            self.add_profile()
        else:
            super().keyPressEvent(event)

    def add_profile(self, name=None, profile_id=""):
        if name is None:
            count = self.count()
            name = _(DEFAULT_NUMBERED_PROFILE_NAME) % (count + 1)
        list_item = ProfileListWidgetItem(name=name, profile_id=profile_id)
        list_item.setCheckState(QtCore.Qt.Checked)
        self.insertItem(0, list_item)
        self.setCurrentItem(list_item, QtCore.QItemSelectionModel.Clear
            | QtCore.QItemSelectionModel.SelectCurrent)

    def remove_selected_profile(self):
        items = self.selectedItems()
        if items:
            self.remove_profile(items[0])

    def remove_profile(self, item):
        row = self.row(item)
        msg = _("Are you sure you want to remove this profile?")
        reply = QtWidgets.QMessageBox.question(self, _('Confirm Remove'), msg,
            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if item and reply == QtWidgets.QMessageBox.Yes:
            item = self.takeItem(row)
            del item


class ProfileListWidgetItem(HashableListWidgetItem):
    """Holds a profile's list and text widget properties"""

    def __init__(self, name=None, enabled=True, profile_id=""):
        super().__init__(name)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
        if name is None:
            name = _(DEFAULT_PROFILE_NAME)
        self.setText(name)
        self.setCheckState(QtCore.Qt.Checked if enabled else QtCore.Qt.Unchecked)
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
        return self.checkState() == QtCore.Qt.Checked

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

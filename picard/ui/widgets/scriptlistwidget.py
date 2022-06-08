# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
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
import threading

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.const import DEFAULT_SCRIPT_NAME
from picard.util import unique_numbered_title

from picard.ui import HashableListWidgetItem


class ScriptListWidget(QtWidgets.QListWidget):

    signal_reset_selected_item = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.itemChanged.connect(self.item_changed)
        self.currentItemChanged.connect(self.current_item_changed)
        self.old_row = -1
        self.bad_row = -1

    def contextMenuEvent(self, event):
        item = self.itemAt(event.x(), event.y())
        if item:
            menu = QtWidgets.QMenu(self)
            rename_action = QtWidgets.QAction(_("Rename script"), self)
            rename_action.triggered.connect(partial(self.editItem, item))
            menu.addAction(rename_action)
            remove_action = QtWidgets.QAction(_("Remove script"), self)
            remove_action.triggered.connect(partial(self.remove_script, item))
            menu.addAction(remove_action)
            menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.StandardKey.Delete):
            self.remove_selected_script()
        elif event.key() == QtCore.Qt.Key.Key_Insert:
            self.add_script()
        else:
            super().keyPressEvent(event)

    def unique_script_name(self):
        existing_titles = [self.item(i).name for i in range(self.count())]
        return unique_numbered_title(gettext_constants(DEFAULT_SCRIPT_NAME), existing_titles)

    def add_script(self):
        numbered_name = self.unique_script_name()
        list_item = ScriptListWidgetItem(name=numbered_name)
        list_item.setCheckState(QtCore.Qt.CheckState.Checked)
        self.addItem(list_item)
        self.setCurrentItem(list_item, QtCore.QItemSelectionModel.SelectionFlag.Clear
            | QtCore.QItemSelectionModel.SelectionFlag.SelectCurrent)

    def remove_selected_script(self):
        items = self.selectedItems()
        if items:
            self.remove_script(items[0])

    def remove_script(self, item):
        row = self.row(item)
        msg = _("Are you sure you want to remove this script?")
        reply = QtWidgets.QMessageBox.question(self, _('Confirm Remove'), msg,
            QtWidgets.QMessageBox.StandardButton.Yes, QtWidgets.QMessageBox.StandardButton.No)
        if item and reply == QtWidgets.QMessageBox.StandardButton.Yes:
            item = self.takeItem(row)
            del item

    def item_changed(self, item):
        if not item.name.strip():
            # Replace empty script name with unique numbered name.
            item.setText(self.unique_script_name())

    def current_item_changed(self, new_item, old_item):
        if old_item and old_item.has_error:
            self.bad_row = self.old_row
            # Use a new thread to force the reset of the selected item outside of the current_item_changed event.
            threading.Thread(target=self.signal_reset_selected_item.emit).start()
        else:
            self.old_row = self.currentRow()


class ScriptListWidgetItem(HashableListWidgetItem):
    """Holds a script's list and text widget properties"""

    def __init__(self, name=None, enabled=True, script=""):
        super().__init__(name)
        self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEditable)
        if name is None:
            name = gettext_constants(DEFAULT_SCRIPT_NAME)
        self.setText(name)
        self.setCheckState(QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked)
        self.script = script
        self.has_error = False

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
        return (self.pos, self.name, self.enabled, self.script)

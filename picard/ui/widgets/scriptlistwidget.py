# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.const import DEFAULT_SCRIPT_NAME

from picard.ui import HashableListWidgetItem


class ScriptListWidget(QtWidgets.QListWidget):

    def contextMenuEvent(self, event):
        item = self.itemAt(event.x(), event.y())
        if item:
            menu = QtWidgets.QMenu(self)
            rename_action = QtWidgets.QAction(_("Rename script"), self)
            rename_action.triggered.connect(partial(self.editItem, item))
            menu.addAction(rename_action)
            menu.exec_(event.globalPos())


class ScriptListWidgetItem(HashableListWidgetItem):
    """Holds a script's list and text widget properties"""

    def __init__(self, name=None, enabled=True, script=""):
        super().__init__(name)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable)
        if name is None:
            name = _(DEFAULT_SCRIPT_NAME)
        self.setText(name)
        self.setCheckState(QtCore.Qt.Checked if enabled else QtCore.Qt.Unchecked)
        self.script = script

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
        return (self.pos, self.name, self.enabled, self.script)

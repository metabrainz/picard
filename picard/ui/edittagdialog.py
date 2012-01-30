# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2011 Michael Wiencek
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

from PyQt4 import QtCore, QtGui
from picard.util.tags import TAG_NAMES
from picard.ui.ui_edittagdialog import Ui_EditTagDialog


class EditTagDialog(QtGui.QDialog):

    def __init__(self, window, tag):
        QtGui.QDialog.__init__(self, window)
        self.ui = Ui_EditTagDialog()
        self.ui.setupUi(self)
        self.window = window
        self.value_list = self.ui.value_list
        self.metadata_box = window.metadata_box
        self.tag = tag
        self.modified_tags = {}
        tag_names = self.ui.tag_names
        tag_names.setCompleter(None)
        tag_names.editTextChanged.connect(self.tag_changed)
        self.default_tags = sorted(set(TAG_NAMES.keys() + self.metadata_box.tag_names))
        tag_names.addItem("")
        tag_names.addItems([tn for tn in self.default_tags if not tn.startswith("~")])
        self.tag_changed(tag)
        self.ui.edit_value.clicked.connect(self.edit_value)
        self.ui.add_value.clicked.connect(self.add_value)
        self.ui.remove_value.clicked.connect(self.remove_value)
        self.value_list.itemChanged.connect(self.value_edited)

    def edit_value(self):
        item = self.value_list.currentItem()
        if item:
            self.value_list.editItem(item)

    def add_value(self):
        self._modified_tag().append("")
        item = QtGui.QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        self.value_list.addItem(item)
        self.value_list.editItem(item)

    def remove_value(self):
        value_list = self.value_list
        row = value_list.row(value_list.currentItem())
        value_list.takeItem(row)
        del self._modified_tag()[row]

    def disable_all(self):
        self.value_list.clear()
        self.value_list.setEnabled(False)
        self.ui.edit_value.setEnabled(False)
        self.ui.add_value.setEnabled(False)
        self.ui.remove_value.setEnabled(False)

    def enable_all(self):
        self.value_list.setEnabled(True)
        self.ui.edit_value.setEnabled(True)
        self.ui.add_value.setEnabled(True)
        self.ui.remove_value.setEnabled(True)

    def tag_changed(self, text):
        tag_names = self.ui.tag_names
        tag_names.editTextChanged.disconnect(self.tag_changed)
        if self.value_list.count() == 0 and self.tag and self.tag not in self.default_tags:
            tag_names.removeItem(tag_names.currentIndex())
        row = tag_names.findText(text, QtCore.Qt.MatchFixedString)
        if row == -1:
            tag_names.addItem(text)
            tag_names.setCurrentIndex(tag_names.count() - 1)
            tag_names.model().sort(0)
        else:
            tag_names.setCurrentIndex(row)
        self.tag = unicode(text)
        if row == 0:
            self.disable_all()
            tag_names.editTextChanged.connect(self.tag_changed)
            return
        self.enable_all()
        value_list = self.value_list
        value_list.clear()
        new_tags = self.metadata_box.new_tags
        values = self.modified_tags.get(self.tag, [])
        if not values:
            different = new_tags.different_placeholder(self.tag)
            if different:
                item = QtGui.QListWidgetItem(different)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                value_list.addItem(item)
            else:
                values = new_tags.get(self.tag, [""])[0]
        for value in values:
            if value:
                item = QtGui.QListWidgetItem(value)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                value_list.addItem(item)
        value_list.setCurrentItem(value_list.item(0), QtGui.QItemSelectionModel.SelectCurrent)
        tag_names.editTextChanged.connect(self.tag_changed)

    def value_edited(self, item):
        row = self.value_list.row(item)
        self._modified_tag()[row] = unicode(item.text())
        font = item.font()
        font.setItalic(False)
        item.setFont(font)

    def _modified_tag(self):
        return self.modified_tags.setdefault(self.tag,
            list(self.metadata_box.new_tags.get(self.tag, [("")])[0]))

    def accept(self):
        self.window.ignore_selection_changes = True
        for tag, values in self.modified_tags.items():
            self.modified_tags[tag] = [v for v in values if v]
        modified_tags = self.modified_tags.items()
        for obj in self.metadata_box.objects:
            for tag, values in modified_tags:
                if values:
                    obj.metadata[tag] = values
                else:
                    obj.metadata._items.pop(tag, None)
            obj.update()
        self.window.ignore_selection_changes = False
        self.window.update_selection()
        QtGui.QDialog.accept(self)

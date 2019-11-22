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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import config
from picard.util.tags import (
    TAG_NAMES,
    display_tag_name,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_interface_top_tags import (
    Ui_InterfaceTopTagsOptionsPage,
)


class TagListModel(QtCore.QAbstractListModel):
    def __init__(self, tags, parent=None):
        super().__init__(parent)
        self.tags = [(tag, display_tag_name(tag)) for tag in tags]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.tags)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return None
        i = index.row()
        field = 1 if role == QtCore.Qt.DisplayRole else 0
        try:
            return self.tags[i][field]
        except IndexError:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return False
        i = index.row()
        try:
            if role == QtCore.Qt.EditRole:
                display_name = display_tag_name(value) if value else value
                self.tags[i] = (value, display_name)
            elif role == QtCore.Qt.DisplayRole:
                current = self.tags[i]
                self.tags[i] = (current[0], value)
            return True
        except IndexError:
            return False

    def flags(self, index):
        if index.isValid():
            return (QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsDragEnabled
                | QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemNeverHasChildren)
        else:
            return QtCore.Qt.ItemIsDropEnabled

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        super().beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            self.tags.insert(row, ("", ""))
        super().endInsertRows()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        super().beginRemoveRows(parent, row, row + count - 1)
        self.tags = self.tags[:row] + self.tags[row + count:]
        super().endRemoveRows()
        return True

    def supportedDragActions(self):
        return QtCore.Qt.MoveAction

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def clear(self):
        self.beginResetModel()
        self.tags = []
        self.endResetModel()


class TagItemDelegate(QtWidgets.QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        completer = QtWidgets.QCompleter(TAG_NAMES.keys(), parent)

        def complete(text):
            parent.setFocus()

        completer.activated.connect(complete)
        editor.setCompleter(completer)
        return editor


class InterfaceTopTagsOptionsPage(OptionsPage):

    NAME = "interface_top_tags"
    TITLE = N_("Top Tags")
    PARENT = "interface"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        config.ListOption("setting", "metadatabox_top_tags", [
            "title",
            "artist",
            "album",
            "tracknumber",
            "~length",
            "date",
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_InterfaceTopTagsOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        tags = config.setting["metadatabox_top_tags"]
        self._model = TagListModel(tags)
        self.ui.top_tags_list.setItemDelegate(TagItemDelegate())
        self.ui.top_tags_list.setModel(self._model)

    def save(self):
        tags = []
        for tag, name in self._model.tags:
            tags.append(tag)
        if tags != config.setting["metadatabox_top_tags"]:
            config.setting["metadatabox_top_tags"] = tags
            self.tagger.window.metadata_box.update()

    def restore_defaults(self):
        self._model.clear()
        super().restore_defaults()


register_options_page(InterfaceTopTagsOptionsPage)

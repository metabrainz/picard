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

from picard.util.tags import (
    TAG_NAMES,
    display_tag_name,
)


class EditableTagListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        model = TagListModel()
        self.setModel(model)
        self.setItemDelegate(TagItemDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.NoModifier
            and event.key() == QtCore.Qt.Key_Delete):
            self.remove_selected_rows()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(QtCore.QPoint(event.x(), event.y()))
        if index.isValid():
            super().mouseDoubleClickEvent(event)
        else:
            self.add_empty_row()

    def closeEditor(self, editor, hint):
        if not editor.text():
            index = self.currentIndex()
            row = index.row()
            self.model().removeRow(row)
            self.select_row(row)
            editor.parent().setFocus()
        else:
            super().closeEditor(editor, hint)

    def add_tag(self, tag=""):
        model = self.model()
        row = model.rowCount()
        model.insertRow(row)
        index = model.createIndex(row, 0)
        model.setData(index, tag)
        return index

    def clear(self):
        self.model().update([])

    def update(self, tags):
        self.model().update(tags)

    @property
    def tags(self):
        return self.model().tags

    def add_empty_row(self):
        index = self.add_tag()
        self.setCurrentIndex(index)
        self.edit(index)

    def remove_selected_rows(self):
        rows = self.get_selected_rows()
        if not rows:
            return
        model = self.model()
        for row in sorted(rows, reverse=True):
            model.removeRow(row)
        first_selected_row = rows[0]
        self.select_row(first_selected_row)

    def move_selected_rows_up(self):
        rows = self.get_selected_rows()
        if not rows:
            return
        first_selected_row = min(rows)
        if first_selected_row > 0:
            self._move_rows_relative(rows, -1)

    def move_selected_rows_down(self):
        rows = self.get_selected_rows()
        if not rows:
            return
        last_selected_row = max(rows)
        if last_selected_row < self.model().rowCount() - 1:
            self._move_rows_relative(rows, 1)

    def select_row(self, row):
        index = self.model().index(row, 0)
        self.setCurrentIndex(index)

    def get_selected_rows(self):
        return [index.row() for index in self.selectedIndexes()]

    def _move_rows_relative(self, rows, direction):
        model = self.model()
        current_index = self.currentIndex()
        selection = self.selectionModel()
        for row in sorted(rows, reverse=direction > 0):
            new_index = model.index(row + direction, 0)
            model.move_row(row, new_index.row())
            selection.select(new_index, QtCore.QItemSelectionModel.Select)
            if row == current_index.row():
                selection.setCurrentIndex(new_index, QtCore.QItemSelectionModel.Current)


class TagListModel(QtCore.QAbstractListModel):
    def __init__(self, tags=None, parent=None):
        super().__init__(parent)
        self._tags = [(tag, display_tag_name(tag)) for tag in tags or []]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._tags)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return None
        field = 1 if role == QtCore.Qt.DisplayRole else 0
        try:
            return self._tags[index.row()][field]
        except IndexError:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return False
        i = index.row()
        try:
            if role == QtCore.Qt.EditRole:
                display_name = display_tag_name(value) if value else value
                self._tags[i] = (value, display_name)
            elif role == QtCore.Qt.DisplayRole:
                current = self._tags[i]
                self._tags[i] = (current[0], value)
            return True
        except IndexError:
            return False

    @staticmethod
    def flags(index):
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
            self._tags.insert(row, ("", ""))
        super().endInsertRows()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        super().beginRemoveRows(parent, row, row + count - 1)
        self._tags = self._tags[:row] + self._tags[row + count:]
        super().endRemoveRows()
        return True

    @staticmethod
    def supportedDragActions():
        return QtCore.Qt.MoveAction

    @staticmethod
    def supportedDropActions():
        return QtCore.Qt.MoveAction

    def update(self, tags):
        self.beginResetModel()
        self._tags = [(tag, display_tag_name(tag)) for tag in tags]
        self.endResetModel()

    def move_row(self, row, new_row):
        item = self._tags[row]
        self.removeRow(row)
        self.insertRow(new_row)
        index = self.index(new_row, 0)
        self.setData(index, item[0], QtCore.Qt.EditRole)
        self.setData(index, item[1], QtCore.Qt.DisplayRole)

    @property
    def tags(self):
        return (t[0] for t in self._tags)


class TagItemDelegate(QtWidgets.QItemDelegate):
    @staticmethod
    def createEditor(parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        completer = QtWidgets.QCompleter(TAG_NAMES.keys(), parent)

        def complete(text):
            parent.setFocus()

        completer.activated.connect(complete)
        editor.setCompleter(completer)
        return editor

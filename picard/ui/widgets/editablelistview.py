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
    QtGui,
    QtWidgets,
)


class EditableListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Delete):
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
        model = self.model()
        index = self.currentIndex()
        if not editor.text():
            row = index.row()
            model.removeRow(row)
            self.select_row(row)
            editor.parent().setFocus()
        else:
            super().closeEditor(editor, hint)
            if not model.user_sortable:
                data = index.data(QtCore.Qt.EditRole)
                model.sort(0)
                self.select_key(data)

    def add_item(self, value=""):
        model = self.model()
        row = model.rowCount()
        model.insertRow(row)
        index = model.createIndex(row, 0)
        model.setData(index, value)
        return index

    def clear(self):
        self.model().update([])

    def update(self, values):
        self.model().update(values)

    @property
    def items(self):
        return self.model().items

    def add_empty_row(self):
        index = self.add_item()
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

    def select_key(self, value):
        model = self.model()
        for row in range(0, model.rowCount() - 1):
            index = model.createIndex(row, 0)
            if value == index.data(QtCore.Qt.EditRole):
                self.setCurrentIndex(index)
                break

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


class EditableListModel(QtCore.QAbstractListModel):
    user_sortable_changed = QtCore.pyqtSignal(bool)

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._items = [(item, self.get_display_name(item)) for item in items or []]
        self._user_sortable = True

    @property
    def user_sortable(self):
        return self._user_sortable

    @user_sortable.setter
    def user_sortable(self, user_sortable):
        self._user_sortable = user_sortable
        if not user_sortable:
            self.sort(0)
        self.user_sortable_changed.emit(user_sortable)

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.beginResetModel()
        self._items.sort(key=lambda t: t[1], reverse=(order == QtCore.Qt.DescendingOrder))
        self.endResetModel()

    def get_display_name(self, item):  # pylint: disable=no-self-use
        return item

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return None
        field = 1 if role == QtCore.Qt.DisplayRole else 0
        try:
            return self._items[index.row()][field]
        except IndexError:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return False
        i = index.row()
        try:
            if role == QtCore.Qt.EditRole:
                display_name = self.get_display_name(value) if value else value
                self._items[i] = (value, display_name)
            elif role == QtCore.Qt.DisplayRole:
                current = self._items[i]
                self._items[i] = (current[0], value)
            return True
        except IndexError:
            return False

    def flags(self, index):
        if index.isValid():
            flags = (QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemNeverHasChildren)
            if self.user_sortable:
                flags |= QtCore.Qt.ItemIsDragEnabled
            return flags
        elif self.user_sortable:
            return QtCore.Qt.ItemIsDropEnabled
        else:
            return QtCore.Qt.NoItemFlags

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        super().beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            self._items.insert(row, ("", ""))
        super().endInsertRows()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        super().beginRemoveRows(parent, row, row + count - 1)
        self._items = self._items[:row] + self._items[row + count:]
        super().endRemoveRows()
        return True

    @staticmethod
    def supportedDragActions():
        return QtCore.Qt.MoveAction

    @staticmethod
    def supportedDropActions():
        return QtCore.Qt.MoveAction

    def update(self, items):
        self.beginResetModel()
        self._items = [(item, self.get_display_name(item)) for item in items]
        self.endResetModel()

    def move_row(self, row, new_row):
        item = self._items[row]
        self.removeRow(row)
        self.insertRow(new_row)
        index = self.index(new_row, 0)
        self.setData(index, item[0], QtCore.Qt.EditRole)
        self.setData(index, item[1], QtCore.Qt.DisplayRole)

    @property
    def items(self):
        return (t[0] for t in self._items)


class AutocompleteItemDelegate(QtWidgets.QItemDelegate):
    def __init__(self, completions, parent=None):
        super().__init__(parent)
        self._completions = completions

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None

        def complete(text):
            parent.setFocus()

        editor = super().createEditor(parent, option, index)
        completer = QtWidgets.QCompleter(self._completions, parent)
        completer.activated.connect(complete)
        editor.setCompleter(completer)
        return editor

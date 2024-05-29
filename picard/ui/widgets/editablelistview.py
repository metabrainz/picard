# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022 Philipp Wolfer
# Copyright (C) 2020-2024 Laurent Monin
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
    QtGui,
    QtWidgets,
)


class EditableListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.StandardKey.Delete):
            self.remove_selected_rows()
        elif event.key() == QtCore.Qt.Key.Key_Insert:
            self.add_empty_row()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        pos = event.pos()
        index = self.indexAt(QtCore.QPoint(pos.x(), pos.y()))
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
                data = index.data(QtCore.Qt.ItemDataRole.EditRole)
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
        # Setting the focus causes any open editor to getting closed
        self.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
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
        for row in range(0, model.rowCount()):
            index = model.createIndex(row, 0)
            if value == index.data(QtCore.Qt.ItemDataRole.EditRole):
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
            selection.select(new_index, QtCore.QItemSelectionModel.SelectionFlag.Select)
            if row == current_index.row():
                selection.setCurrentIndex(new_index, QtCore.QItemSelectionModel.SelectionFlag.Current)


class UniqueEditableListView(EditableListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_drag_drop = False

    def setModel(self, model):
        current_model = self.model()
        if current_model:
            current_model.dataChanged.disconnect(self.on_data_changed)
        super().setModel(model)
        model.dataChanged.connect(self.on_data_changed)

    def dropEvent(self, event):
        self._is_drag_drop = True
        super().dropEvent(event)
        self._is_drag_drop = False

    def on_data_changed(self, top_left, bottom_right, roles):
        # Do not drop duplicates during drag and drop as there is always
        # a duplicate in the list for a short time in this case.
        if self._is_drag_drop:
            return
        model = self.model()
        if QtCore.Qt.ItemDataRole.EditRole in roles:
            value = model.data(top_left, QtCore.Qt.ItemDataRole.EditRole)
            if not value:
                return
            # Remove duplicate entries from the model
            changed_row = top_left.row()
            row = 0
            for item in model.items:
                if item == value and row != changed_row:
                    model.removeRow(row)
                    row -= 1
                    if changed_row > row:
                        changed_row -= 1
                row += 1
            self.select_row(changed_row)


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

    def sort(self, column, order=QtCore.Qt.SortOrder.AscendingOrder):
        self.beginResetModel()
        self._items.sort(key=lambda t: t[1], reverse=(order == QtCore.Qt.SortOrder.DescendingOrder))
        self.endResetModel()

    def get_display_name(self, item):  # pylint: disable=no-self-use
        return item

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in {QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole}:
            return None
        field = 1 if role == QtCore.Qt.ItemDataRole.DisplayRole else 0
        try:
            return self._items[index.row()][field]
        except IndexError:
            return None

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.EditRole):
        if not index.isValid() or role not in {QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole}:
            return False
        i = index.row()
        try:
            if role == QtCore.Qt.ItemDataRole.EditRole:
                display_name = self.get_display_name(value) if value else value
                self._items[i] = (value, display_name)
            elif role == QtCore.Qt.ItemDataRole.DisplayRole:
                current = self._items[i]
                self._items[i] = (current[0], value)
            self.dataChanged.emit(index, index, [role])
            return True
        except IndexError:
            return False

    def flags(self, index):
        if index.isValid():
            flags = (QtCore.Qt.ItemFlag.ItemIsSelectable
                | QtCore.Qt.ItemFlag.ItemIsEditable
                | QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemNeverHasChildren)
            if self.user_sortable:
                flags |= QtCore.Qt.ItemFlag.ItemIsDragEnabled
            return flags
        elif self.user_sortable:
            return QtCore.Qt.ItemFlag.ItemIsDropEnabled
        else:
            return QtCore.Qt.ItemFlag.NoItemFlags

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
        return QtCore.Qt.DropAction.MoveAction

    @staticmethod
    def supportedDropActions():
        return QtCore.Qt.DropAction.MoveAction

    def update(self, items):
        self.beginResetModel()
        self._items = [(item, self.get_display_name(item)) for item in items]
        self.endResetModel()

    def move_row(self, row, new_row):
        item = self._items[row]
        self.removeRow(row)
        self.insertRow(new_row)
        index = self.index(new_row, 0)
        self.setData(index, item[0], QtCore.Qt.ItemDataRole.EditRole)
        self.setData(index, item[1], QtCore.Qt.ItemDataRole.DisplayRole)

    @property
    def items(self):
        return (t[0] for t in self._items)


class AutocompleteItemDelegate(QtWidgets.QItemDelegate):
    def __init__(self, completions, parent=None):
        super().__init__(parent=parent)
        self._completions = completions

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None

        def complete(text):
            parent.setFocus()

        editor = super().createEditor(parent, option, index)
        completer = QtWidgets.QCompleter(self._completions, parent)
        completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.activated.connect(complete)
        editor.setCompleter(completer)
        return editor

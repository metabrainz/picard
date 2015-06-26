#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2015 Laurent Monin
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from PyQt4 import QtCore, QtGui
import sys
import cPickle

"""
List of re-orderable checkable items
"""


class Signal:

    """Signal class from http://blog.abstractfactory.io/dynamic-signals-in-pyqt/
    """

    def __init__(self):
        self.__subscribers = []

    def emit(self, *args, **kwargs):
        for subs in self.__subscribers:
            subs(*args, **kwargs)

    def connect(self, func):
        self.__subscribers.append(func)

    def disconnect(self, func):
        try:
            self.__subscribers.remove(func)
        except ValueError:
            print 'Warning: function %s not removed from signal %s' % (func, self)


class SortCheckListItem:

    def __init__(self, text=u'', checked=False, data=None):
        self._checked = checked
        self._text = text
        self._data = data

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    def checked(self):
        return self._checked

    def setChecked(self, state):
        self._checked = state

    def data(self):
        return self._data

    def setData(self, data):
        self._data = data

    def __repr__(self):
        params = []
        params.append('text=' + repr(self._text))
        params.append('checked=' + repr(self._checked))
        if self._data is not None:
            params.append('data=' + repr(self._data))
        return 'SortCheckListItem(' + ','.join(params) + ')'


class SortCheckListView(QtGui.QListView):

    def __init__(self, parent=None):
        super(SortCheckListView, self).__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(self.InternalMove)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(self.ExtendedSelection)
        self.setModel(SortCheckListModel(self))

    def onChange(self, func):
        self.model().modified.connect(func)

    def setItems(self, items):
        self.model().setItems(items)

    def getItems(self):
        return self.model().getItems()


class SortCheckListModel(QtCore.QAbstractListModel):

    Mimetype = 'application/vnd.sortchecklistitem.list'

    def __init__(self, parent=None):
        super(SortCheckListModel, self).__init__(parent)
        self.__items_count = 0
        self.__modified_emit = True
        self.modified = Signal()

    def setItems(self, items):
        self.__data = items
        self.__items_count = len(items)
        self.__modified()
        self.reset()

    def getItems(self):
        return self.__data

    def __modified(self):
        if self.__modified_emit:
            self.modified.emit(self.getItems())

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return True
        if not data.hasFormat(self.Mimetype):
            return False
        if column > 0:
            return False
        if row != -1:
            beginRow = row
        elif parent.isValid():
            beginRow = parent.row()
        else:
            beginRow = self.rowCount(QtCore.QModelIndex())

        items = cPickle.loads(str(data.data(self.Mimetype)))
        if items:
            n = len(items)
            self.__modified_emit = False
            self.insertRows(beginRow, n)
            for i, item in enumerate(items):
                idx = self.index(beginRow + i, 0, QtCore.QModelIndex())
                self.setData(idx, item.text(), QtCore.Qt.EditRole)
                self.setData(idx, self._bool2check(item.checked()),
                             QtCore.Qt.CheckStateRole)
                self.setData(idx, item.data(), QtCore.Qt.UserRole)
            self.__modified_emit = True
        return True

    def flags(self, index):
        flags = super(SortCheckListModel, self).flags(index)

        if index.isValid():
            flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable
        else:
            flags |= QtCore.Qt.ItemIsDropEnabled

        return flags

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        self.__data[row:row] = [SortCheckListItem() for x in range(0, count)]
        self.endInsertRows()
        self.__modified()
        return True

    def mimeData(self, indexes):
        sortedIndexes = sorted([index for index in indexes
                                if index.isValid()], key=lambda index: index.row())
        items = [self.__data[x.row()] for x in sortedIndexes]
        mimeData = QtCore.QMimeData()
        mimeData.setData(self.Mimetype, cPickle.dumps(items))
        return mimeData

    def mimeTypes(self):
        return [self.Mimetype]

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        del self.__data[row:row + count]
        self.endRemoveRows()
        self.__modified()
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__data)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        if row > len(self.__data):
            return None

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.__data[row].text()

        if role == QtCore.Qt.CheckStateRole:
            return self._bool2check(self.__data[row].checked())

        if role == QtCore.Qt.UserRole:
            return self.__data[row].data()

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        changed = False
        item = self.__data[index.row()]
        if role == QtCore.Qt.EditRole:
            changed = (item.text() != value)
            if changed:
                item.setText(value)
        elif role == QtCore.Qt.CheckStateRole:
            oldvalue = item.checked()
            newvalue = self._check2bool(value)
            changed = (oldvalue != newvalue)
            if changed:
                item.setChecked(newvalue)
        elif role == QtCore.Qt.UserRole:
            olddata = item.data()
            newdata = value
            changed = (olddata != newdata)
            if changed:
                item.setData(newdata)
        if changed:
            self.dataChanged.emit(index, index)
            self.__modified()
            return True
        return False

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction

    def _bool2check(self, checked):
        if checked:
            return QtCore.Qt.Checked
        return QtCore.Qt.Unchecked

    def _check2bool(self, qtchecked):
        if qtchecked == QtCore.Qt.Checked:
            return True
        return False


if __name__ == '__main__':
    def main():
        app = QtGui.QApplication(sys.argv)
        main = MainWindow()
        main.show()
        sys.exit(app.exec_())

    class MainWindow(QtGui.QMainWindow):

        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            view = SortCheckListView()
            view.setItems([SortCheckListItem(u'A'),
                           SortCheckListItem(u'B', True, data='mydata'),
                           SortCheckListItem(u'C'),
                           SortCheckListItem(u'D')])
            self.setCentralWidget(view)
            view.onChange(self.dataChanged)

        def dataChanged(self, items):
            print "items = ", repr(items)

    main()

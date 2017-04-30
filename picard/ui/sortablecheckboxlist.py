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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from functools import partial
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal


class SortableCheckboxListWidget(QtWidgets.QWidget):
    _CHECKBOX_POS = 0
    _BUTTON_UP = 1
    _BUTTON_DOWN = 2

    __no_emit = False
    changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super(SortableCheckboxListWidget, self).__init__(parent)
        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.__items = []

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def setSignals(self, row):
        layout = self.layout()
        checkbox = layout.itemAtPosition(row, self._CHECKBOX_POS).widget()
        up = layout.itemAtPosition(row, self._BUTTON_UP).widget()
        down = layout.itemAtPosition(row, self._BUTTON_DOWN).widget()
        checkbox.stateChanged.connect(partial(self.checkbox_toggled, row))
        up.clicked.connect(partial(self.move_button_clicked, row, up=True))
        down.clicked.connect(partial(self.move_button_clicked, row, up=False))

    def moveItem(self, from_row, to_row):
        to_row = to_row % len(self.__items)
        self.__items[to_row], self.__items[from_row] = \
            self.__items[from_row], self.__items[to_row]
        self.updateRow(to_row)
        self.updateRow(from_row)
        self._emit_changed()

    def checkbox_toggled(self, row, state):
        self.__items[row].setChecked(state == QtCore.Qt.Checked)
        self._emit_changed()

    def move_button_clicked(self, row, up):
        if up:
            to = row - 1
        else:
            to = row + 1
        self.moveItem(row, to)

    def updateRow(self, row):
        self.__no_emit = True
        item = self.__items[row]
        layout = self.layout()
        checkbox = layout.itemAtPosition(row, self._CHECKBOX_POS).widget()
        checkbox.setText(item.text)
        checkbox.setChecked(item.checked)
        self.__no_emit = False

    def addItem(self, item):
        self.__items.append(item)
        row = len(self.__items) - 1
        layout = self.layout()
        layout.addWidget(QtWidgets.QCheckBox(), row, self._CHECKBOX_POS)
        self.updateRow(row)
        up_button = QtWidgets.QToolButton()
        up_button.setArrowType(QtCore.Qt.UpArrow)
        up_button.setMaximumSize(QtCore.QSize(16, 16))
        down_button = QtWidgets.QToolButton()
        down_button.setArrowType(QtCore.Qt.DownArrow)
        down_button.setMaximumSize(QtCore.QSize(16, 16))
        layout.addWidget(up_button, row, self._BUTTON_UP)
        layout.addWidget(down_button, row, self._BUTTON_DOWN)
        self.setSignals(row)

    def _emit_changed(self):
        if not self.__no_emit:
            self.changed.emit(self.__items)

    def clear(self):
        for i in reversed(range(len(self.__items))):
            self._remove(i)
        self.__items = []

    def _remove(self, row):
        self.layout().itemAtPosition(row, self._CHECKBOX_POS).widget().setParent(None)
        self.layout().itemAtPosition(row, self._BUTTON_UP).widget().setParent(None)
        self.layout().itemAtPosition(row, self._BUTTON_DOWN).widget().setParent(None)


class SortableCheckboxListItem(object):

    def __init__(self, text='', checked=False, data=None):
        self._checked = checked
        self._text = text
        self._data = data

    @property
    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    @property
    def checked(self):
        return self._checked

    def setChecked(self, state):
        self._checked = state

    @property
    def data(self):
        return self._data

    def setData(self, data):
        self._data = data

    def __repr__(self):
        params = []
        params.append('text=' + repr(self.text))
        params.append('checked=' + repr(self.checked))
        if self.data is not None:
            params.append('data=' + repr(self.data))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(params))

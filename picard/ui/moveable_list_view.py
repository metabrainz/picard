# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2018 Sambhav Kothari
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


class MoveableListView:

    def __init__(self, list_widget, up_button, down_button, callback=None):
        self.list_widget = list_widget
        self.up_button = up_button
        self.down_button = down_button
        self.update_callback = callback
        self.up_button.clicked.connect(partial(self.move_item, 1))
        self.down_button.clicked.connect(partial(self.move_item, -1))
        self.list_widget.currentRowChanged.connect(self.update_buttons)
        self.list_widget.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.list_widget.setDefaultDropAction(QtCore.Qt.MoveAction)

    def move_item(self, offset):
        current_index = self.list_widget.currentRow()
        offset_index = current_index - offset
        offset_item = self.list_widget.item(offset_index)
        if offset_item:
            current_item = self.list_widget.takeItem(current_index)
            self.list_widget.insertItem(offset_index, current_item)
            self.list_widget.setCurrentItem(current_item)
            self.update_buttons()

    def update_buttons(self):
        current_row = self.list_widget.currentRow()
        self.up_button.setEnabled(current_row > 0)
        self.down_button.setEnabled(current_row < self.list_widget.count() - 1)
        if self.update_callback:
            self.update_callback()

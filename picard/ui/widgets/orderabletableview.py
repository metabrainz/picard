# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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
    QtGui,
    QtWidgets,
)


class OrderableTableView(QtWidgets.QTableView):
    """QListView widget allowing line reordering via moving the currently selected line
    up or down one position, or via drag 'n' drop into the new position."""
    def __init__(self, parent):
        super().__init__(parent)
        self.verticalHeader().hide()
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setShowGrid(True)
        self.setDragDropMode(self.InternalMove)
        self.setDragDropOverwriteMode(False)

        # Set our custom style - this draws the drop indicator across the whole row
        self.setStyle(OrderableTableViewStyle())

        # Set our custom model - this prevents row shifting
        self.model = OrderableTableViewModel()
        self.setModel(self.model)

    def move_row_up(self):
        """Moves the current row up one position"""
        current_row = self.currentIndex().row()
        if current_row < 1:
            return
        self._do_move(current_row, current_row - 1)

    def move_row_down(self):
        """Moves the current row down one position"""
        current_row = self.currentIndex().row()
        if current_row >= self.model.rowCount() - 1:
            return
        self._do_move(current_row, current_row + 1)

    def _do_move(self, old_row, new_row):
        current_item = self.model.takeRow(old_row)
        self.model.insertRow(new_row, current_item)
        self.setCurrentIndex(self.model.index(new_row, 0))


class OrderableTableViewModel(QtGui.QStandardItemModel):
    def dropMimeData(self, data, action, row, col, parent):
        """Always move the entire row, and don't allow column shifting"""
        return super().dropMimeData(data, action, row, 0, parent)


class OrderableTableViewStyle(QtWidgets.QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        """Draw a line across the entire row rather than just the column we're hovering over"""
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            if widget:
                option_new.rect.setRight(widget.width())
            option = option_new
        super().drawPrimitive(element, option, painter, widget)

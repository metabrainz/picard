# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018, 2021-2024 Laurent Monin
# Copyright (C) 2019, 2021-2022, 2024 Philipp Wolfer
# Copyright (C) 2020 Ray Bouchard
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


"""
This can be used for basic dialogs that mostly contain a table as its core feature
"""

from abc import abstractmethod

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt6.QtCore import pyqtSignal

from picard import log
from picard.config import get_config
from picard.i18n import (
    gettext as _,
    sort_key,
)
from picard.util import (
    restore_method,
    throttle,
)

from picard.ui import PicardDialog
from picard.ui.colors import interface_colors
from picard.ui.columns import (
    ColumnAlign,
    Columns,
    ColumnSortType,
)


class ResultTable(QtWidgets.QTableWidget):

    def __init__(self, parent=None, parent_dialog=None):
        super().__init__(parent=parent)
        self.parent_dialog = parent_dialog
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)

        self.horizontalScrollBar().valueChanged.connect(self.emit_scrolled)
        self.verticalScrollBar().valueChanged.connect(self.emit_scrolled)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)

    def prepare(self, labels):
        self.clear()
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)
        self.setRowCount(0)
        self.setSortingEnabled(False)

    @throttle(1000)  # only emit scrolled signal once per second
    def emit_scrolled(self, value):
        if self.parent_dialog:
            self.parent_dialog.scrolled.emit()

    @throttle(1000)  # only emit resized signal once per second
    def emit_resized(self):
        if self.parent_dialog:
            self.parent_dialog.resized.emit()

    def resizeEvent(self, event):
        self.emit_resized()
        super().resizeEvent(event)


class SortableTableWidgetItem(QtWidgets.QTableWidgetItem):

    def __init__(self, obj=None):
        super().__init__()
        self._obj = obj

    def __lt__(self, other):
        column = self.column()
        return self.sortkey(column) < other.sortkey(column)

    def sortkey(self, column):
        this_column = self.tableWidget().parent_dialog.columns[column]

        if this_column.sort_type == ColumnSortType.SORTKEY:
            sortkey = this_column.sortkey(self._obj)
        elif this_column.sort_type == ColumnSortType.NAT:
            sortkey = sort_key(self.text(), numeric=True)
        else:
            sortkey = sort_key(self.text())
        return sortkey


class TableBasedDialog(PicardDialog):

    defaultsize = QtCore.QSize(720, 360)
    scrolled = pyqtSignal()
    resized = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setupUi()
        self.columns = Columns()
        self.sorting_enabled = True
        self.create_table()
        self.finished.connect(self.save_state)

    def set_table_item_value(self, row, colname, value, obj=None):
        item = SortableTableWidgetItem(obj=obj)
        item.setText(value)
        pos = self.columns.pos(colname)
        column = self.columns[pos]
        if column.align == ColumnAlign.RIGHT:
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        if pos == 0:
            item.setData(QtCore.Qt.ItemDataRole.UserRole, row)
        self.table.setItem(row, pos, item)

    @abstractmethod
    def setupUi(self):
        pass

    def add_widget_to_center_layout(self, widget):
        """Update center widget with new child. If child widget exists,
        schedule it for deletion."""
        widget_item = self.center_layout.takeAt(0)
        if widget_item:
            current_widget = widget_item.widget()
            current_widget.hide()
            self.center_layout.removeWidget(current_widget)
            if current_widget != self.table:
                current_widget.deleteLater()
        self.center_layout.addWidget(widget)
        widget.show()

    def create_table_obj(self):
        return ResultTable(parent_dialog=self)

    def create_table(self):
        self.table = self.create_table_obj()
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.table.setSortingEnabled(False)
        self.table.cellDoubleClicked.connect(self.accept)
        self.table.hide()

        def enable_accept_button():
            self.accept_button.setEnabled(True)
        self.table.itemSelectionChanged.connect(enable_accept_button)

    def highlight_row(self, row):
        model = self.table.model()
        highlight_color = interface_colors.get_qcolor('row_highlight')
        highlight_brush = QtGui.QBrush(highlight_color)
        for column in range(0, model.columnCount()):
            index = model.index(row, column)
            model.setData(index, highlight_brush, QtCore.Qt.ItemDataRole.BackgroundRole)

    def restore_default_columns(self):
        labels = tuple(_(c.title) for c in self.columns)
        self.table.prepare(labels)

        self.table.setSortingEnabled(self.sorting_enabled)

        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(self.columns.default_width)

        for i, c in enumerate(self.columns):
            if c.width is not None:
                header.resizeSection(i, c.width)
            if c.resizeable:
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
            else:
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Fixed)

    def prepare_table(self):
        self.restore_table_header_state()

    def show_table(self, sort_column=None, sort_order=QtCore.Qt.SortOrder.DescendingOrder):
        self.add_widget_to_center_layout(self.table)
        self.table.horizontalHeader().setSortIndicatorShown(self.sorting_enabled)
        self.table.setSortingEnabled(self.sorting_enabled)
        if self.sorting_enabled and sort_column:
            pos = self.columns.pos(sort_column)
            self.table.sortItems(pos, sort_order)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setAlternatingRowColors(True)

    def accept(self):
        if self.table:
            selected_rows_user_values = []
            for idx in self.table.selectionModel().selectedRows():
                row = self.table.itemFromIndex(idx).data(QtCore.Qt.ItemDataRole.UserRole)
                selected_rows_user_values .append(row)
            self.accept_event(selected_rows_user_values)
        super().accept()

    @restore_method
    def restore_table_header_state(self):
        self.restore_default_columns()
        header = self.table.horizontalHeader()
        config = get_config()
        state = config.persist[self.dialog_header_state]
        if state:
            header.restoreState(state)
        log.debug("restore_state: %s", self.dialog_header_state)

    def save_state(self):
        if self.table:
            self.save_table_header_state()

    def save_table_header_state(self):
        state = self.table.horizontalHeader().saveState()
        config = get_config()
        config.persist[self.dialog_header_state] = state
        log.debug("save_state: %s", self.dialog_header_state)

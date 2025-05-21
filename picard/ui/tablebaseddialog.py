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
    ColumnSortType,
)


class ResultTable(QtWidgets.QTableWidget):

    def __init__(self, parent=None, parent_dialog=None):
        super().__init__(parent=parent)
        self.parent_dialog = parent_dialog
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.horizontalScrollBar().valueChanged.connect(self.emit_scrolled)
        self.verticalScrollBar().valueChanged.connect(self.emit_scrolled)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel)

    def set_labels(self, labels):
        labels = tuple(labels)
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)

    def clear_contents(self):
        self.clearContents()
        self.setRowCount(0)

    def cell_is_visible(self, row: int, column: int) -> bool:
        """
        Checks if a cell currently visible within the viewport.

        Args:
            row: The row index of the cell.
            column: The column index of the cell.

        Returns:
            True if the cell is visible, False otherwise.
        """
        # Source: https://forum.qt.io/topic/131108/how-to-determine-if-cell-of-a-qtablewidget-is-currently-visible/2?_=1747745577898
        row_count = self.rowCount()
        column_count = self.columnCount()
        if row_count == 0 or column_count == 0:
            return False

        if not (0 <= row < row_count and 0 <= column < column_count):
            return False

        vertical_header = self.verticalHeader()
        horizontal_header = self.horizontalHeader()

        # Get the visual indices of the visible rows
        # visualIndexAt(0) gives the visual index of the first visible item
        # visualIndexAt(header_height) gives the visual index of the last visible item
        # If the header is empty or fully scrolled, visualIndexAt might return -1
        row_start = max(vertical_header.visualIndexAt(0), 0)
        row_end = vertical_header.visualIndexAt(vertical_header.height())
        if row_end == -1:
            row_end = row_count - 1

        # Get the visual indices of the visible columns
        column_start = max(horizontal_header.visualIndexAt(0), 0)
        column_end = horizontal_header.visualIndexAt(horizontal_header.width())
        if column_end == -1:
            column_end = column_count - 1

        # Get the logical indices of the currently visible rows
        # In PyQt, visualIndexAt returns -1 if no item is at that position,
        # and logicalIndex converts a visual index to a logical index.
        visible_rows = set()
        vcount = vertical_header.count()
        for i in range(row_start, row_end + 1):
            # We need to check if the visual index is valid before converting
            # to logical index, as visualIndexAt can return out-of-bounds indices
            # for edge cases or empty headers.
            if 0 <= i < vcount:  # Ensure visual index is within header's visual count
                visible_rows.add(vertical_header.logicalIndex(i))

        # Get the logical indices of the currently visible columns
        visible_columns = set()
        hcount = horizontal_header.count()
        for j in range(column_start, column_end + 1):
            if 0 <= j < hcount:  # Ensure visual index is within header's visual count
                visible_columns.add(horizontal_header.logicalIndex(j))

        return row in visible_rows and column in visible_columns

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
        self.sorting_enabled = True
        self._sort_column_index = None
        self._sort_order = None
        self.create_table()
        self.finished.connect(self.save_state)

    def set_table_item_value(self, row, pos, column, obj):
        value = obj.get(column.key, "")
        item = SortableTableWidgetItem(obj=obj)
        item.setText(value)
        if column.align == ColumnAlign.RIGHT:
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.set_table_item(row, pos, item)

    def set_table_item(self, row, pos, item):
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

    def create_table(self):
        self.table = ResultTable(parent_dialog=self)
        self.table.setSortingEnabled(False)
        self.table.cellDoubleClicked.connect(self.accept)
        self.table.hide()

        def enable_accept_button():
            self.accept_button.setEnabled(True)
        self.table.itemSelectionChanged.connect(enable_accept_button)

        self.restore_default_columns()
        self.restore_table_header_state()

    def highlight_row(self, row):
        model = self.table.model()
        highlight_color = interface_colors.get_qcolor('row_highlight')
        highlight_brush = QtGui.QBrush(highlight_color)
        for column in range(0, model.columnCount()):
            index = model.index(row, column)
            model.setData(index, highlight_brush, QtCore.Qt.ItemDataRole.BackgroundRole)

    def header(self):
        return self.table.horizontalHeader()

    def restore_default_columns(self):
        self.table.set_labels(_(c.title) for c in self.columns)

        header = self.header()

        def sort_indicator_changed(idx, order):
            self._sort_column_index = idx
            self._sort_order = order

        header.sortIndicatorChanged.connect(sort_indicator_changed)

        header.setStretchLastSection(True)
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        header.setDefaultSectionSize(self.columns.default_width)

        for i, c in enumerate(self.columns):
            # header.show_column(i, c.is_default)
            if c.width is not None:
                header.resizeSection(i, c.width)
            if c.resizeable:
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
            else:
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Fixed)

    def prepare_table(self):
        self.table.clear_contents()
        # Disable sorting, as new elements will be added, and having sorting enabled
        # doesn't play well.
        # It will be eventually re-enabled in show_table()
        self.table.setSortingEnabled(False)

    def show_table(self, sort_column=None, sort_order=QtCore.Qt.SortOrder.DescendingOrder):
        self.add_widget_to_center_layout(self.table)
        header = self.header()
        header.setSortIndicatorShown(self.sorting_enabled)
        if self.sorting_enabled:
            if self._sort_column_index is None or self._sort_order is None:
                # Initialize the sort column & order based on passed parameters
                if sort_column is None:
                    pos = 0
                else:
                    pos = self.columns.pos(sort_column)
                # It will trigger a call to sort_indicator_changed()
                # This will set _sort_column_index and _sort_order to non-None values
                header.setSortIndicator(pos, sort_order)
        else:
            # no indicator
            # https://doc.qt.io/qt-6/qheaderview.html#setSortIndicator
            header.setSortIndicator(-1, sort_order)

        # Enabling sorting will sort using current sort column & order
        # https://doc.qt.io/qt-6/qtableview.html#setSortingEnabled
        self.table.setSortingEnabled(self.sorting_enabled)
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
        config = get_config()
        state = config.persist[self.dialog_header_state]
        if state:
            self.header().restoreState(state)
            log.debug("restore_state: %s", self.dialog_header_state)

    def save_state(self):
        if self.table:
            self.save_table_header_state()

    def save_table_header_state(self):
        state = self.header().saveState()
        config = get_config()
        config.persist[self.dialog_header_state] = state
        log.debug("save_state: %s", self.dialog_header_state)

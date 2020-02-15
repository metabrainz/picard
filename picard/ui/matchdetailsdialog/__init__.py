# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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

""" NOTE: THIS FILE IS HIGHLY BASED ON same __init__.py in searchdialog """

from collections import OrderedDict
import re
import traceback

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt5.Qt import QApplication
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialogButtonBox,
    QMenu,
    QWidgetAction,
)

from picard import (
    config,
    log,
)
from picard.util import (
    natsort,
    restore_method,
    throttle,
)

from picard.ui import PicardDialog
from picard.ui.util import StandardButton


class ResultTable(QtWidgets.QTableWidget):
    orig_col_headers_labels = []

    def __init__(self, parent):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)
        self.keywords = dict([(i, []) for i in range(self.columnCount())])
        self.filter_checkboxes = []
        self.col = None

        @throttle(1000)  # only emit scrolled signal once per second
        def emit_scrolled(x):
            parent.scrolled.emit()
        self.horizontalScrollBar().valueChanged.connect(emit_scrolled)
        self.verticalScrollBar().valueChanged.connect(emit_scrolled)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def prepare(self, headers):
        self.clear()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(0)
        self.setSortingEnabled(False)

    def slotSelect(self, state):
        for checkbox in self.filter_checkboxes:
            checkbox.setChecked(QtCore.Qt.Checked == state)

    def show_header_context_menu(self, position):
        try:
            self.clearFilter()
            self.menu = QMenu(self)
            self.col = self.horizontalHeader().logicalIndexAt(position)

            data_unique = []

            self.filter_checkboxes = []

            checkBox = QCheckBox("Select all", self.menu)
            checkableAction = QWidgetAction(self.menu)
            checkableAction.setDefaultWidget(checkBox)
            self.menu.addAction(checkableAction)
            checkBox.setChecked(True)
            checkBox.stateChanged.connect(self.slotSelect)

            for i in range(self.rowCount()):
                if not self.isRowHidden(i):
                    item = self.item(i, self.col)
                    if item.text() not in data_unique:
                        data_unique.append(item.text())

            data_unique.sort()

            for item in data_unique:
                checkBox = QCheckBox(item, self.menu)
                checkBox.setChecked(True)
                checkableAction = QWidgetAction(self.menu)
                checkableAction.setDefaultWidget(checkBox)
                self.menu.addAction(checkableAction)
                self.filter_checkboxes.append(checkBox)

            btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self.menu)
            btn.accepted.connect(self.menuClose)
            btn.rejected.connect(self.menu.close)
            checkableAction = QWidgetAction(self.menu)
            checkableAction.setDefaultWidget(btn)
            self.menu.addAction(checkableAction)

            headerPos = self.mapToGlobal(self.horizontalHeader().pos())

            posY = headerPos.y() + self.horizontalHeader().height()
            posX = headerPos.x() + self.horizontalHeader().sectionPosition(self.col)
            self.menu.exec_(QtCore.QPoint(posX, posY))
        except Exception:
            log.error(traceback.format_exc())

    def menuClose(self):
        self.keywords[self.col] = []
        did_filter = False
        for element in self.filter_checkboxes:
            if element.isChecked():
                self.keywords[self.col].append(element.text())
            else:
                did_filter = True

        # add decorator to show filtered.
        if did_filter:
            it = self.horizontalHeaderItem(self.col)
            oldHeader = it.text()
            newHeader = oldHeader + "*"
            it.setText(newHeader)

        self.filterdata()
        self.menu.close()

    def clearFilter(self):
        # clear filter
        for i in range(self.rowCount()):
            self.setRowHidden(i, False)

        # remove filter decoroator
        for i in range(self.columnCount()):
            it = self.horizontalHeaderItem(i)
            oldHeader = it.text()
            newHeader = re.sub('[*+]', '', oldHeader)
            it.setText(newHeader)

    def filterdata(self):

        columnsShow = dict([(i, True) for i in range(self.rowCount())])

        try:
            for i in range(self.rowCount()):
                for j in range(self.columnCount()):
                    item = self.item(i, j)
                    if j in self.keywords:
                        if item.text() not in self.keywords[j]:
                            columnsShow[i] = False
            for key, value in columnsShow.items():
                self.setRowHidden(key, not value)

        except Exception:
            log.error(traceback.format_exc())


class SortableTableWidgetItem(QtWidgets.QTableWidgetItem):

    def __init__(self, sort_key):
        super().__init__()
        self.sort_key = sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key


class MatchDetailsDialogBase(PicardDialog):

    defaultsize = QtCore.QSize(720, 360)
    autorestore = False
    scrolled = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.response_results = []
        self.setupUi()
        self.restore_state()
        # self.columns has to be an ordered dict, with column name as keys, and
        # matching label as values
        self.columns = None
        self.sorting_enabled = True
        self.create_table()
        self.finished.connect(self.save_state)

    @property
    def columns(self):
        return self.__columns

    @columns.setter
    def columns(self, list_of_tuples):
        if not list_of_tuples:
            list_of_tuples = []
        self.__columns = OrderedDict(list_of_tuples)
        self.__colkeys = list(self.columns.keys())

    @property
    def table_headers(self):
        return list(self.columns.values())

    def colpos(self, colname):
        return self.__colkeys.index(colname)

    def set_acoustid_lookup_url_edit(self, p_acoustid_lookup_url):
        self.acoustid_lookup_url.setText(_("Below is response in jSON format (also copied to clipboard).") + " <a href='" + p_acoustid_lookup_url + "'>" + _("Click to see AcoustId Fingerprint Lookup in browser") + "</a> ")

    def set_input_filename_lbl(self, p_filename):
        self.input_filename_lbl.setText("Input File: " + p_filename)

    def set_json_edit(self, json_str):
        self.json_edit.setText(json_str)
        self.json_edit.setCursorPosition(0)
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(json_str, mode=cb.Clipboard)

    def set_table_item(self, row, colname, value, sortkey=None):
        # QVariant remembers the original type of the data
        # matching comparison operator will be used when sorting
        # get() will return a string, force conversion if asked to
        if sortkey is None:
            sortkey = natsort.natkey(value)
        item = SortableTableWidgetItem(sortkey)
        item.setData(QtCore.Qt.DisplayRole, value)
        pos = self.colpos(colname)
        if pos == 0:
            item.setData(QtCore.Qt.UserRole, row)
        self.table.setItem(row, pos, item)

    def focus_in_event(self, event):
        # When focus is on json edit boxes, need to disable dialog's accept button.
        if self.table:
            self.table.clearSelection()
        self.accept_button.setEnabled(False)

    def setupUi(self):
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("vertical_layout")

        self.input_filename_widget = QtWidgets.QWidget(self)
        self.input_filename_lbl = QtWidgets.QLabel(self.input_filename_widget)
        self.input_filename_lbl.setFocusPolicy(QtCore.Qt.StrongFocus)
        myFont = QtGui.QFont()
        myFont.setBold(True)
        self.input_filename_lbl.setFont(myFont)
        self.input_filename_lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.verticalLayout.addWidget(self.input_filename_lbl)

        self.acoustid_lookup_url_widget = QtWidgets.QWidget(self)
        self.acoustid_lookup_url = QtWidgets.QLabel(self.acoustid_lookup_url_widget)
        self.acoustid_lookup_url.setOpenExternalLinks(True)
        self.verticalLayout.addWidget(self.acoustid_lookup_url)

        self.json_widget = QtWidgets.QWidget(self)
        self.json_edit = QtWidgets.QLineEdit(self.json_widget)
        self.json_edit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.json_edit.focusInEvent = self.focus_in_event
        self.verticalLayout.addWidget(self.json_edit)

        self.tip_widget = QtWidgets.QWidget(self)
        self.tip_lbl = QtWidgets.QLabel(self.tip_widget)
        self.tip_lbl.setText(_("\nTip: Column header left click to sort, right click to filter"))
        self.tip_lbl.setMargin(10)
        self.verticalLayout.addWidget(self.tip_lbl)

        self.center_widget = QtWidgets.QWidget(self)
        self.center_widget.setObjectName("center_widget")
        self.center_layout = QtWidgets.QVBoxLayout(self.center_widget)
        self.center_layout.setObjectName("center_layout")
        self.center_layout.setContentsMargins(1, 1, 1, 1)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.export_button = QtWidgets.QPushButton("Export grid", self.buttonBox)
        self.export_button.setEnabled(True)
        self.buttonBox.addButton(self.export_button, QtWidgets.QDialogButtonBox.ActionRole)
        self.export_button.clicked.connect(self.export_data)

        self.accept_button = QtWidgets.QPushButton("Load into Picard", self.buttonBox)
        self.accept_button.setEnabled(False)
        self.buttonBox.addButton(self.accept_button, QtWidgets.QDialogButtonBox.AcceptRole)

        self.buttonBox.addButton(StandardButton(StandardButton.CANCEL), QtWidgets.QDialogButtonBox.RejectRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.verticalLayout.addWidget(self.buttonBox)

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
        self.table = ResultTable(self)
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.table.setSortingEnabled(False)
        self.table.cellDoubleClicked.connect(self.accept)
        self.table.hide()

        def enable_accept_button():
            row = self.table.currentRow()
            col = self.table.columnCount()-1  # check to see if recording base score exist if so its a data row
            val = self.table.item(row, col).text()
            new_state = val is not None and val != "-1"
            self.accept_button.setEnabled(new_state)

        self.table.itemSelectionChanged.connect(enable_accept_button)

    def prepare_table(self):
        self.table.prepare(self.table_headers)
        self.restore_table_header_state()

    def show_table(self, sort_column=None, sort_order=QtCore.Qt.DescendingOrder):
        self.add_widget_to_center_layout(self.table)
        self.table.horizontalHeader().setSortIndicatorShown(self.sorting_enabled)
        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap)
        self.table.setSortingEnabled(self.sorting_enabled)
        if self.sorting_enabled and sort_column:
            self.table.sortItems(self.colpos(sort_column), sort_order)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setAlternatingRowColors(True)

    def export_data(self):
        self.export_match_dtl_entries_to_file()

    def accept(self):
        if self.table:
            selected_rows = []
            for idx in self.table.selectionModel().selectedRows():
                row = self.table.itemFromIndex(idx).data(QtCore.Qt.UserRole)
                selected_rows.append(row)
            self.accept_event(selected_rows)
        super().accept()

    @restore_method
    def restore_state(self):
        self.restore_geometry()

    @restore_method
    def restore_table_header_state(self):
        header = self.table.horizontalHeader()
        state = config.persist[self.dialog_header_state]
        if state:
            header.restoreState(state)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        log.debug("restore_state: {}".format(self.dialog_header_state))

    def save_state(self):
        if self.table:
            self.save_table_header_state()

    def save_table_header_state(self):
        state = self.table.horizontalHeader().saveState()
        config.persist[self.dialog_header_state] = state
        log.debug("save_state: {}".format(self.dialog_header_state))

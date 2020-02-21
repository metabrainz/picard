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


import re
import traceback

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
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

from picard.ui.tablebaseddialog import (
    ResultTable,
    TableBasedDialog,
)
from picard.ui.util import StandardButton


class MatchResultTable(ResultTable):
    orig_col_headers_labels = []

    def __init__(self, parent):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)
        self.unique_visible_values_by_col = dict([(i, []) for i in range(self.columnCount())])
        self.filter_checkboxes = []
        self.col = None

    def slotSelect(self, state):
        for checkbox in self.filter_checkboxes:
            checkbox.setChecked(QtCore.Qt.Checked == state)

    def show_header_context_menu(self, position):
        try:
            # self.clear_all_col_filters()
            self.menu = QMenu(self)
            self.col = self.horizontalHeader().logicalIndexAt(position)

            unique_col_values = []
            unique_visible_col_values = []
            self.filter_checkboxes = []

            # build list of unique values in this column
            for i in range(self.rowCount()):
                item = self.item(i, self.col)
                if item.text() not in unique_col_values:
                    unique_col_values.append(item.text())
                if item.text() not in unique_visible_col_values and not self.isRowHidden(i):
                    unique_visible_col_values.append(item.text())

            is_filtered = unique_col_values.__len__() != unique_visible_col_values.__len__()

            unique_col_values.sort()
            unique_visible_col_values.sort()

            # add the Select All checkbox to top of list
            checkBox = QCheckBox("Select all", self.menu)
            checkableAction = QWidgetAction(self.menu)
            checkableAction.setDefaultWidget(checkBox)
            self.menu.addAction(checkableAction)
            checkBox.setChecked(not is_filtered)
            checkBox.stateChanged.connect(self.slotSelect)

            # create checkbox for each unique value
            for value in unique_col_values:
                checkBox = QCheckBox(value, self.menu)
                checkBox.setChecked(value in unique_visible_col_values)
                checkableAction = QWidgetAction(self.menu)
                checkableAction.setDefaultWidget(checkBox)
                self.menu.addAction(checkableAction)
                self.filter_checkboxes.append(checkBox)

            # ok/cancel buttons
            btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self.menu)
            btn.accepted.connect(self.menuClose)
            btn.rejected.connect(self.menu.close)
            checkableAction = QWidgetAction(self.menu)
            checkableAction.setDefaultWidget(btn)
            self.menu.addAction(checkableAction)

            # show menu
            headerPos = self.mapToGlobal(self.horizontalHeader().pos())
            posY = headerPos.y() + self.horizontalHeader().height()
            posX = headerPos.x() + self.horizontalHeader().sectionPosition(self.col)
            self.menu.exec_(QtCore.QPoint(posX, posY))
        except Exception:
            log.error(traceback.format_exc())

    def menuClose(self):
        self.unique_visible_values_by_col[self.col] = []
        did_filter = False

        # build list of unique_visible_values_by_col to filter on, based on what user checked.
        for element in self.filter_checkboxes:
            if element.isChecked():
                self.unique_visible_values_by_col[self.col].append(element.text())
            else:
                did_filter = True

        # add/remove decorator to show filtered.
        self.showColFilterDecorator(did_filter)

        # apply filter (including nothing filtered
        self.filterdata()

        self.menu.close()

    def clear_all_col_filters(self):
        # show all rows
        for i in range(self.rowCount()):
            self.setRowHidden(i, False)

        # remove filter decorator in column header
        for i in range(self.columnCount()):
            self.showColFilterDecorator(False)

    def filterdata(self):

        columnsShow = dict([(i, True) for i in range(self.rowCount())])

        try:
            for i in range(self.rowCount()):
                for j in range(self.columnCount()):
                    item = self.item(i, j)
                    if j in self.unique_visible_values_by_col:
                        if item.text() not in self.unique_visible_values_by_col[j]:
                            columnsShow[i] = False
            for key, value in columnsShow.items():
                self.setRowHidden(key, not value)

        except Exception:
            log.error(traceback.format_exc())

    def showColFilterDecorator(self, should_show):
        if should_show:
            it = self.horizontalHeaderItem(self.col)
            oldHeader = it.text()
            newHeader = oldHeader + "*"
            it.setText(newHeader)
        else:
            it = self.horizontalHeaderItem(self.col)
            oldHeader = it.text()
            newHeader = re.sub('[*+]', '', oldHeader)
            it.setText(newHeader)


class MatchDetailsDialogBase(TableBasedDialog):

    def __init__(self, parent):
        self.response_results = []
        super().__init__(parent)

    def create_table_obj(self):
        return MatchResultTable(self)

    def set_acoustid_lookup_url_edit(self, p_acoustid_lookup_url):
        if p_acoustid_lookup_url is not None:
            self.acoustid_lookup_url.setText(_('<a href="{url:s}">Click to see AcoustId Fingerprint Lookup in browser</a>').format(url=p_acoustid_lookup_url))
        else:
            self.acoustid_lookup_url.hide()

    def set_input_filename_lbl(self, p_filename):
        self.input_filename_lbl.setText("Input File: " + p_filename)

    def get_value_for_row_id(self, row, value):
        return value

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

        self.tip_widget = QtWidgets.QWidget(self)
        self.tip_lbl = QtWidgets.QLabel(self.tip_widget)
        self.tip_lbl.setText(_("Tip: Column header left click to sort, right click to filter"))
        self.tip_lbl.setMargin(10)
        self.verticalLayout.addWidget(self.tip_lbl)

        self.center_widget = QtWidgets.QWidget(self)
        self.center_widget.setObjectName("center_widget")
        self.center_layout = QtWidgets.QVBoxLayout(self.center_widget)
        self.center_layout.setObjectName("center_layout")
        self.center_layout.setContentsMargins(1, 1, 1, 1)
        self.center_widget.setLayout(self.center_layout)
        self.verticalLayout.addWidget(self.center_widget)

        self.acoustid_lookup_url_widget = QtWidgets.QWidget(self)
        self.acoustid_lookup_url = QtWidgets.QLabel(self.acoustid_lookup_url_widget)
        self.acoustid_lookup_url.setOpenExternalLinks(True)
        self.verticalLayout.addWidget(self.acoustid_lookup_url)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.export_button = QtWidgets.QPushButton("Export Results", self.buttonBox)
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

    # Override
    def show_table(self, selected_row_nbr=-1, sort_column=None, sort_order=QtCore.Qt.DescendingOrder):
        self.add_widget_to_center_layout(self.table)
        self.table.selectRow(selected_row_nbr)
        self.table.setCurrentCell(selected_row_nbr, 0)
        self.table.horizontalHeader().setSortIndicatorShown(self.sorting_enabled)
        self.table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter | QtCore.Qt.TextWordWrap)

        # sort
        self.table.setSortingEnabled(self.sorting_enabled)
        if self.sorting_enabled and sort_column:
            self.table.sortItems(self.colpos(sort_column), sort_order)

        # Hide debug cols. using first char of label to mark it private
        should_hide_debug_cols = not config.setting['show_debug_col_in_match_dialog']
        for i in range(self.table.columnCount()):
            is_debug_col = self.table.horizontalHeaderItem(i).text().startswith('_')
            hide_this_col = is_debug_col and should_hide_debug_cols
            self.table.setColumnHidden(i, hide_this_col)

        # if no selection then select top row after sorting, that would be top similarity
        if selected_row_nbr == -1:
            self.table.selectRow(0)
            self.table.setCurrentCell(0, 0)

        self.table.setFocus()
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def export_data(self):
        self.export_match_dtl_entries_to_file()

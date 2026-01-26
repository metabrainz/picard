# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025-2026 Bob Swift
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

from picard.config import get_config
from picard.i18n import _
from picard.metadata import (
    album_metadata_processors,
    track_metadata_processors,
)
from picard.plugin import PluginInformation


try:
    from markdown import markdown  # type: ignore[unresolved-import]
except ImportError:
    markdown = None


from picard.ui import PicardDialog
from picard.ui.widgets.orderabletableview import OrderableTableView


class PluginOrderSelectorDialog(PicardDialog):
    help_url = '/config/options_plugin_execution_order.html'

    def __init__(self, parent=None):
        """Display dialog box to select the metadata processing plugins execution order.

        Args:
            parent ([type], optional): Parent of the QDialog object being created. Defaults to None.
        """
        super().__init__(parent)
        config = get_config()
        self.plugin_exec_order = dict(config.setting['plugins3_exec_order'])
        self.updating = False
        self._make_plugin_list()

        self.setWindowTitle(_("Plugin Execution Order"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setMinimumWidth(650)
        self._layout = QtWidgets.QVBoxLayout(self)

        instructions = QtWidgets.QLabel(
            _(
                "This displays the order in which the plugin metadata processing functions are executed "
                "by Picard. You can change the order by moving the functions up or down by selecting "
                "the function to move and then use the up or down button, or by using your mouse to "
                "drag the function to the desired location in the list."
            )
        )
        instructions.setWordWrap(True)
        self._layout.addWidget(instructions)

        self.table_layout = QtWidgets.QHBoxLayout()

        self.tableview = OrderableTableView(self)
        self.tableview.setAlternatingRowColors(True)

        self.tableview._model.setHorizontalHeaderLabels(
            [
                _('Plugin Name'),
                _('Processor'),
                _('Method/Function Called'),
            ]
        )

        for idx, width in enumerate([260, 70, 260]):
            self.tableview.setColumnWidth(idx, width)

        for idx, text in enumerate(
            [
                _("The name of the plugin"),
                _("The type of metadata processor used (album or track)"),
                _("The method or function within the plugin module that is called"),
            ]
        ):
            self.tableview._model.horizontalHeaderItem(idx).setToolTip(text)

        self.tableview.selectionModel().selectionChanged.connect(self._set_up_down_button_states)

        self.button_layout = QtWidgets.QVBoxLayout()

        # spacers
        self.spacer1 = QtWidgets.QSpacerItem(
            0, 10, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.spacer2 = QtWidgets.QSpacerItem(
            0, 10, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )

        # Up button
        self.up_button = QtWidgets.QToolButton()
        up_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarShadeButton)
        self.up_button.setIcon(up_icon)
        self.up_button.setToolTip(_("Move selected plugin up"))
        self.up_button.clicked.connect(self.tableview.move_row_up)

        # Down button
        self.dn_button = QtWidgets.QToolButton()
        dn_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarUnshadeButton)
        self.dn_button.setIcon(dn_icon)
        self.dn_button.setToolTip(_("Move selected plugin down"))
        self.dn_button.clicked.connect(self.tableview.move_row_down)

        self.button_layout.addItem(self.spacer1)
        self.button_layout.addWidget(self.up_button)
        self.button_layout.addWidget(self.dn_button)
        self.button_layout.addItem(self.spacer2)

        self.table_layout.addWidget(self.tableview)
        self.table_layout.addLayout(self.button_layout)

        self._layout.addLayout(self.table_layout)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Help)
        self.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.button_reset = QtWidgets.QDialogButtonBox.StandardButton.Reset
        self.buttonbox.addButton(self.button_reset)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.show_help)
        self.buttonbox.button(self.button_reset).clicked.connect(self._reset_priorities)

        self._layout.addWidget(self.buttonbox)

        self._update_table()

    def _make_plugin_list(self):
        self.plugins = []
        for processor in [album_metadata_processors, track_metadata_processors]:
            for info in processor.get_plugin_function_information(self.plugin_exec_order):
                self.plugins.append(info)

    def _update_table(self):
        self.updating = True
        rows = self.tableview._model.rowCount()
        self.tableview._model.removeRows(0, rows)

        for plugin in sorted(self.plugins, key=lambda i: i.priority, reverse=True):
            plugin: PluginInformation
            column1 = QtGui.QStandardItem(plugin.plugin_name)
            column1.setEditable(False)
            column1.setDropEnabled(False)
            text = markdown(plugin.plugin_description) if markdown else plugin.plugin_description
            column1.setToolTip(text)
            column1.setData(plugin.key, QtCore.Qt.ItemDataRole.UserRole)

            column2 = QtGui.QStandardItem(plugin.processor)
            column2.setEditable(False)
            column2.setDropEnabled(False)
            column2.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            column3 = QtGui.QStandardItem(plugin.function_name)
            column3.setEditable(False)
            column3.setDropEnabled(False)
            text = markdown(plugin.function_description) if markdown else plugin.function_description
            column3.setToolTip(text)

            self.tableview._model.appendRow([column1, column2, column3])

        self.tableview.setCurrentIndex(self.tableview._model.index(0, 0))
        self.updating = False
        self._set_up_down_button_states()

    def _set_up_down_button_states(self):
        if self.updating:
            return
        row = self.tableview.currentIndex().row()
        self.up_button.setDisabled(row < 1)
        self.dn_button.setDisabled(row >= self.tableview._model.rowCount() - 1)

    def _reset_priorities(self):
        button = QtWidgets.QMessageBox.warning(
            self,
            _("Confirm Reset"),
            _("Are you sure you want to reset the execution order to the plugin defaults?"),
            buttons=QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            defaultButton=QtWidgets.QMessageBox.StandardButton.No,
        )

        if button == QtWidgets.QMessageBox.StandardButton.Yes:
            self.plugin_exec_order = dict()
            self._make_plugin_list()
            self._update_table()

    def get_updated_order(self):
        config = get_config()
        plugin_exec_order = dict(config.setting['plugins3_exec_order'])
        for idx in range(self.tableview._model.rowCount()):
            item = self.tableview._model.item(idx, 0)
            key = item.data(QtCore.Qt.ItemDataRole.UserRole)
            priority = -1 - idx
            plugin_exec_order[key] = priority
        return plugin_exec_order


def display_plugin_order_selector(**kwargs):
    dialog = PluginOrderSelectorDialog(**kwargs)
    result = dialog.exec()
    return (dialog.get_updated_order(), result == QtWidgets.QDialog.DialogCode.Accepted)

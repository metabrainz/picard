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


from collections import namedtuple

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.ui import PicardDialog
from picard.ui.util import StandardButton
from picard.ui.widgets.orderabletableview import OrderableTableView


PluginInformation = namedtuple('PluginInformation', ['key', 'name', 'description', 'function_description', 'priority'])


class PluginOrderSelectorDialog(PicardDialog):
    help_url = 'options_plugin_execution_order'

    def __init__(
        self, parent=None, plugins=None
    ):
        """Display dialog box to select the metadata processing plugins execution order.

        Args:
            parent ([type], optional): Parent of the QDialog object being created. Defaults to None.
            plugins (list, optional): List of plugin items to order. Defaults to None.
        """
        super().__init__(parent)
        self.plugins = plugins or []
        self.plugin_exec_order = dict()

        self.setWindowTitle(_("Plugin Metadata Processing Order"))
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setMinimumWidth(650)
        self.layout = QtWidgets.QVBoxLayout(self)

        instructions = QtWidgets.QLabel(
            _(
                "This displays the order in which the plugin metadata processing functions are executed "
                "by Picard. You can change the order by moving the functions up or down by selecting "
                "the funcion to move and then use the up or down button, or by using your mouse to "
                "drag the function to the desired location in the list."
            )
        )
        instructions.setWordWrap(True)
        self.layout.addWidget(instructions)

        self.table_layout = QtWidgets.QHBoxLayout()

        self.tableview = OrderableTableView(self)

        self.tableview.model.setHorizontalHeaderLabels(
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
            self.tableview.model.horizontalHeaderItem(idx).setToolTip(text)

        for plugin in sorted(self.plugins, key=lambda i: i.priority, reverse=True):
            plugin: PluginInformation
            _module_name, processor_type, function_name = plugin.key.split(':', 2)

            column1 = QtGui.QStandardItem(plugin.name)
            column1.setEditable(False)
            column1.setDropEnabled(False)
            column1.setToolTip(plugin.description)
            column1.setData(plugin.key, QtCore.Qt.ItemDataRole.UserRole)

            column2 = QtGui.QStandardItem(processor_type)
            column2.setEditable(False)
            column2.setDropEnabled(False)
            column2.setTextAlignment(QtCore.Qt.AlignCenter)

            column3 = QtGui.QStandardItem(function_name)
            column3.setEditable(False)
            column3.setDropEnabled(False)
            column3.setToolTip(plugin.function_description)

            self.tableview.model.appendRow([column1, column2, column3])

        self.tableview.setCurrentIndex(self.tableview.model.index(0, 0))

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

        self.layout.addLayout(self.table_layout)

        self.buttonbox = QtWidgets.QDialogButtonBox(self)
        self.buttonbox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonbox.addButton(
            StandardButton(StandardButton.OK), QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.buttonbox.addButton(StandardButton(StandardButton.CANCEL),
                                 QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)

        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        self.buttonbox.helpRequested.connect(self.show_help)

        self.layout.addWidget(self.buttonbox)

        self._set_up_down_button_states()

    def _set_up_down_button_states(self):
        row = self.tableview.currentIndex().row()
        self.up_button.setDisabled(row < 1)
        self.dn_button.setDisabled(row >= self.tableview.model.rowCount() - 1)

    def get_updated_order(self):
        plugin_exec_order = dict()
        for idx in range(self.tableview.model.rowCount()):
            item = self.tableview.model.item(idx, 0)
            key = item.data(QtCore.Qt.ItemDataRole.UserRole)
            priority = -1 - idx
            plugin_exec_order[key] = priority
        return plugin_exec_order


def display_plugin_order_selector(**kwargs):
    dialog = PluginOrderSelectorDialog(**kwargs)
    result = dialog.exec_()
    return (dialog.get_updated_order(), result == QtWidgets.QDialog.DialogCode.Accepted)

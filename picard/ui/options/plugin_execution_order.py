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
import sys

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.config import (
    Option,
    get_config,
)
from picard.metadata import (
    _album_metadata_processors,
    _track_metadata_processors,
)
from picard.plugin import EXEC_ORDER_KEY

from markdown import markdown

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_plugin_execution_order import (
    Ui_PluginExecutionOrderOptionsPage,
)
from picard.ui.widgets.orderabletableview import OrderableTableView


PluginInformation = namedtuple('PluginInformation', ['key', 'name', 'description', 'function_description', 'priority'])


class PluginExecutionOrderOptionsPage(OptionsPage):

    NAME = 'plugin_execution_order'
    TITLE = N_("Plugin Execution Order")
    PARENT = 'advanced'
    SORT_ORDER = 50
    ACTIVE = True
    HELP_URL = "/config/options_plugin_execution_order.html"

    options = [
        Option.add_if_missing('setting', EXEC_ORDER_KEY, dict()),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PluginExecutionOrderOptionsPage()
        self.ui.setupUi(self)

        self.title_text = N_("Plugin Metadata Processing Order")

        self.ui.description.setText(_(
            "Each plugin that works with an album or track's metadata has their various processing "
            "functions registered with an execution priority set by the plugin author within the "
            "plugin itself. A plugin may contain multiple different processing functions, each with "
            "its own specified priority. These priorities determine the order in which the functions "
            "are executed, and are generally set as HIGH, NORMAL or LOW.\n\n"
            "Most of the time this grouping of execution priorities is sufficient, however there may be "
            "a situation where one plugin processing function must be executed before another plugin "
            "function with the same priority in order to avoid unintended results. This option setting "
            "allows you to specify the order that the plugin metadata processing functions are executed, "
            "regardless of the initial registered priority for the function. In this way, you can avoid "
            "unexpected results that might otherwise occur.\n\n"
            "When the execution order editor is opened, it will display all of the enabled plugin "
            "metadata processing functions in the order in which they are executed by Picard. You can "
            "change the order by moving the plugin processing functions up or down by selecting the "
            "function to move and then use the up or down button, or by using your mouse to drag the "
            "function to the desired location in the list.\n\n"
            "Hovering your cursor over a plugin's name will display a description of the function, and "
            "hovering over a plugin's processing function will display a description of the function "
            "if available."
        ))

        self.ui.edit_plugin_order.clicked.connect(self.show_execution_order_editor)

        self.setup_editor_dialog()

    def setup_editor_dialog(self):
        self.order_dialog = QtWidgets.QDialog(self)
        self.order_dialog.setWindowTitle(_(self.title_text))
        self.order_dialog.setMinimumWidth(650)

        layout = QtWidgets.QVBoxLayout(self.order_dialog)

        instructions = QtWidgets.QLabel(
            _(
                "This displays the order in which the plugin metadata processing functions are executed "
                "by Picard. You can change the order by moving the functions up or down by selecting "
                "the funcion to move and then use the up or down button, or by using your mouse to "
                "drag the function to the desired location in the list."
            )
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.tableview = OrderableTableView(self.order_dialog)

        self.tableview.model.setHorizontalHeaderLabels(
            [
                _('Plugin Name'),
                _('Processor'),
                _('Method/Function Called'),
            ]
        )

        for idx, width in enumerate([260, 70, 230]):
            self.tableview.setColumnWidth(idx, width)

        for idx, text in enumerate(
            [
                _("The name of the plugin"),
                _("The type of metadata processor used (album or track)"),
                _("The method or function within the plugin module that is called"),
            ]
        ):
            self.tableview.model.horizontalHeaderItem(idx).setToolTip(text)

        self.tableview.selectionModel().selectionChanged.connect(self._set_up_down_button_states)
        layout.addWidget(self.tableview)

        button_layout = QtWidgets.QHBoxLayout()

        # Move Label
        move_label = QtWidgets.QLabel(_("Move row"))
        button_layout.addWidget(move_label)

        # Up button
        self.up_button = QtWidgets.QToolButton()
        up_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarShadeButton)
        self.up_button.setIcon(up_icon)
        self.up_button.setToolTip(_("Move selected plugin up"))
        self.up_button.clicked.connect(self.tableview.move_row_up)
        button_layout.addWidget(self.up_button)

        # Down button
        self.dn_button = QtWidgets.QToolButton()
        dn_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarUnshadeButton)
        self.dn_button.setIcon(dn_icon)
        self.dn_button.setToolTip(_("Move selected plugin down"))
        self.dn_button.clicked.connect(self.tableview.move_row_down)
        button_layout.addWidget(self.dn_button)

        # spacer
        spacer = QtWidgets.QSpacerItem(
            20, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum
        )
        button_layout.addItem(spacer)

        # OK
        ok_button = QtWidgets.QPushButton(_('OK'))
        ok_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOkButton)
        ok_button.setIcon(ok_icon)
        ok_button.clicked.connect(self.order_dialog.accept)
        button_layout.addWidget(ok_button)
        ok_button.setDefault(True)  # default selected button

        # Cancel
        cancel_button = QtWidgets.QPushButton(_('Cancel'))
        cancel_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton)
        cancel_button.setIcon(cancel_icon)
        cancel_button.clicked.connect(self.order_dialog.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def load(self):
        config = get_config()
        self.plugin_exec_order = config.setting[EXEC_ORDER_KEY]

    def save(self):
        config = get_config()
        config.setting[EXEC_ORDER_KEY] = self.plugin_exec_order

    def show_execution_order_editor(self):
        "Open a dialog to allow the user to manually set the execution order of metadata processor plugins"

        # Get list of all registered metadata processor plugins
        plugins = []
        for processor in [_album_metadata_processors, _track_metadata_processors]:
            for (priority, function, key) in processor.get_exec_order():
                function_desc = function.__doc__ or "No description provided"
                module_name = key.split(':')[0]
                # Don't include internal plugins
                if module_name.startswith('picard.'):
                    continue
                module_name = 'picard.plugins.' + module_name
                if module_name in sys.modules:
                    name = getattr(sys.modules[module_name], 'PLUGIN_NAME', "No name provided")
                    module_desc = getattr(sys.modules[module_name], 'PLUGIN_DESCRIPTION', "No description provided")
                else:
                    name = module_desc = "Unknown Plugin"
                plugins.append(PluginInformation(key, name, markdown(module_desc), markdown(function_desc), priority))

        if not plugins:
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText(_("There were no installed metadata processing plugins found."))
            msg.setWindowTitle(_(self.title_text))
            msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.show()

            return

        self.tableview.blockSignals(True)
        i = self.tableview.model.rowCount()
        while i > 0:
            i -= 1
            self.tableview.model.removeRow(i)

        for plugin in sorted(plugins, key=lambda i: i.priority, reverse=True):
            plugin: PluginInformation
            module_name, processor_type, function_name = plugin.key.split(':', 2)

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
        self.tableview.blockSignals(False)

        self._set_up_down_button_states()

        # Show dialog and process result
        if self.order_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.plugin_exec_order = dict()
            for idx in range(self.tableview.model.rowCount()):
                item = self.tableview.model.item(idx, 0)
                key = item.data(QtCore.Qt.ItemDataRole.UserRole)
                priority = -1 - idx
                self.plugin_exec_order[key] = priority

    def _set_up_down_button_states(self):
        row = self.tableview.currentIndex().row()
        self.up_button.setDisabled(row < 1)
        self.dn_button.setDisabled(row >= self.tableview.model.rowCount() - 1)


register_options_page(PluginExecutionOrderOptionsPage)

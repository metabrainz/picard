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


import sys

from PyQt5 import (
    QtCore,
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
from picard.ui.plugin_order_selector import (
    PluginInformation,
    display_plugin_order_selector,
)
from picard.ui.ui_options_plugin_execution_order import (
    Ui_PluginExecutionOrderOptionsPage,
)


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
            msg.setWindowTitle(_("No Data"))
            msg.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.show()

            return

        new_order, return_state = display_plugin_order_selector(parent=self, plugins=plugins)
        if return_state:
            self.plugin_exec_order = new_order


register_options_page(PluginExecutionOrderOptionsPage)

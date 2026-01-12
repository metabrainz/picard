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
    QtWidgets,
)

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    _,
)
from picard.metadata import (
    album_metadata_processors,
    track_metadata_processors,
)

from picard.ui.forms.ui_options_plugin_execution_order import (
    Ui_PluginExecutionOrderOptionsPage,
)
from picard.ui.options import OptionsPage
from picard.ui.plugin_order_selector import display_plugin_order_selector


class PluginExecutionOrderOptionsPage(OptionsPage):
    NAME = 'plugin_execution_order'
    TITLE = N_("Plugin Execution Order")
    PARENT = 'advanced'
    SORT_ORDER = 50
    ACTIVE = True
    HELP_URL = "/config/options_plugin_execution_order.html"

    OPTIONS = (('plugins3_exec_order', []),)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PluginExecutionOrderOptionsPage()
        self.ui.setupUi(self)

        self.title_text = N_("Plugin Metadata Processing Order")

        self.ui.description.setText(
            _(
                "Each plugin that works with an album or track's metadata has their various processing "
                "functions registered with an execution priority set by the plugin author within the "
                "plugin itself. A plugin may contain multiple different processing functions, each with "
                "its own specified priority. These priorities determine the order in which the functions "
                "are executed, and are generally set as high, normal or low.\n\n"
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
            )
        )

        self.ui.edit_plugin_order.clicked.connect(self.show_execution_order_editor)

    def load(self):
        config = get_config()
        self.plugin_exec_order = config.setting['plugins3_exec_order']

    def save(self):
        config = get_config()
        config.setting['plugins3_exec_order'] = self.plugin_exec_order

    def show_execution_order_editor(self):
        "Open a dialog to allow the user to manually set the execution order of metadata processor plugins"

        # Get list of all registered metadata processor plugins
        plugins = []
        for processor in [album_metadata_processors, track_metadata_processors]:
            for info in processor.get_plugin_function_information():
                plugins.append(info)

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

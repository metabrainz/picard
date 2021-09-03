# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
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
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    get_config,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_maintenance import Ui_MaintenanceOptionsPage


class MaintenanceOptionsPage(OptionsPage):

    NAME = "maintenance"
    TITLE = N_("Maintenance")
    PARENT = "advanced"
    SORT_ORDER = 99
    ACTIVE = True
    HELP_URL = '/config/options_maintenance.html'

    options = []

    INSTRUCTIONS = N_(
        "This allows you to remove unused option settings from the configuration INI file.\n\n"
        "Settings that are found in the configuration file that do not appear on any option "
        "settings page will be listed below. If your configuration file does not contain any "
        "unused option settings, then the list will be empty and the removal checkbox will be "
        "disabled.\n\n"
        "Note that unused option settings could come from plugins that have been uninstalled, "
        "so please be careful to not remove settings that you may want to use later when "
        "the plugin is reinstalled. Options belonging to plugins that are installed but "
        "currently disabled will not be listed for possible removal.\n\n"
        "To remove one or more settings, first enable the removal by checking the \"Remove "
        "selected options\" box. You can then select the settings to remove by checking the "
        "box next to the setting. When you choose \"Make It So!\" to save your option "
        "settings, the selected items will be removed."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MaintenanceOptionsPage()
        self.ui.setupUi(self)
        self.ui.description.setText(_(self.INSTRUCTIONS))
        self.ui.tableWidget.setHorizontalHeaderLabels([_("Option"), _("Value")])
        self.ui.select_all.stateChanged.connect(self.select_all_changed)
        self.ui.enable_cleanup.stateChanged.connect(self.enable_cleanup_changed)

    def load(self):
        config = get_config()

        # Setting options from all option pages and loaded plugins (including plugins currently disabled).
        key_options = set(config.setting.as_dict())

        # Combine all page and plugin settings with required options not appearing in option pages.
        current_options = set([
            # Include options that are required but are not entered directly from the options pages.
            'file_renaming_scripts',
            'selected_file_naming_script_id',
            'log_verbosity',
            # Items missed if TagsCompatibilityWaveOptionsPage does not register.
            'remove_wave_riff_info',
            'wave_riff_info_encoding',
            'write_wave_riff_info',
        ]).union(key_options)

        # All setting options included in the INI file.
        config.beginGroup("setting")
        file_options = set(config.childKeys())
        config.endGroup()

        orphan_options = file_options.difference(current_options)

        self.ui.description.setText(
            _(self.INSTRUCTIONS)
            + _("\n\nThe configuration file currently contains %d option settings, %d which are unused.") % (
                len(file_options),
                len(orphan_options)
            )
        )
        self.ui.enable_cleanup.setChecked(False)
        self.ui.tableWidget.clearContents()
        self.ui.tableWidget.setRowCount(len(orphan_options))
        for row, option_name in enumerate(sorted(orphan_options)):
            tableitem = QtWidgets.QTableWidgetItem(option_name)
            tableitem.setData(QtCore.Qt.UserRole, option_name)
            tableitem.setFlags(tableitem.flags() | QtCore.Qt.ItemIsUserCheckable)
            tableitem.setCheckState(False)
            self.ui.tableWidget.setItem(row, 0, tableitem)
            tableitem = QtWidgets.QTextEdit()
            tableitem.setFrameStyle(QtWidgets.QFrame.NoFrame)
            text = self.make_setting_value_text(option_name)
            tableitem.setPlainText(text)
            tableitem.setReadOnly(True)
            # Adjust row height to reasonably accommodate values with more than one line, with a minimum
            # height of 25 pixels.  Long line or multi-line values will be expanded to display up to 5
            # lines, assuming a standard line height of 18 pixels.  Long lines are defined as having over
            # 50 characters.
            text_rows = max(text.count("\n") + 1, int(len(text) / 50))
            row_height = max(25, 18 * min(5, text_rows))
            self.ui.tableWidget.setRowHeight(row, row_height)
            self.ui.tableWidget.setCellWidget(row, 1, tableitem)
        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.select_all.setCheckState(False)
        if not len(orphan_options):
            self.ui.select_all.setEnabled(False)
        self.enable_cleanup_changed()

    def column_items(self, column):
        for idx in range(self.ui.tableWidget.rowCount()):
            yield self.ui.tableWidget.item(idx, column)

    def selected_options(self):
        for item in self.column_items(0):
            if item.checkState() == QtCore.Qt.Checked:
                yield item.data(QtCore.Qt.UserRole)

    def select_all_changed(self):
        state = self.ui.select_all.checkState()
        for item in self.column_items(0):
            item.setCheckState(state)

    def save(self):
        if not self.ui.enable_cleanup.checkState() == QtCore.Qt.Checked:
            return
        to_remove = set(self.selected_options())
        if to_remove and QtWidgets.QMessageBox.question(
            self,
            _('Confirm Remove'),
            _("Are you sure you want to remove the selected option settings?"),
        ) == QtWidgets.QMessageBox.Yes:
            config = get_config()
            for item in to_remove:
                Option.add_if_missing('setting', item, None)
                log.warning("Removing option setting '%s' from the INI file.", item)
                config.setting.remove(item)

    def make_setting_value_text(self, key):
        config = get_config()
        value = config.setting.raw_value(key)
        return repr(value)

    def enable_cleanup_changed(self):
        state = self.ui.enable_cleanup.checkState()
        self.ui.select_all.setEnabled(state)
        self.ui.tableWidget.setEnabled(state)


register_options_page(MaintenanceOptionsPage)

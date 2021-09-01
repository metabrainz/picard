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
from picard.plugin import _extension_points

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_maintenance import Ui_MaintenanceOptionsPage


class MaintenanceOptionsPage(OptionsPage):

    NAME = "maintenance"
    TITLE = N_("Maintenance")
    PARENT = None
    SORT_ORDER = 99
    ACTIVE = True
    HELP_URL = '/config/options_maintenance.html'

    options = []

    INSTRUCTIONS = N_(
        "This allows you to remove unused option settings from the configuration.\n\n"
        "Settings that are found in the configuration that do not appear on any option "
        "settings page will be listed below. If your configuration does not contain any "
        "unused option settings, then the list will be empty.\n\n"
        "Note that unused option settings could come from plugins that have been removed, "
        "so please be careful to not remove settings that you may want to use later when "
        "the plugin is reloaded.  Options belonging to plugins that are loaded but "
        "currently disabled will not be listed for possible removal.\n\n"
        "To remove one or more settings, select the settings to remove by checking the "
        "box next to the settings, and then enable the removal by checking the \"Remove "
        "selected options\" box. When you choose \"Make It So!\" to save your option "
        "settings, the selected items will be removed."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MaintenanceOptionsPage()
        self.ui.setupUi(self)
        self.ui.description.setText(_(self.INSTRUCTIONS))
        self.ui.tableWidget.setHorizontalHeaderLabels([_("Option"), _("Value")])
        self.ui.select_all.stateChanged.connect(self.select_all)

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

        # Add options from Option pages
        for ep in _extension_points:
            if ep.label != 'pages':
                continue
            for page in ep:
                if not hasattr(page, 'options'):
                    continue
                for option in page.options:
                    if option.section == "setting":
                        current_options.add(option.name)

        # All setting options included in the INI file.
        config.beginGroup("setting")
        file_options = set(config.childKeys())
        config.endGroup()

        orphan_options = file_options.difference(current_options)

        self.ui.description.setText(
            _(self.INSTRUCTIONS)
            + _("\n\nThe configuration file currently contains {0} option settings, {1} which are unused.").format(
                len(file_options),
                len(orphan_options)
            )
        )
        self.ui.enable_cleanup.setChecked(False)
        self.ui.tableWidget.clearContents()
        self.ui.tableWidget.setRowCount(len(orphan_options))
        for row, item in enumerate(sorted(orphan_options)):
            tableitem = QtWidgets.QTableWidgetItem(item)
            tableitem.setFlags(tableitem.flags() | QtCore.Qt.ItemIsUserCheckable)
            tableitem.setCheckState(False)
            self.ui.tableWidget.setItem(row, 0, tableitem)
            text = self.make_setting_value_text(item)
            tableitem = QtWidgets.QTextEdit()
            tableitem.setText(text)
            # Adjust row height to reasonably accommodate values with more than one line, with a minimum
            # height of 25 pixels.  Multi-line values will be expanded to display up to 5 lines, assuming
            # a standard line height of 18 pixels.
            row_height = max(25, 18 * min(5, text.count("\n") + 1))
            self.ui.tableWidget.setRowHeight(row, row_height)
            self.ui.tableWidget.setCellWidget(row, 1, tableitem)
        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.select_all.setCheckState(False)

    def save(self):
        if not self.ui.enable_cleanup.checkState() == QtCore.Qt.Checked:
            return
        to_remove = set()
        for idx in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(idx, 0)
            if item.checkState() == QtCore.Qt.Checked:
                to_remove.add(item.text())
        if to_remove and QtWidgets.QMessageBox.question(
            self,
            _('Confirm Remove'),
            _("Are you sure you want to remove the {0} selected option settings?").format(len(to_remove)),
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        ) == QtWidgets.QMessageBox.Yes:
            config = get_config()
            for item in to_remove:
                Option.add_if_missing('setting', item, None)
                log.warning("Removing option setting '%s' from the INI file.", item)
                config.setting.remove(item)

    def make_setting_value_text(self, key):
        NONE_TEXT = _("None")
        config = get_config()
        value = config.setting.raw_value(key)
        if value is None:
            return NONE_TEXT
        if isinstance(value, str):
            return '"%s"' % value
        if type(value) in {bool, int, float}:
            return str(value)
        if type(value) in {set, tuple, list, dict}:
            text = _("List of %i items:") % len(value)
            if isinstance(value, dict):
                for item in value.items():
                    text += "\n{0}".format(item)
            else:
                for item in value:
                    text += '\n"{0}"'.format(item)
            return text
        return _("Unknown value format")

    def select_all(self):
        state = self.ui.select_all.checkState()
        for idx in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(idx, 0)
            item.setCheckState(state)


register_options_page(MaintenanceOptionsPage)

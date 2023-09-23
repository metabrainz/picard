# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2022 Bob Swift
# Copyright (C) 2021-2022 Laurent Monin
# Copyright (C) 2021-2023 Philipp Wolfer
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


import datetime
from os import path

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    get_config,
    load_new_config,
)
from picard.config_upgrade import upgrade_config
from picard.util import open_local_path

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_maintenance import Ui_MaintenanceOptionsPage


OPTIONS_NOT_IN_PAGES = {
    # Include options that are required but are not entered directly from the options pages.
    'file_renaming_scripts',
    'selected_file_naming_script_id',
    'log_verbosity',
    # Items missed if TagsCompatibilityWaveOptionsPage does not register.
    'remove_wave_riff_info',
    'wave_riff_info_encoding',
    'write_wave_riff_info',
}


class MaintenanceOptionsPage(OptionsPage):

    NAME = 'maintenance'
    TITLE = N_("Maintenance")
    PARENT = 'advanced'
    SORT_ORDER = 99
    ACTIVE = True
    HELP_URL = "/config/options_maintenance.html"

    options = []

    signal_reload = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MaintenanceOptionsPage()
        self.ui.setupUi(self)
        self.ui.description.setText(_(
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
        ))
        self.ui.tableWidget.setHorizontalHeaderLabels([_("Option"), _("Value")])
        self.ui.select_all.stateChanged.connect(self.select_all_changed)
        self.ui.enable_cleanup.stateChanged.connect(self.enable_cleanup_changed)
        self.ui.open_folder_button.clicked.connect(self.open_config_dir)
        self.ui.save_backup_button.clicked.connect(self.save_backup)
        self.ui.load_backup_button.clicked.connect(self.load_backup)

        # Set the palette of the config file QLineEdit widget to inactive.
        palette_normal = self.ui.config_file.palette()
        palette_readonly = QtGui.QPalette(palette_normal)
        disabled_color = palette_normal.color(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Window)
        palette_readonly.setColor(QtGui.QPalette.ColorRole.Base, disabled_color)
        self.ui.config_file.setPalette(palette_readonly)

    def load(self):
        config = get_config()

        # Show the path and file name of the currently used configuration file.
        self.ui.config_file.setText(config.fileName())

        # Setting options from all option pages and loaded plugins (including plugins currently disabled).
        key_options = set(config.setting.as_dict())

        # Combine all page and plugin settings with required options not appearing in option pages.
        current_options = OPTIONS_NOT_IN_PAGES.union(key_options)

        # All setting options included in the INI file.
        config.beginGroup('setting')
        file_options = set(config.childKeys())
        config.endGroup()

        orphan_options = file_options.difference(current_options)

        self.ui.option_counts.setText(
            _("The configuration file currently contains %(totalcount)d option "
              "settings, %(unusedcount)d which are unused.") % {
                'totalcount': len(file_options),
                'unusedcount': len(orphan_options),
            })
        self.ui.enable_cleanup.setChecked(False)
        self.ui.tableWidget.clearContents()
        self.ui.tableWidget.setRowCount(len(orphan_options))
        for row, option_name in enumerate(sorted(orphan_options)):
            tableitem = QtWidgets.QTableWidgetItem(option_name)
            tableitem.setData(QtCore.Qt.ItemDataRole.UserRole, option_name)
            tableitem.setFlags(tableitem.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            tableitem.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.ui.tableWidget.setItem(row, 0, tableitem)
            tableitem = QtWidgets.QTextEdit()
            tableitem.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
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
        self.ui.select_all.setCheckState(QtCore.Qt.CheckState.Unchecked)
        if not len(orphan_options):
            self.ui.select_all.setEnabled(False)
        self.enable_cleanup_changed()

    def open_config_dir(self):
        config = get_config()
        config_dir = path.split(config.fileName())[0]
        open_local_path(config_dir)

    def _get_dialog_filetypes(self, _ext='.ini'):
        return ";;".join((
            _("Configuration files") + " (*{0})".format(_ext,),
            _("All files") + " (*)",
        ))

    def _make_backup_filename(self, auto=False):
        config = get_config()
        _filename = path.split(config.fileName())[1]
        _root, _ext = path.splitext(_filename)
        return "{0}_{1}_Backup_{2}{3}".format(
            _root,
            'Auto' if auto else 'User',
            datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            _ext,
        )

    def _backup_error(self, dialog_title=None):
        if not dialog_title:
            dialog_title = _("Backup Configuration File")
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Critical,
            dialog_title,
            _("There was a problem backing up the configuration file. Please see the logs for more details."),
            QtWidgets.QMessageBox.StandardButton.Ok,
            self
        )
        dialog.exec_()

    def save_backup(self):
        config = get_config()
        directory = path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))
        filename = self._make_backup_filename()
        ext = path.splitext(filename)[1]
        default_path = path.normpath(path.join(directory, filename))

        dialog_title = _("Backup Configuration File")
        dialog_file_types = self._get_dialog_filetypes(ext)
        options = QtWidgets.QFileDialog.Options()
        filename, file_type = QtWidgets.QFileDialog.getSaveFileName(self, dialog_title, default_path, dialog_file_types, options=options)
        if not filename:
            return
        # Fix issue where Qt may set the extension twice
        (name, ext) = path.splitext(filename)
        if ext and str(name).endswith('.' + ext):
            filename = name

        if config.save_user_backup(filename):
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Information,
                dialog_title,
                _("Configuration successfully backed up to %s") % filename,
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            )
            dialog.exec_()
        else:
            self._backup_error(dialog_title)

    def load_backup(self):
        dialog_title = _("Load Backup Configuration File")
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning,
            dialog_title,
            _("Loading a backup configuration file will replace the current configuration settings. "
            "A backup copy of the current file will be saved automatically.\n\nDo you want to continue?"),
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
            self
        )
        dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
        if not dialog.exec_() == QtWidgets.QMessageBox.StandardButton.Ok:
            return

        config = get_config()
        directory = path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))
        filename = path.join(directory, self._make_backup_filename(auto=True))
        if not config.save_user_backup(filename):
            self._backup_error()
            return

        ext = path.splitext(filename)[1]
        dialog_file_types = self._get_dialog_filetypes(ext)
        directory = path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))
        options = QtWidgets.QFileDialog.Options()
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(self, dialog_title, directory, dialog_file_types, options=options)
        if not filename:
            return
        log.warning("Loading configuration from %s", filename)
        if load_new_config(filename):
            config = get_config()
            upgrade_config(config)
            QtCore.QObject.config = get_config()
            self.signal_reload.emit()
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Information,
                dialog_title,
                _("Configuration successfully loaded from %s") % filename,
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            )
        else:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Critical,
                dialog_title,
                _("There was a problem restoring the configuration file. Please see the logs for more details."),
                QtWidgets.QMessageBox.StandardButton.Ok,
                self
            )
        dialog.exec_()

    def column_items(self, column):
        for idx in range(self.ui.tableWidget.rowCount()):
            yield self.ui.tableWidget.item(idx, column)

    def selected_options(self):
        for item in self.column_items(0):
            if item.checkState() == QtCore.Qt.CheckState.Checked:
                yield item.data(QtCore.Qt.ItemDataRole.UserRole)

    def select_all_changed(self):
        state = self.ui.select_all.checkState()
        for item in self.column_items(0):
            item.setCheckState(state)

    def save(self):
        if not self.ui.enable_cleanup.checkState() == QtCore.Qt.CheckState.Checked:
            return
        to_remove = set(self.selected_options())
        if to_remove and QtWidgets.QMessageBox.question(
            self,
            _("Confirm Remove"),
            _("Are you sure you want to remove the selected option settings?"),
        ) == QtWidgets.QMessageBox.StandardButton.Yes:
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
        state = self.ui.enable_cleanup.checkState() == QtCore.Qt.CheckState.Checked
        self.ui.select_all.setEnabled(state)
        self.ui.tableWidget.setEnabled(state)


register_options_page(MaintenanceOptionsPage)

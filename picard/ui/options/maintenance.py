# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021-2022, 2024 Bob Swift
# Copyright (C) 2021-2023 Philipp Wolfer
# Copyright (C) 2021-2024 Laurent Monin
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
import os

from PyQt6 import (
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
from picard.const.defaults import DEFAULT_AUTOBACKUP_DIRECTORY
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import open_local_path

from picard.ui.forms.ui_options_maintenance import Ui_MaintenanceOptionsPage
from picard.ui.options import OptionsPage


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


def _safe_autobackup_dir(path):
    if not path or not os.path.isdir(path):
        return DEFAULT_AUTOBACKUP_DIRECTORY
    return os.path.normpath(path)


class MaintenanceOptionsPage(OptionsPage):

    NAME = 'maintenance'
    TITLE = N_("Maintenance")
    PARENT = 'advanced'
    SORT_ORDER = 99
    ACTIVE = True
    HELP_URL = "/config/options_maintenance.html"

    signal_reload = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_MaintenanceOptionsPage()
        self.ui.setupUi(self)
        self.ui.description.setText(_(
            "Settings that are found in the configuration file that do not appear on any option "
            "settings page are listed below. If your configuration file does not contain any "
            "unused option settings, then the list will be empty and the removal checkbox will be "
            "disabled.\n\n"
            "Note that unused option settings could come from plugins that have been uninstalled, "
            "so please be careful to not remove settings that you may want to use later when "
            "the plugin is reinstalled. Options belonging to plugins that are installed but "
            "currently disabled are not listed for possible removal.\n\n"
            "To remove one or more settings, select the settings that you want to remove by "
            "checking the box next to the setting, and enable the removal by checking the \"Remove "
            "selected options\" box. When you choose \"Make It So!\" to save your option "
            "settings, the selected items will be removed."
        ))
        self.ui.tableWidget.setHorizontalHeaderLabels([_("Option"), _("Value")])
        self.ui.select_all.stateChanged.connect(self.select_all_changed)
        self.ui.open_folder_button.clicked.connect(self.open_config_dir)
        self.ui.save_backup_button.clicked.connect(self.save_backup)
        self.ui.load_backup_button.clicked.connect(self.load_backup)
        self.ui.browse_autobackup_dir.clicked.connect(self._dialog_autobackup_dir_browse)
        self.ui.autobackup_dir.editingFinished.connect(self._check_autobackup_dir)

        # Set the palette of the config file QLineEdit widget to inactive.
        palette_normal = self.ui.config_file.palette()
        palette_readonly = QtGui.QPalette(palette_normal)
        disabled_color = palette_normal.color(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Window)
        palette_readonly.setColor(QtGui.QPalette.ColorRole.Base, disabled_color)
        self.ui.config_file.setPalette(palette_readonly)
        self.last_valid_path = _safe_autobackup_dir('')

        self.register_setting('autobackup_directory', ['autobackup_dir'])

    def get_current_autobackup_dir(self):
        return _safe_autobackup_dir(self.ui.autobackup_dir.text())

    def set_current_autobackup_dir(self, path):
        self.last_valid_path = _safe_autobackup_dir(path)
        self.ui.autobackup_dir.setText(self.last_valid_path)

    def _check_autobackup_dir(self):
        path = self.ui.autobackup_dir.text()
        if not path or not os.path.isdir(path):
            self._dialog_invalid_backup_dir(path)
        else:
            self.last_valid_path = _safe_autobackup_dir(path)
        self.ui.autobackup_dir.setText(self.last_valid_path)

    def _dialog_invalid_backup_dir(self, path):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Critical,
            _("Configuration File Backup Directory Error"),
            _("The path provided isn't a valid directory, reverting to:\n"
              "%s\n") % self.last_valid_path,
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.exec()

    def _dialog_autobackup_dir_browse(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            directory=self.get_current_autobackup_dir(),
        )
        if path:
            self.set_current_autobackup_dir(path)

    def load(self):
        config = get_config()

        self.set_current_autobackup_dir(config.setting['autobackup_directory'])

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
              "settings (%(unusedcount)d unused).") % {
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
        self._set_cleanup_state()

    def open_config_dir(self):
        config = get_config()
        config_dir = os.path.split(config.fileName())[0]
        open_local_path(config_dir)

    def _get_dialog_filetypes(self, _ext='.ini'):
        return ";;".join((
            _("Configuration files") + " (*{0})".format(_ext,),
            _("All files") + " (*)",
        ))

    def _make_backup_filename(self, auto=False):
        config = get_config()
        _filename = os.path.split(config.fileName())[1]
        _root, _ext = os.path.splitext(_filename)
        return "{0}_{1}_Backup_{2}{3}".format(
            _root,
            'Auto' if auto else 'User',
            datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            _ext,
        )

    def _dialog_save_backup_error(self, filename):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Critical,
            _("Backup Configuration File Save Error"),
            _("Failed to save the configuration file to:\n"
              "%s\n"
              "\n"
              "Please see the logs for more details." % filename),
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.exec()

    def _dialog_ask_backup_filename(self, default_path, ext):
        filename, file_type = QtWidgets.QFileDialog.getSaveFileName(
            self,
            _("Backup Configuration File"),
            default_path,
            self._get_dialog_filetypes(ext),
        )
        return filename

    def _dialog_save_backup_success(self, filename):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Information,
            _("Backup Configuration File"),
            _("Configuration successfully backed up to:\n"
              "%s") % filename,
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.exec()

    def save_backup(self):
        config = get_config()
        directory = self.get_current_autobackup_dir()
        filename = self._make_backup_filename()
        ext = os.path.splitext(filename)[1]
        default_path = os.path.normpath(os.path.join(directory, filename))

        filename = self._dialog_ask_backup_filename(default_path, ext)
        if not filename:
            return
        # Fix issue where Qt may set the extension twice
        (name, ext) = os.path.splitext(filename)
        if ext and str(name).endswith('.' + ext):
            filename = name

        if config.save_user_backup(filename):
            self._dialog_save_backup_success(filename)
        else:
            self._dialog_save_backup_error(filename)

    def _dialog_load_backup_confirmation(self, filename):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning,
            _("Load Backup Configuration File"),
            _("Loading a backup configuration file will replace the current configuration settings.\n"
              "Before any change, the current configuration will be automatically saved to:\n"
              "%s\n"
              "\n"
              "Do you want to continue?") % filename,
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
            self,
        )
        dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Cancel)
        return dialog.exec() == QtWidgets.QMessageBox.StandardButton.Ok

    def _dialog_load_backup_success(self, filename):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Information,
            _("Load Backup Configuration File"),
            _("Configuration successfully loaded from:\n"
              "%s") % filename,
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.exec()

    def _dialog_load_backup_error(self, filename):
        dialog = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Information,
            _("Load Backup Configuration File"),
            _("There was a problem restoring the configuration file from:\n"
              "%s\n"
              "\n"
              "Please see the logs for more details.") % filename,
            QtWidgets.QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.exec()

    def _dialog_load_backup_select_filename(self, directory, ext):
        filename, file_type = QtWidgets.QFileDialog.getOpenFileName(
            self,
            _("Select Configuration File to Load"),
            directory,
            self._get_dialog_filetypes(ext),
        )
        return filename

    def load_backup(self):
        directory = self.get_current_autobackup_dir()
        filename = os.path.join(directory, self._make_backup_filename(auto=True))

        if not self._dialog_load_backup_confirmation(filename):
            return

        config = get_config()
        if not config.save_user_backup(filename):
            self._dialog_save_backup_error(filename)
            return

        ext = os.path.splitext(filename)[1]
        filename = self._dialog_load_backup_select_filename(directory, ext)
        if not filename:
            return

        log.warning("Loading configuration from %s", filename)
        if load_new_config(filename):
            config = get_config()
            upgrade_config(config)
            self.signal_reload.emit()
            self._dialog_load_backup_success(filename)
        else:
            self._dialog_load_backup_error(filename)

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

    def _dialog_ask_remove_confirmation(self):
        return QtWidgets.QMessageBox.question(
            self,
            _("Confirm Remove"),
            _("Are you sure you want to remove the selected option settings?"),
        ) == QtWidgets.QMessageBox.StandardButton.Yes

    def save(self):
        config = get_config()

        config.setting['autobackup_directory'] = self.get_current_autobackup_dir()

        if not self.ui.enable_cleanup.checkState() == QtCore.Qt.CheckState.Checked:
            return
        to_remove = set(self.selected_options())
        if to_remove and self._dialog_ask_remove_confirmation():
            for item in to_remove:
                Option.add_if_missing('setting', item, None)
                log.warning("Removing option setting '%s' from the INI file.", item)
                config.setting.remove(item)

    def make_setting_value_text(self, key):
        config = get_config()
        value = config.setting.raw_value(key)
        return repr(value)

    def _set_cleanup_state(self):
        state = self.ui.tableWidget.rowCount() > 0
        self.ui.select_all.setEnabled(state)
        self.ui.enable_cleanup.setChecked(False)
        self.ui.enable_cleanup.setEnabled(state)


register_options_page(MaintenanceOptionsPage)

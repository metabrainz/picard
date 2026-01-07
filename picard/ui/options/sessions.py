# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

from PyQt6 import QtWidgets

from picard.config import get_config
from picard.const.appdirs import sessions_folder
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_, gettext as _

from picard.ui.forms.ui_options_advanced_sessions import Ui_SessionsOptionsPage
from picard.ui.options import OptionsPage
from picard.ui.util import FileDialog


class SessionsOptionsPage(OptionsPage):
    NAME = 'sessions'
    TITLE = N_('Sessions')
    PARENT = 'advanced'
    SORT_ORDER = 90
    ACTIVE = True
    HELP_URL = "/config/options_sessions.html"

    OPTIONS = (
        ('session_safe_restore', ['safe_restore_checkbox']),
        ('session_load_last_on_startup', ['load_last_checkbox']),
        ('session_autosave_interval_min', ['autosave_spin']),
        ('session_backup_on_crash', ['backup_checkbox']),
        ('session_include_mb_data', ['include_mb_data_checkbox']),
        ('session_no_mb_requests_on_load', ['no_mb_requests_checkbox']),
        ('session_folder_path', ['folder_path_edit']),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SessionsOptionsPage()
        self.ui.setupUi(self)

        # Set open directory icon on folder browse button
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon)
        self.ui.folder_browse_button.setIcon(icon)

        # Set sessions folder path placeholder text to default path
        default_path = sessions_folder()
        self.ui.folder_path_edit.setPlaceholderText(default_path)

        self.ui.folder_browse_button.clicked.connect(self._browse_sessions_folder)
        self.ui.include_mb_data_checkbox.toggled.connect(self.ui.no_mb_requests_checkbox.setEnabled)

    def load(self):
        config = get_config()
        self.ui.safe_restore_checkbox.setChecked(config.setting['session_safe_restore'])
        self.ui.load_last_checkbox.setChecked(config.setting['session_load_last_on_startup'])
        self.ui.autosave_spin.setValue(config.setting['session_autosave_interval_min'])
        self.ui.backup_checkbox.setChecked(config.setting['session_backup_on_crash'])
        self.ui.include_mb_data_checkbox.setChecked(config.setting['session_include_mb_data'])
        self.ui.no_mb_requests_checkbox.setChecked(config.setting['session_no_mb_requests_on_load'])
        # Enforce dependency (child enabled only when parent is on)
        self.ui.no_mb_requests_checkbox.setEnabled(self.ui.include_mb_data_checkbox.isChecked())
        self.ui.folder_path_edit.setText(config.setting['session_folder_path'])

    def save(self):
        config = get_config()
        config.setting['session_safe_restore'] = self.ui.safe_restore_checkbox.isChecked()
        config.setting['session_load_last_on_startup'] = self.ui.load_last_checkbox.isChecked()
        config.setting['session_autosave_interval_min'] = int(self.ui.autosave_spin.value())
        config.setting['session_backup_on_crash'] = self.ui.backup_checkbox.isChecked()
        include_mb = self.ui.include_mb_data_checkbox.isChecked()
        config.setting['session_include_mb_data'] = include_mb
        # Force child off when parent is off to avoid stale state
        config.setting['session_no_mb_requests_on_load'] = (
            self.ui.no_mb_requests_checkbox.isChecked() if include_mb else False
        )
        config.setting['session_folder_path'] = self.ui.folder_path_edit.text().strip()

    def _browse_sessions_folder(self):
        """Open a folder selection dialog for the sessions folder."""
        current_path = self.ui.folder_path_edit.text().strip()
        if not current_path:
            current_path = sessions_folder()

        folder = FileDialog.getExistingDirectory(
            parent=self, directory=current_path, caption=_("Select Sessions Folder")
        )
        if folder:
            self.ui.folder_path_edit.setText(folder)


register_options_page(SessionsOptionsPage)

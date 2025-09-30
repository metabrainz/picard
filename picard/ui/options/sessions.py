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
from picard.session.constants import SessionMessages

from picard.ui.options import OptionsPage
from picard.ui.util import FileDialog


class SessionsOptionsPage(OptionsPage):
    NAME = 'sessions'
    TITLE = N_('Sessions')
    PARENT = 'advanced'
    SORT_ORDER = 90
    ACTIVE = True

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
        self.vbox = QtWidgets.QVBoxLayout(self)

        # Sessions folder path
        folder_layout = QtWidgets.QHBoxLayout()
        self.folder_label = QtWidgets.QLabel(_(SessionMessages.SESSION_FOLDER_PATH_TITLE))
        self.folder_path_edit = QtWidgets.QLineEdit()
        # Set placeholder text showing the default path
        default_path = sessions_folder()
        self.folder_path_edit.setPlaceholderText(default_path)
        self.folder_browse_button = QtWidgets.QPushButton(_("Browse..."))
        self.folder_browse_button.clicked.connect(self._browse_sessions_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path_edit)
        folder_layout.addWidget(self.folder_browse_button)
        self.vbox.addLayout(folder_layout)

        self.safe_restore_checkbox = QtWidgets.QCheckBox(_(SessionMessages.SESSION_SAFE_RESTORE_TITLE))
        self.vbox.addWidget(self.safe_restore_checkbox)

        self.load_last_checkbox = QtWidgets.QCheckBox(_(SessionMessages.SESSION_LOAD_LAST_TITLE))
        self.vbox.addWidget(self.load_last_checkbox)

        autosave_layout = QtWidgets.QHBoxLayout()
        self.autosave_label = QtWidgets.QLabel(_(SessionMessages.SESSION_AUTOSAVE_TITLE))
        self.autosave_spin = QtWidgets.QSpinBox()
        self.autosave_spin.setRange(0, 1440)
        autosave_layout.addWidget(self.autosave_label)
        autosave_layout.addWidget(self.autosave_spin)
        self.vbox.addLayout(autosave_layout)

        self.backup_checkbox = QtWidgets.QCheckBox(_(SessionMessages.SESSION_BACKUP_TITLE))
        self.vbox.addWidget(self.backup_checkbox)

        self.include_mb_data_checkbox = QtWidgets.QCheckBox(_(SessionMessages.SESSION_INCLUDE_MB_DATA_TITLE))
        self.vbox.addWidget(self.include_mb_data_checkbox)

        # Child option: Only effective when Include MB data is enabled
        self.no_mb_requests_checkbox = QtWidgets.QCheckBox(_(SessionMessages.SESSION_NO_MB_REQUESTS_ON_LOAD))
        # Visually indent to indicate dependency on parent option
        child_layout = QtWidgets.QHBoxLayout()
        child_layout.setContentsMargins(24, 0, 0, 0)
        child_layout.addWidget(self.no_mb_requests_checkbox)
        self.vbox.addLayout(child_layout)
        # Keep child disabled when parent is unchecked
        self.include_mb_data_checkbox.toggled.connect(self.no_mb_requests_checkbox.setEnabled)

        self.vbox.addStretch(1)

    def load(self):
        config = get_config()
        self.safe_restore_checkbox.setChecked(config.setting['session_safe_restore'])
        self.load_last_checkbox.setChecked(config.setting['session_load_last_on_startup'])
        self.autosave_spin.setValue(config.setting['session_autosave_interval_min'])
        self.backup_checkbox.setChecked(config.setting['session_backup_on_crash'])
        self.include_mb_data_checkbox.setChecked(config.setting['session_include_mb_data'])
        self.no_mb_requests_checkbox.setChecked(config.setting['session_no_mb_requests_on_load'])
        # Enforce dependency (child enabled only when parent is on)
        self.no_mb_requests_checkbox.setEnabled(self.include_mb_data_checkbox.isChecked())
        self.folder_path_edit.setText(config.setting['session_folder_path'])

    def save(self):
        config = get_config()
        config.setting['session_safe_restore'] = self.safe_restore_checkbox.isChecked()
        config.setting['session_load_last_on_startup'] = self.load_last_checkbox.isChecked()
        config.setting['session_autosave_interval_min'] = int(self.autosave_spin.value())
        config.setting['session_backup_on_crash'] = self.backup_checkbox.isChecked()
        include_mb = self.include_mb_data_checkbox.isChecked()
        config.setting['session_include_mb_data'] = include_mb
        # Force child off when parent is off to avoid stale state
        config.setting['session_no_mb_requests_on_load'] = (
            self.no_mb_requests_checkbox.isChecked() if include_mb else False
        )
        config.setting['session_folder_path'] = self.folder_path_edit.text().strip()

    def _browse_sessions_folder(self):
        """Open a folder selection dialog for the sessions folder."""
        current_path = self.folder_path_edit.text().strip()
        if not current_path:
            current_path = sessions_folder()

        folder = FileDialog.getExistingDirectory(
            parent=self, directory=current_path, caption=_("Select Sessions Folder")
        )
        if folder:
            self.folder_path_edit.setText(folder)


register_options_page(SessionsOptionsPage)

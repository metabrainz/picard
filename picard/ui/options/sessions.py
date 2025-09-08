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
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_, gettext as _

from picard.ui.options import OptionsPage


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
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vbox = QtWidgets.QVBoxLayout(self)

        self.safe_restore_checkbox = QtWidgets.QCheckBox(
            _('Honor local edits and placement on load (no auto-matching)')
        )
        self.vbox.addWidget(self.safe_restore_checkbox)

        self.load_last_checkbox = QtWidgets.QCheckBox(_('Load last saved session on startup'))
        self.vbox.addWidget(self.load_last_checkbox)

        autosave_layout = QtWidgets.QHBoxLayout()
        self.autosave_label = QtWidgets.QLabel(_('Auto-save session every N minutes (0 disables)'))
        self.autosave_spin = QtWidgets.QSpinBox()
        self.autosave_spin.setRange(0, 1440)
        autosave_layout.addWidget(self.autosave_label)
        autosave_layout.addWidget(self.autosave_spin)
        self.vbox.addLayout(autosave_layout)

        self.backup_checkbox = QtWidgets.QCheckBox(_('Attempt to keep a session backup on unexpected shutdown'))
        self.vbox.addWidget(self.backup_checkbox)

        self.vbox.addStretch(1)

    def load(self):
        config = get_config()
        self.safe_restore_checkbox.setChecked(config.setting['session_safe_restore'])
        self.load_last_checkbox.setChecked(config.setting['session_load_last_on_startup'])
        self.autosave_spin.setValue(config.setting['session_autosave_interval_min'])
        self.backup_checkbox.setChecked(config.setting['session_backup_on_crash'])

    def save(self):
        config = get_config()
        config.setting['session_safe_restore'] = self.safe_restore_checkbox.isChecked()
        config.setting['session_load_last_on_startup'] = self.load_last_checkbox.isChecked()
        config.setting['session_autosave_interval_min'] = int(self.autosave_spin.value())
        config.setting['session_backup_on_crash'] = self.backup_checkbox.isChecked()


register_options_page(SessionsOptionsPage)

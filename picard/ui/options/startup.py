# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014 Lukáš Lalinský
# Copyright (C) 2008, 2018-2025 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2011, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2023 Bob Swift
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

from PyQt6 import QtCore

from picard import log
from picard.config import get_config
from picard.const import PROGRAM_UPDATE_LEVELS
from picard.const.defaults import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_PROGRAM_UPDATE_LEVEL,
)
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    gettext_constants,
)

from picard.ui.forms.ui_options_startup import Ui_StartupOptionsPage
from picard.ui.options import OptionsPage


class StartupOptionsPage(OptionsPage):
    NAME = 'startup'
    TITLE = N_("Startup")
    PARENT = 'general'
    SORT_ORDER = 5
    ACTIVE = True
    HELP_URL = "/config/options_startup.html"

    OPTIONS = (
        ('check_rtd_updates', ['check_rtd_updates']),
        ('check_for_plugin_updates', ['check_plugin_updates']),
        ('check_for_updates', ['check_for_updates']),
        ('update_check_days', ['update_check_days']),
        ('update_level', ['update_level']),
        ('log_verbosity', ['log_verbosity_label']),
    )

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_StartupOptionsPage()
        self.ui.setupUi(self)

        # Populate log verbosity selector
        for level, feat in log.levels_features.items():
            self.ui.starting_log_level.addItem(_(feat.name), level)

    def load(self):
        config = get_config()
        self.ui.check_rtd_updates.setChecked(config.setting['check_rtd_updates'])
        self.ui.check_plugin_updates.setChecked(config.setting['check_for_plugin_updates'])
        self.ui.check_for_updates.setChecked(config.setting['check_for_updates'])
        self.set_update_level(config.setting['update_level'])
        self.ui.update_check_days.setValue(config.setting['update_check_days'])
        if not self.tagger.autoupdate_enabled:
            self.ui.program_update_check_group.hide()
        log_level = config.setting['log_verbosity']
        if log_level not in log.levels_features:
            log_level = DEFAULT_LOG_LEVEL
        idx = self.ui.starting_log_level.findData(log_level)
        if idx != -1:
            self.ui.starting_log_level.setCurrentIndex(idx)

    def set_update_level(self, value):
        if value not in PROGRAM_UPDATE_LEVELS:
            value = DEFAULT_PROGRAM_UPDATE_LEVEL
        self.ui.update_level.clear()
        for level, description in PROGRAM_UPDATE_LEVELS.items():
            # TODO: Remove temporary workaround once https://github.com/python-babel/babel/issues/415 has been resolved.
            babel_415_workaround = description['title']
            self.ui.update_level.addItem(gettext_constants(babel_415_workaround), level)
        idx = self.ui.update_level.findData(value)
        if idx == -1:
            idx = self.ui.update_level.findData(DEFAULT_PROGRAM_UPDATE_LEVEL)
        self.ui.update_level.setCurrentIndex(idx)

    def save(self):
        config = get_config()
        config.setting['check_rtd_updates'] = self.ui.check_rtd_updates.isChecked()
        config.setting['check_for_plugin_updates'] = self.ui.check_plugin_updates.isChecked()
        config.setting['check_for_updates'] = self.ui.check_for_updates.isChecked()
        config.setting['update_level'] = self.ui.update_level.currentData(QtCore.Qt.ItemDataRole.UserRole)
        config.setting['update_check_days'] = self.ui.update_check_days.value()
        config.setting['log_verbosity'] = self.ui.starting_log_level.currentData(QtCore.Qt.ItemDataRole.UserRole)
        log.set_verbosity(config.setting['log_verbosity'])


register_options_page(StartupOptionsPage)

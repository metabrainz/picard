# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2013-2015, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014, 2019-2022, 2025 Philipp Wolfer
# Copyright (C) 2016-2017 Sambhav Kothari
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


from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_advanced import Ui_AdvancedOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)


class AdvancedOptionsPage(OptionsPage):
    NAME = 'advanced'
    TITLE = N_("Advanced")
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True
    HELP_URL = "/config/options_advanced.html"

    OPTIONS: PageOptionConfigs = {
        'ignore_regex': {'widgets': ['ignore_regex']},
        'ignore_hidden_files': {'widgets': ['ignore_hidden_files']},
        'recursively_add_files': {'widgets': ['recursively_add_files']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.init_regex_checker(self.ui.ignore_regex, self.ui.regex_error)

    def load(self):
        config = get_config()
        self.ui.ignore_regex.setText(config.setting['ignore_regex'])
        self.ui.ignore_hidden_files.setChecked(config.setting['ignore_hidden_files'])
        self.ui.recursively_add_files.setChecked(config.setting['recursively_add_files'])

    def save(self):
        config = get_config()
        config.setting['ignore_regex'] = self.ui.ignore_regex.text()
        config.setting['ignore_hidden_files'] = self.ui.ignore_hidden_files.isChecked()
        config.setting['recursively_add_files'] = self.ui.recursively_add_files.isChecked()


register_options_page(AdvancedOptionsPage)

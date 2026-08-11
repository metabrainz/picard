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


import re
from typing import ClassVar

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_options_advanced import Ui_AdvancedOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)
from picard.ui.playground import Playground


TOOLTIP_TEST_FILE_PATH_MATCHING = N_("""<html><head/><body>
<p>Enter file paths to test the regex against, one per line.<br/>
This playground will not be preserved on exit.
</p>
<p>
Red background means the file path does not match.<br/>
Green background means the file path matches.
</p>
</body></html>""")


class AdvancedOptionsPage(OptionsPage):
    NAME = 'advanced'
    TITLE = N_("Advanced")
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True
    HELP_URL = "/config/options_advanced.html"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'ignore_regex': {'widgets': ['ignore_regex']},
        'ignore_hidden_files': {'widgets': ['ignore_hidden_files']},
        'recursively_add_files': {'widgets': ['recursively_add_files']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.init_regex_checker(self.ui.ignore_regex, self.ui.regex_error)

        self.ui.ignore_regex.textChanged.connect(self._update_test_file_path_playground)
        self.ui.test_file_path_matching.setToolTip(_(TOOLTIP_TEST_FILE_PATH_MATCHING))
        self.ui.test_file_path_matching.setPlaceholderText(_("Enter file paths to test, one per line"))
        self.ui.test_file_path_matching.textChanged.connect(self._update_test_file_path_playground)

        self.playground = Playground(self.ui.test_file_path_matching)

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

    def _update_test_file_path_playground(self):
        regex_text = self.ui.ignore_regex.text()
        try:
            self.file_path_filter = re.compile(regex_text) if regex_text else None
        except re.error:
            self.file_path_filter = None

        def check_line(line: str) -> bool:
            return bool(self.file_path_filter.search(line))

        self.playground.update(check_line if self.file_path_filter else None)


register_options_page(AdvancedOptionsPage)

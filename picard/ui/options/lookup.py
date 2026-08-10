# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from picard.ui.forms.ui_options_lookup import Ui_LookupOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)


class LookupOptionsPage(OptionsPage):
    NAME = 'lookup'
    TITLE = N_("Lookup")
    PARENT = None
    SORT_ORDER = 25
    ACTIVE = True
    HELP_URL = "/config/options_lookup.html"

    OPTIONS: PageOptionConfigs = {
        'analyze_new_files': {'widgets': ['analyze_new_files']},
        'cluster_new_files': {'widgets': ['cluster_new_files']},
        'ignore_file_mbids': {'widgets': ['ignore_file_mbids']},
        'query_limit': {'widgets': ['query_limit']},
        'builtin_search': {'widgets': ['builtin_search']},
        'use_adv_search_syntax': {'widgets': ['use_adv_search_syntax']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_LookupOptionsPage()
        self.ui.setupUi(self)
        self.ui.analyze_new_files.toggled.connect(self._update_cluster_new_files)
        self.ui.cluster_new_files.toggled.connect(self._update_analyze_new_files)

    def load(self):
        config = get_config()
        self.ui.analyze_new_files.setChecked(config.setting['analyze_new_files'])
        self.ui.cluster_new_files.setChecked(config.setting['cluster_new_files'])
        self.ui.ignore_file_mbids.setChecked(config.setting['ignore_file_mbids'])
        self.ui.query_limit.setCurrentText(str(config.setting['query_limit']))
        self.ui.builtin_search.setChecked(config.setting['builtin_search'])
        self.ui.use_adv_search_syntax.setChecked(config.setting['use_adv_search_syntax'])

    def save(self):
        config = get_config()
        config.setting['analyze_new_files'] = self.ui.analyze_new_files.isChecked()
        config.setting['cluster_new_files'] = self.ui.cluster_new_files.isChecked()
        config.setting['ignore_file_mbids'] = self.ui.ignore_file_mbids.isChecked()
        config.setting['query_limit'] = self.ui.query_limit.currentText()
        config.setting['builtin_search'] = self.ui.builtin_search.isChecked()
        config.setting['use_adv_search_syntax'] = self.ui.use_adv_search_syntax.isChecked()

    def _update_analyze_new_files(self, cluster_new_files):
        if cluster_new_files:
            self.ui.analyze_new_files.setChecked(False)

    def _update_cluster_new_files(self, analyze_new_files):
        if analyze_new_files:
            self.ui.cluster_new_files.setChecked(False)


register_options_page(LookupOptionsPage)

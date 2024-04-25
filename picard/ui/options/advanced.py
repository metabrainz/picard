# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2013-2015, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014, 2019-2022 Philipp Wolfer
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
from picard.i18n import N_
from picard.profile import register_profile_highlights

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_advanced import Ui_AdvancedOptionsPage


class AdvancedOptionsPage(OptionsPage):

    NAME = 'advanced'
    TITLE = N_("Advanced")
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True
    HELP_URL = "/config/options_advanced.html"

    options = [
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.init_regex_checker(self.ui.ignore_regex, self.ui.regex_error)

        register_profile_highlights('advanced', 'ignore_regex', ['ignore_regex'])
        register_profile_highlights('advanced', 'ignore_hidden_files', ['ignore_hidden_files'])
        register_profile_highlights('advanced', 'recursively_add_files', ['recursively_add_files'])
        register_profile_highlights('advanced', 'ignore_track_duration_difference_under', ['ignore_track_duration_difference_under', 'label_track_duration_diff'])
        register_profile_highlights('advanced', 'query_limit', ['query_limit', 'label_query_limit'])
        register_profile_highlights('advanced', 'completeness_ignore_videos', ['completeness_ignore_videos'])
        register_profile_highlights('advanced', 'completeness_ignore_pregap', ['completeness_ignore_pregap'])
        register_profile_highlights('advanced', 'completeness_ignore_data', ['completeness_ignore_data'])
        register_profile_highlights('advanced', 'completeness_ignore_silence', ['completeness_ignore_silence'])
        register_profile_highlights('advanced', 'compare_ignore_tags', ['groupBox_ignore_tags'])

    def load(self):
        config = get_config()
        self.ui.ignore_regex.setText(config.setting['ignore_regex'])
        self.ui.ignore_hidden_files.setChecked(config.setting['ignore_hidden_files'])
        self.ui.recursively_add_files.setChecked(config.setting['recursively_add_files'])
        self.ui.ignore_track_duration_difference_under.setValue(config.setting['ignore_track_duration_difference_under'])
        self.ui.query_limit.setCurrentText(str(config.setting['query_limit']))
        self.ui.completeness_ignore_videos.setChecked(config.setting['completeness_ignore_videos'])
        self.ui.completeness_ignore_pregap.setChecked(config.setting['completeness_ignore_pregap'])
        self.ui.completeness_ignore_data.setChecked(config.setting['completeness_ignore_data'])
        self.ui.completeness_ignore_silence.setChecked(config.setting['completeness_ignore_silence'])
        self.ui.compare_ignore_tags.update(config.setting['compare_ignore_tags'])
        self.ui.compare_ignore_tags.set_user_sortable(False)

    def save(self):
        config = get_config()
        config.setting['ignore_regex'] = self.ui.ignore_regex.text()
        config.setting['ignore_hidden_files'] = self.ui.ignore_hidden_files.isChecked()
        config.setting['recursively_add_files'] = self.ui.recursively_add_files.isChecked()
        config.setting['ignore_track_duration_difference_under'] = self.ui.ignore_track_duration_difference_under.value()
        config.setting['query_limit'] = self.ui.query_limit.currentText()
        config.setting['completeness_ignore_videos'] = self.ui.completeness_ignore_videos.isChecked()
        config.setting['completeness_ignore_pregap'] = self.ui.completeness_ignore_pregap.isChecked()
        config.setting['completeness_ignore_data'] = self.ui.completeness_ignore_data.isChecked()
        config.setting['completeness_ignore_silence'] = self.ui.completeness_ignore_silence.isChecked()
        tags = list(self.ui.compare_ignore_tags.tags)
        if tags != config.setting['compare_ignore_tags']:
            config.setting['compare_ignore_tags'] = tags

    def restore_defaults(self):
        self.ui.compare_ignore_tags.clear()
        super().restore_defaults()


register_options_page(AdvancedOptionsPage)

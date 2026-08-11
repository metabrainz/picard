# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009, 2011, 2019-2021, 2025 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
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


from typing import ClassVar

from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_matching import Ui_MatchingOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)


class MatchingOptionsPage(OptionsPage):
    NAME = 'matching'
    TITLE = N_("Matching")
    PARENT = 'advanced'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_matching.html"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'match_min_similarity': {'widgets': ['match_min_similarity']},
        'match_min_margin': {'widgets': ['match_min_margin']},
        'track_matching_threshold': {'widgets': ['track_matching_threshold']},
        'ignore_track_duration_difference_under': {'widgets': ['ignore_track_duration_difference_under']},
        'completeness_ignore_videos': {'widgets': ['completeness_ignore_videos']},
        'completeness_ignore_pregap': {'widgets': ['completeness_ignore_pregap']},
        'completeness_ignore_data': {'widgets': ['completeness_ignore_data']},
        'completeness_ignore_silence': {'widgets': ['completeness_ignore_silence']},
        'compare_ignore_tags': {'widgets': ['groupBox_ignore_tags']},
    }
    _release_type_sliders: dict = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_MatchingOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.match_min_similarity.setValue(int(config.setting['match_min_similarity'] * 100))
        self.ui.match_min_margin.setValue(int(config.setting['match_min_margin'] * 100))
        self.ui.track_matching_threshold.setValue(int(config.setting['track_matching_threshold'] * 100))
        self.ui.ignore_track_duration_difference_under.setValue(
            config.setting['ignore_track_duration_difference_under']
        )
        self.ui.completeness_ignore_videos.setChecked(config.setting['completeness_ignore_videos'])
        self.ui.completeness_ignore_pregap.setChecked(config.setting['completeness_ignore_pregap'])
        self.ui.completeness_ignore_data.setChecked(config.setting['completeness_ignore_data'])
        self.ui.completeness_ignore_silence.setChecked(config.setting['completeness_ignore_silence'])
        self.ui.compare_ignore_tags.update(config.setting['compare_ignore_tags'])
        self.ui.compare_ignore_tags.set_user_sortable(False)

    def save(self):
        config = get_config()
        config.setting['match_min_similarity'] = float(self.ui.match_min_similarity.value()) / 100.0
        config.setting['match_min_margin'] = float(self.ui.match_min_margin.value()) / 100.0
        config.setting['track_matching_threshold'] = float(self.ui.track_matching_threshold.value()) / 100.0
        config.setting['ignore_track_duration_difference_under'] = (
            self.ui.ignore_track_duration_difference_under.value()
        )
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


register_options_page(MatchingOptionsPage)

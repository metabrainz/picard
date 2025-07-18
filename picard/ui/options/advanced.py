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
from picard.ui.options import OptionsPage



class AdvancedOptionsPage(OptionsPage):
    """
    Options page for advanced settings in Picard.
    Provides UI and logic for advanced configuration options.
    """

    NAME: str = 'advanced'
    TITLE: str = N_("Advanced")
    PARENT: None = None
    SORT_ORDER: int = 90
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_advanced.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('ignore_regex', ['ignore_regex']),
        ('ignore_hidden_files', ['ignore_hidden_files']),
        ('recursively_add_files', ['recursively_add_files']),
        ('ignore_track_duration_difference_under', ['ignore_track_duration_difference_under', 'label_track_duration_diff']),
        ('query_limit', ['query_limit', 'label_query_limit']),
        ('completeness_ignore_videos', ['completeness_ignore_videos']),
        ('completeness_ignore_pregap', ['completeness_ignore_pregap']),
        ('completeness_ignore_data', ['completeness_ignore_data']),
        ('completeness_ignore_silence', ['completeness_ignore_silence']),
        ('compare_ignore_tags', ['groupBox_ignore_tags']),
    )

    ui: Ui_AdvancedOptionsPage

    def __init__(self, parent: object = None) -> None:
        """
        Initialize the AdvancedOptionsPage and connect UI elements to logic.
        :param parent: The parent widget.
        """
        super().__init__(parent=parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.init_regex_checker(self.ui.ignore_regex, self.ui.regex_error)


    def load(self) -> None:
        """
        Load current advanced settings from the configuration and update the UI accordingly.
        """
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


    def save(self) -> None:
        """
        Save the current advanced settings from the UI to the configuration.
        """
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


    def restore_defaults(self) -> None:
        """
        Reset advanced settings to default values.
        """
        self.ui.compare_ignore_tags.clear()
        super().restore_defaults()


register_options_page(AdvancedOptionsPage)

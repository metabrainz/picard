# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from picard import config

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_advanced import Ui_AdvancedOptionsPage


class AdvancedOptionsPage(OptionsPage):

    NAME = "advanced"
    TITLE = N_("Advanced")
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True

    options = [
        config.TextOption("setting", "ignore_regex", ""),
        config.BoolOption("setting", "ignore_hidden_files", False),
        config.BoolOption("setting", "recursively_add_files", True),
        config.IntOption("setting", "ignore_track_duration_difference_under", 2),
        config.BoolOption("setting", "completeness_ignore_videos", False),
        config.BoolOption("setting", "completeness_ignore_pregap", False),
        config.BoolOption("setting", "completeness_ignore_data", False),
        config.BoolOption("setting", "completeness_ignore_silence", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.init_regex_checker(self.ui.ignore_regex, self.ui.regex_error)

    def load(self):
        self.ui.ignore_regex.setText(config.setting["ignore_regex"])
        self.ui.ignore_hidden_files.setChecked(config.setting["ignore_hidden_files"])
        self.ui.recursively_add_files.setChecked(config.setting["recursively_add_files"])
        self.ui.ignore_track_duration_difference_under.setValue(config.setting["ignore_track_duration_difference_under"])
        self.ui.completeness_ignore_videos.setChecked(config.setting["completeness_ignore_videos"])
        self.ui.completeness_ignore_pregap.setChecked(config.setting["completeness_ignore_pregap"])
        self.ui.completeness_ignore_data.setChecked(config.setting["completeness_ignore_data"])
        self.ui.completeness_ignore_silence.setChecked(config.setting["completeness_ignore_silence"])

    def save(self):
        config.setting["ignore_regex"] = self.ui.ignore_regex.text()
        config.setting["ignore_hidden_files"] = self.ui.ignore_hidden_files.isChecked()
        config.setting["recursively_add_files"] = self.ui.recursively_add_files.isChecked()
        config.setting["ignore_track_duration_difference_under"] = self.ui.ignore_track_duration_difference_under.value()
        config.setting["completeness_ignore_videos"] = self.ui.completeness_ignore_videos.isChecked()
        config.setting["completeness_ignore_pregap"] = self.ui.completeness_ignore_pregap.isChecked()
        config.setting["completeness_ignore_data"] = self.ui.completeness_ignore_data.isChecked()
        config.setting["completeness_ignore_silence"] = self.ui.completeness_ignore_silence.isChecked()


register_options_page(AdvancedOptionsPage)

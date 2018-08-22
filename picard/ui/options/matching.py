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
from picard.ui.ui_options_matching import Ui_MatchingOptionsPage


class MatchingOptionsPage(OptionsPage):

    NAME = "matching"
    TITLE = N_("Matching")
    PARENT = "advanced"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        config.FloatOption("setting", "file_lookup_threshold", 0.7),
        config.FloatOption("setting", "cluster_lookup_threshold", 0.8),
        config.FloatOption("setting", "track_matching_threshold", 0.4),
    ]

    _release_type_sliders = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MatchingOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.file_lookup_threshold.setValue(int(config.setting["file_lookup_threshold"] * 100))
        self.ui.cluster_lookup_threshold.setValue(int(config.setting["cluster_lookup_threshold"] * 100))
        self.ui.track_matching_threshold.setValue(int(config.setting["track_matching_threshold"] * 100))

    def save(self):
        config.setting["file_lookup_threshold"] = float(self.ui.file_lookup_threshold.value()) / 100.0
        config.setting["cluster_lookup_threshold"] = float(self.ui.cluster_lookup_threshold.value()) / 100.0
        config.setting["track_matching_threshold"] = float(self.ui.track_matching_threshold.value()) / 100.0


register_options_page(MatchingOptionsPage)

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009, 2011, 2019-2021 Philipp Wolfer
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


from picard.config import (
    FloatSetting,
    get_config,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_matching import Ui_MatchingOptionsPage


class MatchingOptionsPage(OptionsPage):

    NAME = 'matching'
    TITLE = N_("Matching")
    PARENT = 'advanced'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_matching.html"

    options = [
        FloatSetting('file_lookup_threshold', 0.7, title=N_("Minimal similarity for file lookups")),
        FloatSetting('cluster_lookup_threshold', 0.7, title=N_("Minimal similarity for cluster lookups")),
        FloatSetting('track_matching_threshold', 0.4, title=N_("Minimal similarity for matching files to tracks")),
    ]

    _release_type_sliders = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MatchingOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.file_lookup_threshold.setValue(int(config.setting['file_lookup_threshold'] * 100))
        self.ui.cluster_lookup_threshold.setValue(int(config.setting['cluster_lookup_threshold'] * 100))
        self.ui.track_matching_threshold.setValue(int(config.setting['track_matching_threshold'] * 100))

    def save(self):
        config = get_config()
        config.setting['file_lookup_threshold'] = float(self.ui.file_lookup_threshold.value()) / 100.0
        config.setting['cluster_lookup_threshold'] = float(self.ui.cluster_lookup_threshold.value()) / 100.0
        config.setting['track_matching_threshold'] = float(self.ui.track_matching_threshold.value()) / 100.0


register_options_page(MatchingOptionsPage)

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


from picard.config import get_config
from picard.extension_points.options_pages import register_options_page
from picard.i18n import N_

from picard.ui.forms.ui_options_matching import Ui_MatchingOptionsPage
from picard.ui.options import OptionsPage


class MatchingOptionsPage(OptionsPage):

    NAME = 'matching'
    TITLE = N_("Matching")
    PARENT = 'advanced'
    SORT_ORDER = 30
    ACTIVE = True
    HELP_URL = "/config/options_matching.html"

    _release_type_sliders = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_MatchingOptionsPage()
        self.ui.setupUi(self)

        self.register_setting('file_lookup_threshold', ['file_lookup_threshold'])
        self.register_setting('cluster_lookup_threshold', ['cluster_lookup_threshold'])
        self.register_setting('track_matching_threshold', ['track_matching_threshold'])

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

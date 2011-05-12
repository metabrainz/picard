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

from PyQt4 import QtCore, QtGui
from picard.config import FloatOption, TextOption
from picard.util import load_release_type_scores, save_release_type_scores
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_matching import Ui_MatchingOptionsPage


class MatchingOptionsPage(OptionsPage):

    NAME = "matching"
    TITLE = N_("Matching")
    PARENT = "advanced"
    SORT_ORDER = 30
    ACTIVE = True

    options = [
        FloatOption("setting", "file_lookup_threshold", 0.7),
        FloatOption("setting", "cluster_lookup_threshold", 0.8),
        FloatOption("setting", "track_matching_threshold", 0.4),
        TextOption("setting", "release_type_scores", "Album 0.2 Single 0.2 EP 0.2 Compilation 0.2 Soundtrack 0.2 Spokenword 0.2 Interview 0.2 Audiobook 0.2 Live 0.2 Remix 0.2 Other 0.5"),
    ]

    _release_type_sliders = {}

    def __init__(self, parent=None):
        super(MatchingOptionsPage, self).__init__(parent)
        self.ui = Ui_MatchingOptionsPage()
        self.ui.setupUi(self)
        self.connect(self.ui.reset_preferred_types_btn, QtCore.SIGNAL("clicked()"), self.reset_preferred_types)
        self._release_type_sliders["Album"] = self.ui.prefer_album_score
        self._release_type_sliders["Single"] = self.ui.prefer_single_score
        self._release_type_sliders["EP"] = self.ui.prefer_ep_score
        self._release_type_sliders["Compilation"] = self.ui.prefer_compilation_score
        self._release_type_sliders["Soundtrack"] = self.ui.prefer_soundtrack_score
        self._release_type_sliders["Spokenword"] = self.ui.prefer_spokenword_score
        self._release_type_sliders["Interview"] = self.ui.prefer_interview_score
        self._release_type_sliders["Audiobook"] = self.ui.prefer_audiobook_score
        self._release_type_sliders["Live"] = self.ui.prefer_live_score
        self._release_type_sliders["Remix"] = self.ui.prefer_remix_score
        self._release_type_sliders["Other"] = self.ui.prefer_other_score

    def load(self):
        self.ui.file_lookup_threshold.setValue(int(self.config.setting["file_lookup_threshold"] * 100))
        self.ui.cluster_lookup_threshold.setValue(int(self.config.setting["cluster_lookup_threshold"] * 100))
        self.ui.track_matching_threshold.setValue(int(self.config.setting["track_matching_threshold"] * 100))
        scores = load_release_type_scores(self.config.setting["release_type_scores"])
        for (release_type, release_type_slider) in self._release_type_sliders.iteritems():
            release_type_slider.setValue(int(scores.get(release_type, 0.5) * 100))

    def save(self):
        self.config.setting["file_lookup_threshold"] = float(self.ui.file_lookup_threshold.value()) / 100.0
        self.config.setting["cluster_lookup_threshold"] = float(self.ui.cluster_lookup_threshold.value()) / 100.0
        self.config.setting["track_matching_threshold"] = float(self.ui.track_matching_threshold.value()) / 100.0
        scores = {}
        for (release_type, release_type_slider) in self._release_type_sliders.iteritems():
            scores[release_type] = float(release_type_slider.value()) / 100.0
        self.config.setting["release_type_scores"] = save_release_type_scores(scores)

    def reset_preferred_types(self):
        for release_type_slider in self._release_type_sliders.values():
            release_type_slider.setValue(50)


register_options_page(MatchingOptionsPage)

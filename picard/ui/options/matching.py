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

from PyQt4 import QtGui
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import FloatOption

class MatchingOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        FloatOption("setting", "puid_lookup_threshold", 0.5),
        FloatOption("setting", "file_lookup_threshold", 0.7),
        FloatOption("setting", "cluster_lookup_threshold", 0.8),
        FloatOption("setting", "track_matching_threshold", 0.4),
    ]

    def get_page_info(self):
        return _(u"Matching"), "matching", "advanced", 30

    def get_page_widget(self, parent=None):
        from picard.ui.ui_options_matching import Ui_Form
        self.widget = QtGui.QWidget(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)
        return self.widget

    def load_options(self):
        self.ui.puid_lookup_threshold.setValue(int(self.config.setting["puid_lookup_threshold"] * 100))
        self.ui.file_lookup_threshold.setValue(int(self.config.setting["file_lookup_threshold"] * 100))
        self.ui.cluster_lookup_threshold.setValue(int(self.config.setting["cluster_lookup_threshold"] * 100))
        self.ui.track_matching_threshold.setValue(int(self.config.setting["track_matching_threshold"] * 100))

    def save_options(self):
        self.config.setting["puid_lookup_threshold"] = float(self.ui.puid_lookup_threshold.value()) / 100.0
        self.config.setting["file_lookup_threshold"] = float(self.ui.file_lookup_threshold.value()) / 100.0
        self.config.setting["cluster_lookup_threshold"] = float(self.ui.cluster_lookup_threshold.value()) / 100.0
        self.config.setting["track_matching_threshold"] = float(self.ui.track_matching_threshold.value()) / 100.0

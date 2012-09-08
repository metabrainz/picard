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

from operator import itemgetter
from locale import strcoll
from PyQt4 import QtCore, QtGui
from picard.config import TextOption
from picard.util import load_release_type_scores, save_release_type_scores
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_releases import Ui_ReleasesOptionsPage
from picard.const import RELEASE_COUNTRIES, RELEASE_FORMATS


class ReleasesOptionsPage(OptionsPage):

    NAME = "releases"
    TITLE = N_("Preferred Releases")
    PARENT = "metadata"
    SORT_ORDER = 10
    ACTIVE = True

    options = [
        TextOption("setting", "release_type_scores", "Album 0.5 Single 0.5 EP 0.5 Compilation 0.5 Soundtrack 0.5 Spokenword 0.5 Interview 0.5 Audiobook 0.5 Live 0.5 Remix 0.5 Other 0.5"),
        TextOption("setting", "preferred_release_countries", u""),
        TextOption("setting", "preferred_release_formats", u""),
    ]

    _release_type_sliders = {}

    def __init__(self, parent=None):
        super(ReleasesOptionsPage, self).__init__(parent)
        self.ui = Ui_ReleasesOptionsPage()
        self.ui.setupUi(self)
        self.ui.reset_preferred_types_btn.clicked.connect(self.reset_preferred_types)
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

        self.ui.add_countries.clicked.connect(self.add_preferred_countries)
        self.ui.remove_countries.clicked.connect(self.remove_preferred_countries)
        self.ui.add_formats.clicked.connect(self.add_preferred_formats)
        self.ui.remove_formats.clicked.connect(self.remove_preferred_formats)
        self.ui.country_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ui.preferred_country_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ui.format_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ui.preferred_format_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    def load(self):
        scores = load_release_type_scores(self.config.setting["release_type_scores"])
        for (release_type, release_type_slider) in self._release_type_sliders.iteritems():
            release_type_slider.setValue(int(scores.get(release_type, 0.5) * 100))

        self._load_list_items("preferred_release_countries", RELEASE_COUNTRIES,
            self.ui.country_list, self.ui.preferred_country_list)
        self._load_list_items("preferred_release_formats", RELEASE_FORMATS,
            self.ui.format_list, self.ui.preferred_format_list)

    def save(self):
        scores = {}
        for (release_type, release_type_slider) in self._release_type_sliders.iteritems():
            scores[release_type] = float(release_type_slider.value()) / 100.0
        self.config.setting["release_type_scores"] = save_release_type_scores(scores)

        self._save_list_items("preferred_release_countries", self.ui.preferred_country_list)
        self._save_list_items("preferred_release_formats", self.ui.preferred_format_list)

    def reset_preferred_types(self):
        for release_type_slider in self._release_type_sliders.values():
            release_type_slider.setValue(50)

    def add_preferred_countries(self):
        self._move_selected_items(self.ui.country_list, self.ui.preferred_country_list)

    def remove_preferred_countries(self):
        self._move_selected_items(self.ui.preferred_country_list, self.ui.country_list)
        self.ui.country_list.sortItems()

    def add_preferred_formats(self):
        self._move_selected_items(self.ui.format_list, self.ui.preferred_format_list)

    def remove_preferred_formats(self):
        self._move_selected_items(self.ui.preferred_format_list, self.ui.format_list)
        self.ui.format_list.sortItems()

    def _move_selected_items(self, list1, list2):
        for item in list1.selectedItems():
            clone = item.clone()
            list2.addItem(clone)
            list1.takeItem(list1.row(item))

    def _load_list_items(self, setting, source, list1, list2):
        source_list = [(c[0], _(c[1])) for c in source.items()]
        source_list.sort(key=itemgetter(1), cmp=strcoll)
        saved_data = self.config.setting[setting].split("  ")
        move = []
        for data, name in source_list:
            item = QtGui.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, QtCore.QVariant(data))
            try:
                i = saved_data.index(data)
                move.append((i, item))
            except:
                list1.addItem(item)
        move.sort(key=itemgetter(0))
        for i, item in move:
            list2.addItem(item)

    def _save_list_items(self, setting, list1):
        data = []
        for i in range(list1.count()):
            item = list1.item(i)
            data.append(unicode(item.data(QtCore.Qt.UserRole).toString()))
        self.config.setting[setting] = "  ".join(data)


register_options_page(ReleasesOptionsPage)

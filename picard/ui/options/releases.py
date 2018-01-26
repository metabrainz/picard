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
from locale import strxfrm
from PyQt5 import QtCore, QtWidgets
from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_releases import Ui_ReleasesOptionsPage
from picard.const import (RELEASE_COUNTRIES,
                          RELEASE_FORMATS,
                          RELEASE_PRIMARY_GROUPS,
                          RELEASE_SECONDARY_GROUPS)
from picard.i18n import gettext_attr


_DEFAULT_SCORE = 0.5
_release_type_scores = [(g, _DEFAULT_SCORE) for g in list(RELEASE_PRIMARY_GROUPS.keys()) + list(RELEASE_SECONDARY_GROUPS.keys())]


class ReleaseTypeScore:

    def __init__(self, group, layout, label, cell):
        row, column = cell  # it uses 2 cells (r,c and r,c+1)
        self.group = group
        self.layout = layout
        self.label = QtWidgets.QLabel(self.group)
        self.label.setText(label)
        self.layout.addWidget(self.label, row, column, 1, 1)
        self.slider = QtWidgets.QSlider(self.group)
        self.slider.setMaximum(100)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.layout.addWidget(self.slider, row, column + 1, 1, 1)
        self.reset()

    def setValue(self, value):
        self.slider.setValue(int(value * 100))

    def value(self):
        return float(self.slider.value()) / 100.0

    def reset(self):
        self.setValue(_DEFAULT_SCORE)


class RowColIter:

    def __init__(self, max_cells, max_cols=6, step=2):
        assert(max_cols % step == 0)
        self.step = step
        self.cols = max_cols
        self.rows = int((max_cells - 1) / (self.cols / step)) + 1
        self.current = (-1, 0)

    def __iter__(self):
        return self

    def __next__(self):
        row, col = self.current
        row += 1
        if row == self.rows:
            col += self.step
            row = 0
        self.current = (row, col)
        return self.current


class ReleasesOptionsPage(OptionsPage):

    NAME = "releases"
    TITLE = N_("Preferred Releases")
    PARENT = "metadata"
    SORT_ORDER = 10
    ACTIVE = True

    options = [
        config.ListOption("setting", "release_type_scores", _release_type_scores),
        config.ListOption("setting", "preferred_release_countries", []),
        config.ListOption("setting", "preferred_release_formats", []),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ReleasesOptionsPage()
        self.ui.setupUi(self)

        self._release_type_sliders = {}

        def add_slider(name, griditer, context):
            label = gettext_attr(name, context)
            self._release_type_sliders[name] = \
                ReleaseTypeScore(self.ui.type_group,
                                 self.ui.gridLayout,
                                 label,
                                 next(griditer))

        griditer = RowColIter(len(RELEASE_PRIMARY_GROUPS) +
                              len(RELEASE_SECONDARY_GROUPS) + 1)  # +1 for Reset button
        for name in RELEASE_PRIMARY_GROUPS:
            add_slider(name, griditer, context='release_group_primary_type')
        for name in RELEASE_SECONDARY_GROUPS:
            add_slider(name, griditer, context='release_group_secondary_type')

        self.reset_preferred_types_btn = QtWidgets.QPushButton(self.ui.type_group)
        self.reset_preferred_types_btn.setText(_("Reset all"))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.reset_preferred_types_btn.sizePolicy().hasHeightForWidth())
        self.reset_preferred_types_btn.setSizePolicy(sizePolicy)
        r, c = next(griditer)
        self.ui.gridLayout.addWidget(self.reset_preferred_types_btn, r, c, 1, 2)
        self.reset_preferred_types_btn.clicked.connect(self.reset_preferred_types)

        self.ui.add_countries.clicked.connect(self.add_preferred_countries)
        self.ui.remove_countries.clicked.connect(self.remove_preferred_countries)
        self.ui.add_formats.clicked.connect(self.add_preferred_formats)
        self.ui.remove_formats.clicked.connect(self.remove_preferred_formats)
        self.ui.country_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.ui.preferred_country_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.ui.format_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.ui.preferred_format_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def restore_defaults(self):
        # Clear lists
        self.ui.preferred_country_list.clear()
        self.ui.preferred_format_list.clear()
        self.ui.country_list.clear()
        self.ui.format_list.clear()
        super().restore_defaults()

    def load(self):
        scores = dict(config.setting["release_type_scores"])
        for (release_type, release_type_slider) in self._release_type_sliders.items():
            release_type_slider.setValue(scores.get(release_type,
                                                    _DEFAULT_SCORE))

        self._load_list_items("preferred_release_countries", RELEASE_COUNTRIES,
                              self.ui.country_list, self.ui.preferred_country_list)
        self._load_list_items("preferred_release_formats", RELEASE_FORMATS,
                              self.ui.format_list, self.ui.preferred_format_list)

    def save(self):
        scores = []
        for (release_type, release_type_slider) in self._release_type_sliders.items():
            scores.append((release_type, release_type_slider.value()))
        config.setting["release_type_scores"] = scores

        self._save_list_items("preferred_release_countries", self.ui.preferred_country_list)
        self._save_list_items("preferred_release_formats", self.ui.preferred_format_list)

    def reset_preferred_types(self):
        for release_type_slider in self._release_type_sliders.values():
            release_type_slider.reset()

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
        if setting == "preferred_release_countries":
            source_list = [(c[0], gettext_countries(c[1])) for c in
                           source.items()]
        elif setting == "preferred_release_formats":
            source_list = [(c[0], gettext_attr(c[1], "medium_format")) for c
                           in source.items()]
        else:
            source_list = [(c[0], _(c[1])) for c in source.items()]
        fcmp = lambda x: strxfrm(x[1])
        source_list.sort(key=fcmp)
        saved_data = config.setting[setting]
        move = []
        for data, name in source_list:
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, data)
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
            data.append(string_(item.data(QtCore.Qt.UserRole)))
        config.setting[setting] = data


register_options_page(ReleasesOptionsPage)

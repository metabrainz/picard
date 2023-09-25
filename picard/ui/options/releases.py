# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2015, 2018-2022 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2018-2022 Philipp Wolfer
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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    ListOption,
    get_config,
)
from picard.const import (
    RELEASE_FORMATS,
    RELEASE_PRIMARY_GROUPS,
    RELEASE_SECONDARY_GROUPS,
)
from picard.const.countries import RELEASE_COUNTRIES
from picard.const.sys import IS_WIN
from picard.util import strxfrm

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_releases import Ui_ReleasesOptionsPage
from picard.ui.util import qlistwidget_items
from picard.ui.widgets import ClickableSlider


_DEFAULT_SCORE = 0.5
_release_type_scores = [(g, _DEFAULT_SCORE) for g in list(RELEASE_PRIMARY_GROUPS.keys()) + list(RELEASE_SECONDARY_GROUPS.keys())]


class TipSlider(ClickableSlider):

    _offset = QtCore.QPoint(0, -30)
    _step = 5
    _pagestep = 25
    _minimum = 0
    _maximum = 100

    def __init__(self, *args):
        super().__init__(*args)

        self.style = QtWidgets.QApplication.style()
        self.opt = QtWidgets.QStyleOptionSlider()
        self.setMinimum(self._minimum)
        self.setMaximum(self._maximum)
        self.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.setSingleStep(self._step)
        self.setTickInterval(self._step)
        self.setPageStep(self._pagestep)

    def showEvent(self, event):
        super().showEvent(event)
        if not IS_WIN:
            self.valueChanged.connect(self.show_tip)

    def hideEvent(self, event):
        super().hideEvent(event)
        if not IS_WIN:
            try:
                self.valueChanged.disconnect(self.show_tip)
            except TypeError:
                pass

    def show_tip(self, value):
        self.round_value(value)
        self.initStyleOption(self.opt)
        rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)

        offset = self._offset * self.tagger.primaryScreen().devicePixelRatio()
        pos_local = rectHandle.topLeft() + offset
        pos_global = self.mapToGlobal(pos_local)
        QtWidgets.QToolTip.showText(pos_global, str(self.value()), self)

    def round_value(self, value):
        step = max(1, int(self._step))
        if step > 1:
            super().setValue(int(value / step) * step)


class ReleaseTypeScore:

    def __init__(self, group, layout, label, cell):
        row, column = cell  # it uses 2 cells (r,c and r,c+1)
        self.group = group
        self.layout = layout
        self.label = QtWidgets.QLabel(self.group)
        self.label.setText(label)
        self.layout.addWidget(self.label, row, column, 1, 1)
        self.slider = TipSlider(self.group)
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
        assert max_cols % step == 0
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

    NAME = 'releases'
    TITLE = N_("Preferred Releases")
    PARENT = 'metadata'
    SORT_ORDER = 10
    ACTIVE = True
    HELP_URL = "/config/options_releases.html"

    options = [
        ListOption('setting', 'release_type_scores', _release_type_scores),
        ListOption('setting', 'preferred_release_countries', []),
        ListOption('setting', 'preferred_release_formats', []),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ReleasesOptionsPage()
        self.ui.setupUi(self)

        self._release_type_sliders = {}

        def add_slider(name, griditer, context):
            label = pgettext_attributes(context, name)
            self._release_type_sliders[name] = ReleaseTypeScore(
                self.ui.type_group,
                self.ui.gridLayout,
                label,
                next(griditer))

        griditer = RowColIter(len(RELEASE_PRIMARY_GROUPS)
                              + len(RELEASE_SECONDARY_GROUPS)
                              + 1)  # +1 for Reset button
        for name in RELEASE_PRIMARY_GROUPS:
            add_slider(name, griditer, context='release_group_primary_type')
        for name in sorted(RELEASE_SECONDARY_GROUPS,
                           key=lambda v: pgettext_attributes('release_group_secondary_type', v)):
            add_slider(name, griditer, context='release_group_secondary_type')

        reset_types_btn = QtWidgets.QPushButton(self.ui.type_group)
        reset_types_btn.setText(_("Reset all"))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(reset_types_btn.sizePolicy().hasHeightForWidth())
        reset_types_btn.setSizePolicy(sizePolicy)
        r, c = next(griditer)
        self.ui.gridLayout.addWidget(reset_types_btn, r, c, 1, 2)
        reset_types_btn.clicked.connect(self.reset_preferred_types)

        self.setTabOrder(reset_types_btn, self.ui.country_list)
        self.setTabOrder(self.ui.country_list, self.ui.preferred_country_list)
        self.setTabOrder(self.ui.preferred_country_list, self.ui.add_countries)
        self.setTabOrder(self.ui.add_countries, self.ui.remove_countries)
        self.setTabOrder(self.ui.remove_countries, self.ui.format_list)
        self.setTabOrder(self.ui.format_list, self.ui.preferred_format_list)
        self.setTabOrder(self.ui.preferred_format_list, self.ui.add_formats)
        self.setTabOrder(self.ui.add_formats, self.ui.remove_formats)

        self.ui.add_countries.clicked.connect(self.add_preferred_countries)
        self.ui.remove_countries.clicked.connect(self.remove_preferred_countries)
        self.ui.add_formats.clicked.connect(self.add_preferred_formats)
        self.ui.remove_formats.clicked.connect(self.remove_preferred_formats)
        self.ui.country_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.preferred_country_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.format_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.preferred_format_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

    def restore_defaults(self):
        # Clear lists
        self.ui.preferred_country_list.clear()
        self.ui.preferred_format_list.clear()
        self.ui.country_list.clear()
        self.ui.format_list.clear()
        super().restore_defaults()

    def load(self):
        config = get_config()
        scores = dict(config.setting['release_type_scores'])
        for (release_type, release_type_slider) in self._release_type_sliders.items():
            release_type_slider.setValue(scores.get(release_type,
                                                    _DEFAULT_SCORE))

        self._load_list_items('preferred_release_countries', RELEASE_COUNTRIES,
                              self.ui.country_list, self.ui.preferred_country_list)
        self._load_list_items('preferred_release_formats', RELEASE_FORMATS,
                              self.ui.format_list, self.ui.preferred_format_list)

    def save(self):
        config = get_config()
        scores = []
        for (release_type, release_type_slider) in self._release_type_sliders.items():
            scores.append((release_type, release_type_slider.value()))
        config.setting['release_type_scores'] = scores

        self._save_list_items('preferred_release_countries', self.ui.preferred_country_list)
        self._save_list_items('preferred_release_formats', self.ui.preferred_format_list)

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
        if setting == 'preferred_release_countries':
            source_list = [(c[0], gettext_countries(c[1])) for c in
                           source.items()]
        elif setting == 'preferred_release_formats':
            source_list = [(c[0], pgettext_attributes('medium_format', c[1])) for c
                           in source.items()]
        else:
            source_list = [(c[0], _(c[1])) for c in source.items()]

        def fcmp(x):
            return strxfrm(x[1])
        source_list.sort(key=fcmp)
        config = get_config()
        saved_data = config.setting[setting]
        move = []
        for data, name in source_list:
            item = QtWidgets.QListWidgetItem(name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, data)
            try:
                i = saved_data.index(data)
                move.append((i, item))
            except BaseException:
                list1.addItem(item)
        move.sort(key=itemgetter(0))
        for i, item in move:
            list2.addItem(item)

    def _save_list_items(self, setting, list1):
        data = [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in qlistwidget_items(list1)
        ]
        config = get_config()
        config.setting[setting] = data


register_options_page(ReleasesOptionsPage)

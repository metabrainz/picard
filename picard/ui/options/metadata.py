# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009, 2018-2021 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020 Laurent Monin
# Copyright (C) 2014 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2021 Bob Swift
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


from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    BoolOption,
    IntOption,
    ListOption,
    TextOption,
    get_config,
)
from picard.const import (
    ALIAS_LOCALES,
    SCRIPTS,
)

from picard.ui import PicardDialog
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_multi_locale_selector import Ui_MultiLocaleSelector
from picard.ui.ui_options_metadata import Ui_MetadataOptionsPage


def iter_sorted_locales(locales):
    generic_names = []
    grouped_locales = {}
    for locale, name in locales.items():
        name = _(name)
        generic_locale = locale.split('_', 1)[0]
        if generic_locale == locale:
            generic_names.append((name, locale))
        else:
            grouped_locales.setdefault(generic_locale, []).append((name, locale))

    for name, locale in sorted(generic_names):
        yield (locale, 0)
        for name, locale in sorted(grouped_locales.get(locale, [])):
            yield (locale, 1)


class MetadataOptionsPage(OptionsPage):

    NAME = "metadata"
    TITLE = N_("Metadata")
    PARENT = None
    SORT_ORDER = 20
    ACTIVE = True
    HELP_URL = '/config/options_metadata.html'

    options = [
        TextOption("setting", "va_name", "Various Artists"),
        TextOption("setting", "nat_name", "[non-album tracks]"),
        ListOption("setting", "artist_locales", ["en"]),
        BoolOption("setting", "translate_artist_names", False),
        BoolOption("setting", "translate_artist_names_script_exception", False),
        ListOption("setting", "artist_script_exceptions", []),
        IntOption("setting", "artist_script_exception_weighting", 0),
        BoolOption("setting", "release_ars", True),
        BoolOption("setting", "track_ars", False),
        BoolOption("setting", "convert_punctuation", True),
        BoolOption("setting", "standardize_artists", False),
        BoolOption("setting", "standardize_instruments", True),
        BoolOption("setting", "guess_tracknumber_and_title", True),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MetadataOptionsPage()
        self.ui.setupUi(self)
        self.ui.va_name_default.clicked.connect(self.set_va_name_default)
        self.ui.nat_name_default.clicked.connect(self.set_nat_name_default)
        self.ui.select_locales.clicked.connect(self.open_locale_selector)
        self.ui.translate_artist_names.stateChanged.connect(self.set_enabled_states)
        self.ui.translate_artist_names_script_exception.stateChanged.connect(self.set_enabled_states)

    def load(self):
        config = get_config()
        self.ui.translate_artist_names.setChecked(config.setting["translate_artist_names"])
        self.current_locales = config.setting["artist_locales"]
        self.make_locales_text()
        self.ui.translate_artist_names_script_exception.setChecked(config.setting["translate_artist_names_script_exception"])
        self.ui.ignore_tx_scripts.clear()
        for script_id in SCRIPTS:
            enabled = script_id in config.setting["artist_script_exceptions"]
            item = QtWidgets.QListWidgetItem(_(SCRIPTS[script_id]))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setData(QtCore.Qt.UserRole, script_id)
            item.setCheckState(QtCore.Qt.Checked if enabled else QtCore.Qt.Unchecked)
            self.ui.ignore_tx_scripts.addItem(item)
        self.ui.minimum_weighting.setValue(config.setting["artist_script_exception_weighting"])

        self.ui.convert_punctuation.setChecked(config.setting["convert_punctuation"])
        self.ui.release_ars.setChecked(config.setting["release_ars"])
        self.ui.track_ars.setChecked(config.setting["track_ars"])
        self.ui.va_name.setText(config.setting["va_name"])
        self.ui.nat_name.setText(config.setting["nat_name"])
        self.ui.standardize_artists.setChecked(config.setting["standardize_artists"])
        self.ui.standardize_instruments.setChecked(config.setting["standardize_instruments"])
        self.ui.guess_tracknumber_and_title.setChecked(config.setting["guess_tracknumber_and_title"])

        self.set_enabled_states()

    def make_locales_text(self):
        def translated_locales():
            for locale in self.current_locales:
                yield _(ALIAS_LOCALES[locale])

        self.ui.selected_locales.setText('; '.join(translated_locales()))

    def save(self):
        config = get_config()
        config.setting["translate_artist_names"] = self.ui.translate_artist_names.isChecked()
        config.setting["artist_locales"] = self.current_locales
        config.setting["translate_artist_names_script_exception"] = self.ui.translate_artist_names_script_exception.isChecked()
        script_exceptions = []
        for idx in range(self.ui.ignore_tx_scripts.count()):
            item = self.ui.ignore_tx_scripts.item(idx)
            if item.checkState() == QtCore.Qt.Checked:
                script_exceptions.append(item.data(QtCore.Qt.UserRole))
        config.setting["artist_script_exceptions"] = script_exceptions
        config.setting["artist_script_exception_weighting"] = min(100, max(0, self.ui.minimum_weighting.value()))
        config.setting["convert_punctuation"] = self.ui.convert_punctuation.isChecked()
        config.setting["release_ars"] = self.ui.release_ars.isChecked()
        config.setting["track_ars"] = self.ui.track_ars.isChecked()
        config.setting["va_name"] = self.ui.va_name.text()
        nat_name = self.ui.nat_name.text()
        if nat_name != config.setting["nat_name"]:
            config.setting["nat_name"] = nat_name
            if self.tagger.nats is not None:
                self.tagger.nats.update()
        config.setting["standardize_artists"] = self.ui.standardize_artists.isChecked()
        config.setting["standardize_instruments"] = self.ui.standardize_instruments.isChecked()
        config.setting["guess_tracknumber_and_title"] = self.ui.guess_tracknumber_and_title.isChecked()

    def set_va_name_default(self):
        self.ui.va_name.setText(self.options[0].default)
        self.ui.va_name.setCursorPosition(0)

    def set_nat_name_default(self):
        self.ui.nat_name.setText(self.options[1].default)
        self.ui.nat_name.setCursorPosition(0)

    def set_enabled_states(self):
        translate_checked = self.ui.translate_artist_names.isChecked()
        translate_exception_checked = self.ui.translate_artist_names_script_exception.isChecked()
        self.ui.select_locales.setEnabled(translate_checked)
        self.ui.selected_locales.setEnabled(translate_checked)
        self.ui.translate_artist_names_script_exception.setEnabled(translate_checked)
        self.ui.ignore_script_frame.setEnabled(translate_checked and translate_exception_checked)

    def open_locale_selector(self):
        dialog = MultiLocaleSelector(self)
        dialog.show()


class MultiLocaleSelector(PicardDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MultiLocaleSelector()
        self.ui.setupUi(self)
        self.ui.button_box.accepted.connect(self.save_changes)
        self.ui.button_box.rejected.connect(self.reject)
        self.move_view = MoveableListView(self.ui.selected_locales, self.ui.move_up, self.ui.move_down)
        self.ui.add_locale.clicked.connect(self.add_locale)
        self.ui.remove_locale.clicked.connect(self.remove_locale)
        self.ui.selected_locales.currentRowChanged.connect(self.set_button_state)
        self.load()

    def load(self):
        for locale in self.parent().current_locales:
            # Note that items in the selected locales list are not indented because
            # the root locale may not be in the list, or may not immediately precede
            # the specific locale.
            label = _(ALIAS_LOCALES[locale])
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, locale)
            self.ui.selected_locales.addItem(item)
        self.ui.selected_locales.setCurrentRow(0)

        def indented_translated_locale(locale, level):
            return _("{indent}{locale}").format(
                indent="    " * level,
                locale=_(ALIAS_LOCALES[locale])
            )

        self.ui.available_locales.clear()
        for (locale, level) in iter_sorted_locales(ALIAS_LOCALES):
            label = indented_translated_locale(locale, level)
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, locale)
            self.ui.available_locales.addItem(item)
        self.ui.available_locales.setCurrentRow(0)

        self.set_button_state()

    def add_locale(self):
        item = self.ui.available_locales.currentItem()
        if item is None:
            return
        locale = item.data(QtCore.Qt.UserRole)
        for row in range(self.ui.selected_locales.count()):
            selected_item = self.ui.selected_locales.item(row)
            if selected_item.data(QtCore.Qt.UserRole) == locale:
                return
        new_item = item.clone()
        # Note that items in the selected locales list are not indented because
        # the root locale may not be in the list, or may not immediately precede
        # the specific locale.
        new_item.setText(_(ALIAS_LOCALES[locale]))
        self.ui.selected_locales.addItem(new_item)
        self.ui.selected_locales.setCurrentRow(self.ui.selected_locales.count() - 1)

    def remove_locale(self):
        row = self.ui.selected_locales.currentRow()
        self.ui.selected_locales.takeItem(row)

    def set_button_state(self):
        enabled = self.ui.selected_locales.count() > 1
        self.ui.remove_locale.setEnabled(enabled)

    def save_changes(self):
        locales = []
        for row in range(self.ui.selected_locales.count()):
            selected_item = self.ui.selected_locales.item(row)
            locales.append(selected_item.data(QtCore.Qt.UserRole))
        self.parent().current_locales = locales
        self.parent().make_locales_text()
        self.accept()


register_options_page(MetadataOptionsPage)

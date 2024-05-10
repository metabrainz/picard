# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018, 2020-2024 Laurent Monin
# Copyright (C) 2014 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2021-2023 Bob Swift
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


from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import (
    Option,
    get_config,
)
from picard.const.locales import ALIAS_LOCALES
from picard.const.scripts import (
    SCRIPTS,
    scripts_sorted_by_localized_name,
)
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    gettext_constants,
)

from picard.ui import PicardDialog
from picard.ui.moveable_list_view import MoveableListView
from picard.ui.options import OptionsPage
from picard.ui.ui_exception_script_selector import Ui_ExceptionScriptSelector
from picard.ui.ui_multi_locale_selector import Ui_MultiLocaleSelector
from picard.ui.ui_options_metadata import Ui_MetadataOptionsPage
from picard.ui.util import qlistwidget_items


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

    NAME = 'metadata'
    TITLE = N_("Metadata")
    PARENT = None
    SORT_ORDER = 20
    ACTIVE = True
    HELP_URL = "/config/options_metadata.html"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MetadataOptionsPage()
        self.ui.setupUi(self)
        self.ui.va_name_default.clicked.connect(self.set_va_name_default)
        self.ui.nat_name_default.clicked.connect(self.set_nat_name_default)
        self.ui.select_locales.clicked.connect(self.open_locale_selector)
        self.ui.select_scripts.clicked.connect(self.open_script_selector)
        self.ui.translate_artist_names.stateChanged.connect(self.set_enabled_states)
        self.ui.translate_artist_names_script_exception.stateChanged.connect(self.set_enabled_states)

        self.register_setting('translate_artist_names', ['translate_artist_names'])
        self.register_setting('artist_locales', ['selected_locales'])
        self.register_setting('translate_artist_names_script_exception', ['translate_artist_names_script_exception'])
        self.register_setting('script_exceptions', ['selected_scripts'])
        self.register_setting('standardize_artists', ['standardize_artists'])
        self.register_setting('standardize_instruments', ['standardize_instruments'])
        self.register_setting('convert_punctuation', ['convert_punctuation'])
        self.register_setting('release_ars', ['release_ars'])
        self.register_setting('track_ars', ['track_ars'])
        self.register_setting('guess_tracknumber_and_title', ['guess_tracknumber_and_title'])
        self.register_setting('va_name', ['va_name'])
        self.register_setting('nat_name', ['nat_name'])

    def load(self):
        config = get_config()
        self.ui.translate_artist_names.setChecked(config.setting['translate_artist_names'])
        self.current_locales = config.setting['artist_locales']
        self.make_locales_text()
        self.current_scripts = config.setting['script_exceptions']
        self.make_scripts_text()
        self.ui.translate_artist_names_script_exception.setChecked(config.setting['translate_artist_names_script_exception'])

        self.ui.convert_punctuation.setChecked(config.setting['convert_punctuation'])
        self.ui.release_ars.setChecked(config.setting['release_ars'])
        self.ui.track_ars.setChecked(config.setting['track_ars'])
        self.ui.va_name.setText(config.setting['va_name'])
        self.ui.nat_name.setText(config.setting['nat_name'])
        self.ui.standardize_artists.setChecked(config.setting['standardize_artists'])
        self.ui.standardize_instruments.setChecked(config.setting['standardize_instruments'])
        self.ui.guess_tracknumber_and_title.setChecked(config.setting['guess_tracknumber_and_title'])

        self.set_enabled_states()

    def make_locales_text(self):
        def translated_locales():
            for locale in self.current_locales:
                yield gettext_constants(ALIAS_LOCALES[locale])

        self.ui.selected_locales.setText('; '.join(translated_locales()))

    def make_scripts_text(self):
        def translated_scripts():
            for script in self.current_scripts:
                yield ScriptExceptionSelector.make_label(script[0], script[1])

        self.ui.selected_scripts.setText('; '.join(translated_scripts()))

    def save(self):
        config = get_config()
        config.setting['translate_artist_names'] = self.ui.translate_artist_names.isChecked()
        config.setting['artist_locales'] = self.current_locales
        config.setting['translate_artist_names_script_exception'] = self.ui.translate_artist_names_script_exception.isChecked()
        config.setting['script_exceptions'] = self.current_scripts
        config.setting['convert_punctuation'] = self.ui.convert_punctuation.isChecked()
        config.setting['release_ars'] = self.ui.release_ars.isChecked()
        config.setting['track_ars'] = self.ui.track_ars.isChecked()
        config.setting['va_name'] = self.ui.va_name.text()
        nat_name = self.ui.nat_name.text()
        if nat_name != config.setting['nat_name']:
            config.setting['nat_name'] = nat_name
            if self.tagger.nats is not None:
                self.tagger.nats.update()
        config.setting['standardize_artists'] = self.ui.standardize_artists.isChecked()
        config.setting['standardize_instruments'] = self.ui.standardize_instruments.isChecked()
        config.setting['guess_tracknumber_and_title'] = self.ui.guess_tracknumber_and_title.isChecked()

    def set_va_name_default(self):
        self.ui.va_name.setText(Option.get_default('setting', 'va_name'))
        self.ui.va_name.setCursorPosition(0)

    def set_nat_name_default(self):
        self.ui.nat_name.setText(Option.get_default('setting', 'nat_name'))
        self.ui.nat_name.setCursorPosition(0)

    def set_enabled_states(self):
        translate_checked = self.ui.translate_artist_names.isChecked()
        translate_exception_checked = self.ui.translate_artist_names_script_exception.isChecked()
        self.ui.select_locales.setEnabled(translate_checked)
        self.ui.selected_locales.setEnabled(translate_checked)
        self.ui.translate_artist_names_script_exception.setEnabled(translate_checked)
        select_scripts_enabled = translate_checked and translate_exception_checked
        self.ui.selected_scripts.setEnabled(select_scripts_enabled)
        self.ui.select_scripts.setEnabled(select_scripts_enabled)

    def open_locale_selector(self):
        dialog = MultiLocaleSelector(self)
        dialog.show()

    def open_script_selector(self):
        dialog = ScriptExceptionSelector(self)
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
            label = gettext_constants(ALIAS_LOCALES[locale])
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, locale)
            self.ui.selected_locales.addItem(item)
        self.ui.selected_locales.setCurrentRow(0)

        def indented_translated_locale(locale, level):
            return _("{indent}{locale}").format(
                indent="    " * level,
                locale=gettext_constants(ALIAS_LOCALES[locale])
            )

        self.ui.available_locales.clear()
        for (locale, level) in iter_sorted_locales(ALIAS_LOCALES):
            label = indented_translated_locale(locale, level)
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, locale)
            self.ui.available_locales.addItem(item)
        self.ui.available_locales.setCurrentRow(0)

        self.set_button_state()

    def add_locale(self):
        item = self.ui.available_locales.currentItem()
        if item is None:
            return
        locale = item.data(QtCore.Qt.ItemDataRole.UserRole)
        for selected_item in qlistwidget_items(self.ui.selected_locales):
            if selected_item.data(QtCore.Qt.ItemDataRole.UserRole) == locale:
                return
        new_item = item.clone()
        # Note that items in the selected locales list are not indented because
        # the root locale may not be in the list, or may not immediately precede
        # the specific locale.
        new_item.setText(gettext_constants(ALIAS_LOCALES[locale]))
        self.ui.selected_locales.addItem(new_item)
        self.ui.selected_locales.setCurrentRow(self.ui.selected_locales.count() - 1)

    def remove_locale(self):
        row = self.ui.selected_locales.currentRow()
        self.ui.selected_locales.takeItem(row)

    def set_button_state(self):
        enabled = self.ui.selected_locales.count() > 1
        self.ui.remove_locale.setEnabled(enabled)

    def save_changes(self):
        locales = [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in qlistwidget_items(self.ui.selected_locales)
        ]
        self.parent().current_locales = locales
        self.parent().make_locales_text()
        self.accept()


class ScriptExceptionSelector(PicardDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExceptionScriptSelector()
        self.ui.setupUi(self)
        self.ui.button_box.accepted.connect(self.save_changes)
        self.ui.button_box.rejected.connect(self.reject)
        self.move_view = MoveableListView(self.ui.selected_scripts, self.ui.move_up, self.ui.move_down)
        self.ui.add_script.clicked.connect(self.add_script)
        self.ui.remove_script.clicked.connect(self.remove_script)
        self.ui.selected_scripts.currentRowChanged.connect(self.selected_script_changed)
        self.ui.weighting_selector.valueChanged.connect(self.weighting_changed)

        weighting_tooltip_text = _(
            "Each selected script includes a matching threshold value used to determine if that script should be used. When an artist name is "
            "evaluated to determine if it matches one of your selected scripts, it is first parsed to determine which scripts are represented "
            "in the name, and what weighted percentage of the name belongs to each script. Then each of your selected scripts are checked, and "
            "if the name contains characters belonging to the script and the percentage of script characters in the name meets or exceeds the "
            "match threshold specified for the script, then the artist name will not be translated."
        )
        self.ui.weighting_selector.setToolTip(weighting_tooltip_text)
        self.ui.threshold_label.setToolTip(weighting_tooltip_text)

        self.load()

    @staticmethod
    def make_label(script_id, script_weighting):
        return "{script} ({weighting}%)".format(
            script=gettext_constants(SCRIPTS[script_id]),
            weighting=script_weighting,
        )

    def load(self):
        self.ui.selected_scripts.clear()
        for script in self.parent().current_scripts:
            label = self.make_label(script_id=script[0], script_weighting=script[1])
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, script)
            self.ui.selected_scripts.addItem(item)
        if self.ui.selected_scripts.count() > 0:
            self.ui.selected_scripts.setCurrentRow(0)
        self.set_weighting_selector()

        self.ui.available_scripts.clear()
        for script_id, label in scripts_sorted_by_localized_name():
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, script_id)
            self.ui.available_scripts.addItem(item)
        self.ui.available_scripts.setCurrentRow(0)

        self.set_button_state()

    def add_script(self):
        item = self.ui.available_scripts.currentItem()
        if item is None:
            return
        script_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        for selected_item in qlistwidget_items(self.ui.selected_scripts):
            if selected_item.data(QtCore.Qt.ItemDataRole.UserRole)[0] == script_id:
                return
        new_item = QtWidgets.QListWidgetItem(self.make_label(script_id, 0))
        new_item.setData(QtCore.Qt.ItemDataRole.UserRole, (script_id, 0))
        self.ui.selected_scripts.addItem(new_item)
        self.ui.selected_scripts.setCurrentRow(self.ui.selected_scripts.count() - 1)
        self.set_weighting_selector()

    def remove_script(self):
        row = self.ui.selected_scripts.currentRow()
        self.ui.selected_scripts.takeItem(row)

    def selected_script_changed(self):
        self.set_weighting_selector()
        self.set_button_state()

    def weighting_changed(self):
        self.set_item_from_weighting()

    def set_button_state(self):
        enabled = self.ui.selected_scripts.count() > 0
        self.ui.remove_script.setEnabled(enabled)
        self.ui.weighting_selector.setEnabled(enabled)

    def set_weighting_selector(self):
        row = self.ui.selected_scripts.currentRow()
        selected_item = self.ui.selected_scripts.item(row)
        if selected_item:
            weighting = selected_item.data(QtCore.Qt.ItemDataRole.UserRole)[1]
        else:
            weighting = 0
        self.ui.weighting_selector.setValue(weighting)

    def set_item_from_weighting(self):
        row = self.ui.selected_scripts.currentRow()
        selected_item = self.ui.selected_scripts.item(row)
        if selected_item:
            item_data = selected_item.data(QtCore.Qt.ItemDataRole.UserRole)
            weighting = self.ui.weighting_selector.value()
            new_data = (item_data[0], weighting)
            selected_item.setData(QtCore.Qt.ItemDataRole.UserRole, new_data)
            label = self.make_label(script_id=item_data[0], script_weighting=weighting)
            selected_item.setText(label)

    def save_changes(self):
        scripts = [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in qlistwidget_items(self.ui.selected_scripts)
        ]
        self.parent().current_scripts = scripts
        self.parent().make_scripts_text()
        self.accept()


register_options_page(MetadataOptionsPage)

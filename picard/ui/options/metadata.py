# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009, 2018-2021 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2018 Laurent Monin
# Copyright (C) 2014 Wieland Hoffmann
# Copyright (C) 2017 Sambhav Kothari
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
    BoolOption,
    TextOption,
    get_config,
)
from picard.const import ALIAS_LOCALES

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
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
        yield (locale, name, 0)
        for name, locale in sorted(grouped_locales.get(locale, [])):
            yield (locale, name, 1)


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
        TextOption("setting", "artist_locale", "en"),
        BoolOption("setting", "translate_artist_names", False),
        BoolOption("setting", "release_ars", True),
        BoolOption("setting", "track_ars", False),
        BoolOption("setting", "convert_punctuation", True),
        BoolOption("setting", "standardize_artists", False),
        BoolOption("setting", "standardize_instruments", True),
        BoolOption("setting", "originaldate_use_recording", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MetadataOptionsPage()
        self.ui.setupUi(self)
        self.ui.va_name_default.clicked.connect(self.set_va_name_default)
        self.ui.nat_name_default.clicked.connect(self.set_nat_name_default)

    def load(self):
        config = get_config()
        self.ui.translate_artist_names.setChecked(config.setting["translate_artist_names"])

        combo_box = self.ui.artist_locale
        current_locale = config.setting["artist_locale"]
        for i, (locale, name, level) in enumerate(iter_sorted_locales(ALIAS_LOCALES)):
            label = "    " * level + name
            combo_box.addItem(label, locale)
            if locale == current_locale:
                combo_box.setCurrentIndex(i)

        self.ui.convert_punctuation.setChecked(config.setting["convert_punctuation"])
        self.ui.release_ars.setChecked(config.setting["release_ars"])
        self.ui.track_ars.setChecked(config.setting["track_ars"])
        self.ui.va_name.setText(config.setting["va_name"])
        self.ui.nat_name.setText(config.setting["nat_name"])
        self.ui.standardize_artists.setChecked(config.setting["standardize_artists"])
        self.ui.standardize_instruments.setChecked(config.setting["standardize_instruments"])
        if config.setting["originaldate_use_recording"]:
            self.ui.originaldate_use_recording.setChecked(True)
        else:
            self.ui.originaldate_use_releasegroup.setChecked(True)

    def save(self):
        config = get_config()
        config.setting["translate_artist_names"] = self.ui.translate_artist_names.isChecked()
        config.setting["artist_locale"] = self.ui.artist_locale.itemData(self.ui.artist_locale.currentIndex())
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
        config.setting["originaldate_use_recording"] = self.ui.originaldate_use_recording.isChecked()

    def set_va_name_default(self):
        self.ui.va_name.setText(self.options[0].default)
        self.ui.va_name.setCursorPosition(0)

    def set_nat_name_default(self):
        self.ui.nat_name.setText(self.options[1].default)
        self.ui.nat_name.setCursorPosition(0)


register_options_page(MetadataOptionsPage)

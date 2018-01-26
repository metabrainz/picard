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

from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_metadata import Ui_MetadataOptionsPage
from picard.const import ALIAS_LOCALES


class MetadataOptionsPage(OptionsPage):

    NAME = "metadata"
    TITLE = N_("Metadata")
    PARENT = None
    SORT_ORDER = 20
    ACTIVE = True

    options = [
        config.TextOption("setting", "va_name", "Various Artists"),
        config.TextOption("setting", "nat_name", "[non-album tracks]"),
        config.TextOption("setting", "artist_locale", "en"),
        config.BoolOption("setting", "translate_artist_names", False),
        config.BoolOption("setting", "release_ars", True),
        config.BoolOption("setting", "track_ars", False),
        config.BoolOption("setting", "folksonomy_tags", False),
        config.BoolOption("setting", "convert_punctuation", True),
        config.BoolOption("setting", "standardize_artists", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MetadataOptionsPage()
        self.ui.setupUi(self)
        self.ui.va_name_default.clicked.connect(self.set_va_name_default)
        self.ui.nat_name_default.clicked.connect(self.set_nat_name_default)

    def load(self):
        self.ui.translate_artist_names.setChecked(config.setting["translate_artist_names"])

        combo_box = self.ui.artist_locale
        locales = sorted(ALIAS_LOCALES.keys())
        for i, loc in enumerate(locales):
            name = ALIAS_LOCALES[loc]
            if "_" in loc:
                name = "    " + name
            combo_box.addItem(name, loc)
            if loc == config.setting["artist_locale"]:
                combo_box.setCurrentIndex(i)

        self.ui.convert_punctuation.setChecked(config.setting["convert_punctuation"])
        self.ui.release_ars.setChecked(config.setting["release_ars"])
        self.ui.track_ars.setChecked(config.setting["track_ars"])
        self.ui.folksonomy_tags.setChecked(config.setting["folksonomy_tags"])
        self.ui.va_name.setText(config.setting["va_name"])
        self.ui.nat_name.setText(config.setting["nat_name"])
        self.ui.standardize_artists.setChecked(config.setting["standardize_artists"])

    def save(self):
        config.setting["translate_artist_names"] = self.ui.translate_artist_names.isChecked()
        config.setting["artist_locale"] = self.ui.artist_locale.itemData(self.ui.artist_locale.currentIndex())
        config.setting["convert_punctuation"] = self.ui.convert_punctuation.isChecked()
        config.setting["release_ars"] = self.ui.release_ars.isChecked()
        config.setting["track_ars"] = self.ui.track_ars.isChecked()
        config.setting["folksonomy_tags"] = self.ui.folksonomy_tags.isChecked()
        config.setting["va_name"] = self.ui.va_name.text()
        nat_name = self.ui.nat_name.text()
        if nat_name != config.setting["nat_name"]:
            config.setting["nat_name"] = nat_name
            if self.tagger.nats is not None:
                self.tagger.nats.update()
        config.setting["standardize_artists"] = self.ui.standardize_artists.isChecked()

    def set_va_name_default(self):
        self.ui.va_name.setText(self.options[0].default)
        self.ui.va_name.setCursorPosition(0)

    def set_nat_name_default(self):
        self.ui.nat_name.setText(self.options[1].default)
        self.ui.nat_name.setCursorPosition(0)


register_options_page(MetadataOptionsPage)

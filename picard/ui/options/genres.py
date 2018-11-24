# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2008 Lukáš Lalinský
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

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_genres import Ui_GenresOptionsPage


class GenresOptionsPage(OptionsPage):

    NAME = "genres"
    TITLE = N_("Genres")
    PARENT = "metadata"
    SORT_ORDER = 20
    ACTIVE = True

    options = [
        config.BoolOption("setting", "use_genres", False),
        config.IntOption("setting", "max_genres", 5),
        config.IntOption("setting", "min_genre_usage", 90),
        config.TextOption("setting", "ignore_genres", "seen live, favorites, fixme, owned"),
        config.TextOption("setting", "join_genres", ""),
        config.BoolOption("setting", "only_my_genres", False),
        config.BoolOption("setting", "artists_genres", False),
        config.BoolOption("setting", "folksonomy_tags", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GenresOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.use_genres.setChecked(config.setting["use_genres"])
        self.ui.max_genres.setValue(config.setting["max_genres"])
        self.ui.min_genre_usage.setValue(config.setting["min_genre_usage"])
        self.ui.join_genres.setEditText(config.setting["join_genres"])
        self.ui.ignore_genres.setText(config.setting["ignore_genres"])
        self.ui.only_my_genres.setChecked(config.setting["only_my_genres"])
        self.ui.artists_genres.setChecked(config.setting["artists_genres"])
        self.ui.folksonomy_tags.setChecked(config.setting["folksonomy_tags"])

    def save(self):
        config.setting["use_genres"] = self.ui.use_genres.isChecked()
        config.setting["max_genres"] = self.ui.max_genres.value()
        config.setting["min_genre_usage"] = self.ui.min_genre_usage.value()
        config.setting["join_genres"] = self.ui.join_genres.currentText()
        config.setting["ignore_genres"] = self.ui.ignore_genres.text()
        config.setting["only_my_genres"] = self.ui.only_my_genres.isChecked()
        config.setting["artists_genres"] = self.ui.artists_genres.isChecked()
        config.setting["folksonomy_tags"] = self.ui.folksonomy_tags.isChecked()


register_options_page(GenresOptionsPage)

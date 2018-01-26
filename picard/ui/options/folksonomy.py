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
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_folksonomy import Ui_FolksonomyOptionsPage


class FolksonomyOptionsPage(OptionsPage):

    NAME = "folsonomy"
    TITLE = N_("Folksonomy Tags")
    PARENT = "metadata"
    SORT_ORDER = 20
    ACTIVE = True

    options = [
        config.IntOption("setting", "max_tags", 5),
        config.IntOption("setting", "min_tag_usage", 90),
        config.TextOption("setting", "ignore_tags", "seen live,favorites,fixme,owned"),
        config.TextOption("setting", "join_tags", ""),
        config.BoolOption("setting", "only_my_tags", False),
        config.BoolOption("setting", "artists_tags", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_FolksonomyOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.max_tags.setValue(config.setting["max_tags"])
        self.ui.min_tag_usage.setValue(config.setting["min_tag_usage"])
        self.ui.join_tags.setEditText(config.setting["join_tags"])
        self.ui.ignore_tags.setText(config.setting["ignore_tags"])
        self.ui.only_my_tags.setChecked(config.setting["only_my_tags"])
        self.ui.artists_tags.setChecked(config.setting["artists_tags"])

    def save(self):
        config.setting["max_tags"] = self.ui.max_tags.value()
        config.setting["min_tag_usage"] = self.ui.min_tag_usage.value()
        config.setting["join_tags"] = self.ui.join_tags.currentText()
        config.setting["ignore_tags"] = self.ui.ignore_tags.text()
        config.setting["only_my_tags"] = self.ui.only_my_tags.isChecked()
        config.setting["artists_tags"] = self.ui.artists_tags.isChecked()


register_options_page(FolksonomyOptionsPage)

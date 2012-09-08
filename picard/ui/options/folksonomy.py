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

from picard.config import BoolOption, TextOption, IntOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_folksonomy import Ui_FolksonomyOptionsPage


class FolksonomyOptionsPage(OptionsPage):

    NAME = "folsonomy"
    TITLE = N_("Folksonomy Tags")
    PARENT = "metadata"
    SORT_ORDER = 20
    ACTIVE = True

    options = [
        IntOption("setting", "max_tags", 5),
        IntOption("setting", "min_tag_usage", 90),
        TextOption("setting", "ignore_tags", "seen live,favorites,fixme,owned"),
        TextOption("setting", "join_tags", ""),
        BoolOption("setting", "only_my_tags", False),
    ]

    def __init__(self, parent=None):
        super(FolksonomyOptionsPage, self).__init__(parent)
        self.ui = Ui_FolksonomyOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.max_tags.setValue(self.config.setting["max_tags"])
        self.ui.min_tag_usage.setValue(self.config.setting["min_tag_usage"])
        self.ui.join_tags.setEditText(self.config.setting["join_tags"])
        self.ui.ignore_tags.setText(self.config.setting["ignore_tags"])
        self.ui.only_my_tags.setChecked(self.config.setting["only_my_tags"])

    def save(self):
        self.config.setting["max_tags"] = self.ui.max_tags.value()
        self.config.setting["min_tag_usage"] = self.ui.min_tag_usage.value()
        self.config.setting["join_tags"] = self.ui.join_tags.currentText()
        self.config.setting["ignore_tags"] = self.ui.ignore_tags.text()
        self.config.setting["only_my_tags"] = self.ui.only_my_tags.isChecked()


register_options_page(FolksonomyOptionsPage)

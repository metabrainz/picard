# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

from picard.config import BoolOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_interface import Ui_InterfaceOptionsPage


class InterfaceOptionsPage(OptionsPage):

    NAME = "interface"
    TITLE = N_("User Interface")
    PARENT = "advanced"
    SORT_ORDER = 40
    ACTIVE = True

    options = [
        BoolOption("setting", "toolbar_show_labels", True),
        BoolOption("setting", "toolbar_multiselect", False),
        BoolOption("setting", "show_hidden_files", False),
        BoolOption("setting", "use_adv_search_syntax", False),
    ]

    def __init__(self, parent=None):
        super(InterfaceOptionsPage, self).__init__(parent)
        self.ui = Ui_InterfaceOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.toolbar_show_labels.setChecked(self.config.setting["toolbar_show_labels"])
        self.ui.toolbar_multiselect.setChecked(self.config.setting["toolbar_multiselect"])
        self.ui.show_hidden_files.setChecked(self.config.setting["show_hidden_files"])
        self.ui.use_adv_search_syntax.setChecked(self.config.setting["use_adv_search_syntax"])

    def save(self):
        self.config.setting["toolbar_show_labels"] = self.ui.toolbar_show_labels.isChecked()
        self.config.setting["toolbar_multiselect"] = self.ui.toolbar_multiselect.isChecked()
        self.config.setting["show_hidden_files"] = self.ui.show_hidden_files.isChecked()
        self.config.setting["use_adv_search_syntax"] = self.ui.use_adv_search_syntax.isChecked()
        self.tagger.window.update_toolbar_style()
        self.tagger.window.file_browser.show_hidden(self.config.setting["show_hidden_files"])


register_options_page(InterfaceOptionsPage)

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
    ]

    def __init__(self, parent=None):
        super(InterfaceOptionsPage, self).__init__(parent)
        self.ui = Ui_InterfaceOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.toolbar_show_labels.setChecked(self.config.setting["toolbar_show_labels"])

    def save(self):
        self.config.setting["toolbar_show_labels"] = self.ui.toolbar_show_labels.isChecked()
        self.tagger.window.update_toolbar_style()


register_options_page(InterfaceOptionsPage)

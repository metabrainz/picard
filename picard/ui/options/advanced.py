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

from PyQt4.QtGui import QPalette, QColor
import re

from picard import config
from picard.ui.options import OptionsPage, OptionsCheckError, register_options_page
from picard.ui.ui_options_advanced import Ui_AdvancedOptionsPage


class AdvancedOptionsPage(OptionsPage):

    NAME = "advanced"
    TITLE = N_("Advanced")
    PARENT = None
    SORT_ORDER = 90
    ACTIVE = True

    options = [
        config.TextOption("setting", "ignore_regex", ""),
    ]

    def __init__(self, parent=None):
        super(AdvancedOptionsPage, self).__init__(parent)
        self.ui = Ui_AdvancedOptionsPage()
        self.ui.setupUi(self)
        self.ui.ignore_regex.textChanged.connect(self.live_checker)

    def load(self):
        self.ui.ignore_regex.setText(config.setting["ignore_regex"])

    def save(self):
        config.setting["ignore_regex"] = unicode(self.ui.ignore_regex.text())

    def live_checker(self, text):
        self.ui.regex_error.setStyleSheet("")
        self.ui.regex_error.setText("")
        try:
            self.check()
        except OptionsCheckError as e:
            self.ui.regex_error.setStyleSheet(self.STYLESHEET_ERROR)
            self.ui.regex_error.setText(e.info)
            return

    def check(self):
        try:
            re.compile(unicode(self.ui.ignore_regex.text()))
        except re.error as e:
            raise OptionsCheckError(_("Regex Error"), str(e))


register_options_page(AdvancedOptionsPage)

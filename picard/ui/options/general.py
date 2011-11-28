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

from picard.config import IntOption, TextOption, BoolOption, PasswordOption
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_general import Ui_GeneralOptionsPage
from picard.util import rot13


class GeneralOptionsPage(OptionsPage):

    NAME = "general"
    TITLE = N_("General")
    PARENT = None
    SORT_ORDER = 1
    ACTIVE = True

    options = [
        TextOption("setting", "server_host", "musicbrainz.org"),
        IntOption("setting", "server_port", 80),
        TextOption("setting", "username", ""),
        PasswordOption("setting", "password", ""),
        BoolOption("setting", "analyze_new_files", False),
        BoolOption("setting", "ignore_file_mbids", False),
    ]

    def __init__(self, parent=None):
        super(GeneralOptionsPage, self).__init__(parent)
        self.ui = Ui_GeneralOptionsPage()
        self.ui.setupUi(self)
        mirror_servers = [
            "musicbrainz.org",
            ]
        self.ui.server_host.addItems(sorted(mirror_servers))

    def load(self):
        self.ui.server_host.setEditText(self.config.setting["server_host"])
        self.ui.server_port.setValue(self.config.setting["server_port"])
        self.ui.username.setText(self.config.setting["username"])
        self.ui.password.setText(self.config.setting["password"])
        self.ui.analyze_new_files.setChecked(self.config.setting["analyze_new_files"])
        self.ui.ignore_file_mbids.setChecked(self.config.setting["ignore_file_mbids"])

    def save(self):
        self.config.setting["server_host"] = unicode(self.ui.server_host.currentText()).strip()
        self.config.setting["server_port"] = self.ui.server_port.value()
        self.config.setting["username"] = unicode(self.ui.username.text())
        # trivially encode the password, just to not make it so apparent
        self.config.setting["password"] = rot13(unicode(self.ui.password.text()))
        self.config.setting["analyze_new_files"] = self.ui.analyze_new_files.isChecked()
        self.config.setting["ignore_file_mbids"] = self.ui.ignore_file_mbids.isChecked()


register_options_page(GeneralOptionsPage)

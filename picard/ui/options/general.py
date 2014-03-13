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
from picard.ui.ui_options_general import Ui_GeneralOptionsPage
from picard.util import rot13
from picard.const import MUSICBRAINZ_SERVERS
from picard.collection import load_user_collections


class GeneralOptionsPage(OptionsPage):

    NAME = "general"
    TITLE = N_("General")
    PARENT = None
    SORT_ORDER = 1
    ACTIVE = True

    options = [
        config.TextOption("setting", "server_host", MUSICBRAINZ_SERVERS[0]),
        config.IntOption("setting", "server_port", 80),
        config.TextOption("setting", "username", ""),
        config.PasswordOption("setting", "password", ""),
        config.BoolOption("setting", "analyze_new_files", False),
        config.BoolOption("setting", "ignore_file_mbids", False),
    ]

    def __init__(self, parent=None):
        super(GeneralOptionsPage, self).__init__(parent)
        self.ui = Ui_GeneralOptionsPage()
        self.ui.setupUi(self)
        self.ui.server_host.addItems(MUSICBRAINZ_SERVERS)

    def load(self):
        self.ui.server_host.setEditText(config.setting["server_host"])
        self.ui.server_port.setValue(config.setting["server_port"])
        self.ui.username.setText(config.setting["username"])
        self.ui.password.setText(config.setting["password"])
        self.ui.analyze_new_files.setChecked(config.setting["analyze_new_files"])
        self.ui.ignore_file_mbids.setChecked(config.setting["ignore_file_mbids"])

    def save(self):
        config.setting["server_host"] = unicode(self.ui.server_host.currentText()).strip()
        config.setting["server_port"] = self.ui.server_port.value()
        reload_collections = config.setting["username"] != unicode(self.ui.username.text()) \
                         or config.setting["password"] != unicode(self.ui.password.text())
        config.setting["username"] = unicode(self.ui.username.text())
        # trivially encode the password, just to not make it so apparent
        config.setting["password"] = rot13(unicode(self.ui.password.text()))
        if reload_collections:
            load_user_collections()
        config.setting["analyze_new_files"] = self.ui.analyze_new_files.isChecked()
        config.setting["ignore_file_mbids"] = self.ui.ignore_file_mbids.isChecked()

register_options_page(GeneralOptionsPage)

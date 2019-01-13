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

from PyQt5 import QtCore

from picard import config
from picard.const import (
    MUSICBRAINZ_SERVERS,
    PROGRAM_UPDATE_LEVELS,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_general import Ui_GeneralOptionsPage


class GeneralOptionsPage(OptionsPage):

    NAME = "general"
    TITLE = N_("General")
    PARENT = None
    SORT_ORDER = 1
    ACTIVE = True

    options = [
        config.TextOption("setting", "server_host", MUSICBRAINZ_SERVERS[0]),
        config.IntOption("setting", "server_port", 443),
        config.TextOption("persist", "oauth_refresh_token", ""),
        config.BoolOption("setting", "analyze_new_files", False),
        config.BoolOption("setting", "ignore_file_mbids", False),
        config.TextOption("persist", "oauth_refresh_token", ""),
        config.TextOption("persist", "oauth_refresh_token_scopes", ""),
        config.TextOption("persist", "oauth_access_token", ""),
        config.IntOption("persist", "oauth_access_token_expires", 0),
        config.TextOption("persist", "oauth_username", ""),
        config.BoolOption("setting", "check_for_updates", True),
        config.IntOption("setting", "update_check_days", 7),
        config.IntOption("setting", "update_level", 0),
        config.IntOption("persist", "last_update_check", 0),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GeneralOptionsPage()
        self.ui.setupUi(self)
        self.ui.server_host.addItems(MUSICBRAINZ_SERVERS)
        self.ui.login.clicked.connect(self.login)
        self.ui.logout.clicked.connect(self.logout)
        self.update_login_logout()

    def load(self):
        self.ui.server_host.setEditText(config.setting["server_host"])
        self.ui.server_port.setValue(config.setting["server_port"])
        self.ui.analyze_new_files.setChecked(config.setting["analyze_new_files"])
        self.ui.ignore_file_mbids.setChecked(config.setting["ignore_file_mbids"])
        if self.tagger.autoupdate_enabled:
            self.ui.check_for_updates.setChecked(config.setting["check_for_updates"])
            self.ui.update_level.clear()
            for level, description in PROGRAM_UPDATE_LEVELS.items():
                # TODO: Remove temporary workaround once https://github.com/python-babel/babel/issues/415 has been resolved.
                babel_415_workaround = description['title']
                self.ui.update_level.addItem(_(babel_415_workaround), level)
            self.ui.update_level.setCurrentIndex(self.ui.update_level.findData(config.setting["update_level"]))
            self.ui.update_check_days.setValue(config.setting["update_check_days"])
        else:
            self.ui.update_check_groupbox.hide()

    def save(self):
        config.setting["server_host"] = self.ui.server_host.currentText().strip()
        config.setting["server_port"] = self.ui.server_port.value()
        config.setting["analyze_new_files"] = self.ui.analyze_new_files.isChecked()
        config.setting["ignore_file_mbids"] = self.ui.ignore_file_mbids.isChecked()
        if self.tagger.autoupdate_enabled:
            config.setting["check_for_updates"] = self.ui.check_for_updates.isChecked()
            config.setting["update_level"] = self.ui.update_level.currentData(QtCore.Qt.UserRole)
            config.setting["update_check_days"] = self.ui.update_check_days.value()

    def update_login_logout(self):
        if self.tagger.webservice.oauth_manager.is_logged_in():
            self.ui.logged_in.setText(_("Logged in as <b>%s</b>.") % config.persist["oauth_username"])
            self.ui.logged_in.show()
            self.ui.login.hide()
            self.ui.logout.show()
        else:
            self.ui.logged_in.hide()
            self.ui.login.show()
            self.ui.logout.hide()

    def login(self):
        self.tagger.mb_login(self.on_login_finished, self)

    def restore_defaults(self):
        super().restore_defaults()
        self.logout()

    def on_login_finished(self, successful):
        self.update_login_logout()

    def logout(self):
        self.tagger.mb_logout()
        self.update_login_logout()


register_options_page(GeneralOptionsPage)

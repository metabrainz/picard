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

from PyQt5.QtWidgets import QInputDialog
from picard import config
from picard.util import webbrowser2
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_general import Ui_GeneralOptionsPage
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
        config.IntOption("setting", "server_port", 443),
        config.TextOption("persist", "oauth_refresh_token", ""),
        config.BoolOption("setting", "analyze_new_files", False),
        config.BoolOption("setting", "ignore_file_mbids", False),
        config.TextOption("persist", "oauth_refresh_token", ""),
        config.TextOption("persist", "oauth_refresh_token_scopes", ""),
        config.TextOption("persist", "oauth_access_token", ""),
        config.IntOption("persist", "oauth_access_token_expires", 0),
        config.TextOption("persist", "oauth_username", ""),
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

    def save(self):
        config.setting["server_host"] = self.ui.server_host.currentText().strip()
        config.setting["server_port"] = self.ui.server_port.value()
        config.setting["analyze_new_files"] = self.ui.analyze_new_files.isChecked()
        config.setting["ignore_file_mbids"] = self.ui.ignore_file_mbids.isChecked()

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
        scopes = "profile tag rating collection submit_isrc submit_barcode"
        authorization_url = self.tagger.webservice.oauth_manager.get_authorization_url(scopes)
        webbrowser2.open(authorization_url)
        authorization_code, ok = QInputDialog.getText(self,
            _("MusicBrainz Account"), _("Authorization code:"))
        if ok:
            self.tagger.webservice.oauth_manager.exchange_authorization_code(
                authorization_code, scopes, self.on_authorization_finished)

    def restore_defaults(self):
        super().restore_defaults()
        self.logout()

    def on_authorization_finished(self, successful):
        if successful:
            self.tagger.webservice.oauth_manager.fetch_username(
                self.on_login_finished)

    def on_login_finished(self, successful):
        self.update_login_logout()
        if successful:
            load_user_collections()

    def logout(self):
        self.tagger.webservice.oauth_manager.revoke_tokens()
        self.update_login_logout()
        load_user_collections()


register_options_page(GeneralOptionsPage)

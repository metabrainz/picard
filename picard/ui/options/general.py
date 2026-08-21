# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014 Lukáš Lalinský
# Copyright (C) 2008, 2018-2026 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2011, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2026 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2023, 2025-2026 Bob Swift
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import ClassVar

from PyQt6 import QtWidgets

from picard import log
from picard.collection import load_user_collections
from picard.config import get_config
from picard.const import MUSICBRAINZ_SERVERS
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util.mbserver import is_official_server

from picard.ui.colors import stylesheet_validation_error
from picard.ui.forms.ui_options_general import Ui_GeneralOptionsPage
from picard.ui.options import (
    OptionsPage,
    PageOptionConfigs,
)


class GeneralOptionsPage(OptionsPage):
    NAME = 'general'
    TITLE = N_("General")
    PARENT = None
    SORT_ORDER = 1
    ACTIVE = True
    HELP_URL = "/config/options_general.html"

    OPTIONS: ClassVar[PageOptionConfigs] = {
        'server_host': {'widgets': ['server_host']},
        'server_port': {'widgets': ['server_port']},
        'use_server_for_submission': {'widgets': ['use_server_for_submission']},
        'enable_user_collections': {'widgets': ['enable_user_collections']},
        'remove_complete_albums_after_save': {'widgets': ['remove_complete_albums_after_save']},
    }

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_GeneralOptionsPage()
        self.ui.setupUi(self)
        self.ui.server_host.addItems(MUSICBRAINZ_SERVERS)
        self.ui.server_host.currentTextChanged.connect(self.update_server_host)
        self.ui.login.clicked.connect(self.login)
        self.ui.logout.clicked.connect(self.logout)
        self.ui.login_error.setStyleSheet(stylesheet_validation_error())
        self.ui.login_error.hide()
        self.tagger.webservice.authorization_state_changed.connect(self.update_login_logout)
        self.update_login_logout()

    def load(self):
        config = get_config()
        self.ui.server_host.setEditText(config.setting['server_host'])
        self.ui.server_port.setValue(config.setting['server_port'])
        self.ui.use_server_for_submission.setChecked(config.setting['use_server_for_submission'])
        self.update_server_host()
        self.ui.enable_user_collections.setChecked(config.setting['enable_user_collections'])
        self.ui.remove_complete_albums_after_save.setChecked(config.setting['remove_complete_albums_after_save'])

    def save(self):
        config = get_config()
        config.setting['server_host'] = self.ui.server_host.currentText().strip()
        config.setting['server_port'] = self.ui.server_port.value()
        config.setting['use_server_for_submission'] = self.ui.use_server_for_submission.isChecked()
        config.setting['remove_complete_albums_after_save'] = self.ui.remove_complete_albums_after_save.isChecked()
        self._update_user_collections(config, self.ui.enable_user_collections.isChecked())

    def _update_user_collections(self, config, new_enable_user_collections):
        old_enable_user_collections = config.setting['enable_user_collections']
        config.setting['enable_user_collections'] = new_enable_user_collections
        if old_enable_user_collections != new_enable_user_collections and new_enable_user_collections:
            load_user_collections()

    def update_server_host(self):
        host = self.ui.server_host.currentText().strip()
        if host and is_official_server(host):
            self.ui.server_host_primary_warning.hide()
        else:
            self.ui.server_host_primary_warning.show()

    def update_login_logout(self, error_msg=None):
        if self.deleted:
            return
        oauth_manager = self.tagger.webservice.oauth_manager
        log.debug(
            "update_login_logout: is_logged_in=%s, is_authorized=%s, username=%r, error_msg=%r",
            oauth_manager.is_logged_in(),
            oauth_manager.is_authorized(),
            oauth_manager.username,
            error_msg,
        )
        if oauth_manager.is_logged_in():
            config = get_config()
            self.ui.logged_in.setText(_("Logged in as <b>%s</b>.") % config.persist['oauth_username'])
            self.ui.logged_in.show()
            self.ui.login_error.hide()
            self.ui.login.hide()
            self.ui.logout.show()
        elif error_msg:
            self.ui.logged_in.hide()
            self.ui.login_error.setText(_("Login failed: %s") % error_msg)
            self.ui.login_error.show()
            self.ui.login.show()
            self.ui.logout.hide()
        else:
            self.ui.logged_in.hide()
            self.ui.login_error.hide()
            self.ui.login.show()
            self.ui.logout.hide()

    def login(self):
        self.tagger.mb_login(self.on_login_finished, self)

    def on_login_finished(self, successful, error_msg=None):
        self.update_login_logout(error_msg)

    def logout(self):
        self.tagger.mb_logout(self.on_logout_finished)

    def on_logout_finished(self, successful, error_msg=None):
        if not successful:
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setWindowTitle(_("Logout error"))
            msg.setText(
                _(
                    "A server error occurred while revoking access to the MusicBrainz server: %s\n"
                    "\n"
                    "Remove locally stored credentials anyway?"
                )
                % error_msg
            )
            msg.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Retry
            )
            result = msg.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                oauth_manager = self.tagger.webservice.oauth_manager
                oauth_manager.forget_access_token()
                oauth_manager.forget_refresh_token()
            elif result == QtWidgets.QMessageBox.StandardButton.Retry:
                self.logout()
        self.update_login_logout()

    def restore_defaults(self):
        super().restore_defaults()
        self.logout()


register_options_page(GeneralOptionsPage)

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2014 Lukáš Lalinský
# Copyright (C) 2008, 2018-2025 Philipp Wolfer
# Copyright (C) 2011, 2013 Michael Wiencek
# Copyright (C) 2011, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014 Sophist-UK
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2023 Bob Swift
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


from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from picard.tagger import Tagger



import logging
from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.config import get_config
from picard.const import (
    MUSICBRAINZ_SERVERS,
    PROGRAM_UPDATE_LEVELS,
)
from picard.const.defaults import DEFAULT_PROGRAM_UPDATE_LEVEL
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
    gettext_constants,
)
from picard.util.mbserver import is_official_server

from picard.ui.forms.ui_options_general import Ui_GeneralOptionsPage
from picard.ui.options import OptionsPage



class GeneralOptionsPage(OptionsPage):
    """
    Options page for general settings in Picard.
    Provides the UI and logic for configuring server, updates, and file analysis.
    """

    NAME: str = 'general'
    TITLE: str = N_("General")
    PARENT: None = None
    SORT_ORDER: int = 1
    ACTIVE: bool = True
    HELP_URL: str = "/config/options_general.html"

    OPTIONS: tuple[tuple[str, list[str]], ...] = (
        ('server_host', ['server_host']),
        ('server_port', ['server_port']),
        ('analyze_new_files', ['analyze_new_files']),
        ('cluster_new_files', ['cluster_new_files']),
        ('ignore_file_mbids', ['ignore_file_mbids']),
        ('check_for_plugin_updates', ['check_for_plugin_updates']),
        ('check_for_updates', ['check_for_updates']),
        ('update_check_days', ['update_check_days']),
        ('update_level', ['update_level']),
        ('use_server_for_submission', ['use_server_for_submission']),
    )

    ui: Ui_GeneralOptionsPage
    deleted: bool = False
    tagger: 'Tagger'

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """
        Initialize the GeneralOptionsPage and connect UI elements to logic.
        :param parent: The parent widget.
        """
        super().__init__(parent=parent)
        self.ui = Ui_GeneralOptionsPage()
        self.ui.setupUi(self)
        self.ui.server_host.addItems(MUSICBRAINZ_SERVERS)
        self.ui.server_host.currentTextChanged.connect(self.update_server_host)
        self.ui.login.clicked.connect(self.login)
        self.ui.logout.clicked.connect(self.logout)
        self.ui.analyze_new_files.toggled.connect(self._update_cluster_new_files)
        self.ui.cluster_new_files.toggled.connect(self._update_analyze_new_files)
        self.ui.login_error.setStyleSheet(self.STYLESHEET_ERROR)
        self.ui.login_error.hide()
        self.update_login_logout()

    def load(self) -> None:
        """
        Load current settings from the configuration and update the UI accordingly.
        Adds error handling and logging for config and UI access.
        """
        logger = logging.getLogger(__name__)
        try:
            config = get_config()
            self.ui.server_host.setEditText(config.setting['server_host'])
            self.ui.server_port.setValue(config.setting['server_port'])
            self.ui.use_server_for_submission.setChecked(config.setting['use_server_for_submission'])
            self.update_server_host()
            self.ui.analyze_new_files.setChecked(config.setting['analyze_new_files'])
            self.ui.cluster_new_files.setChecked(config.setting['cluster_new_files'])
            self.ui.ignore_file_mbids.setChecked(config.setting['ignore_file_mbids'])
            self.ui.check_for_plugin_updates.setChecked(config.setting['check_for_plugin_updates'])
            self.ui.check_for_updates.setChecked(config.setting['check_for_updates'])
            self.set_update_level(config.setting['update_level'])
            self.ui.update_check_days.setValue(config.setting['update_check_days'])
            if not self.tagger.autoupdate_enabled:
                self.ui.program_update_check_group.hide()
            logger.info("General options loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading general options: {e}")

    def set_update_level(self, value: str) -> None:
        """
        Set the update level in the UI based on the value from the configuration.
        :param value: The desired update level.
        """
        if value not in PROGRAM_UPDATE_LEVELS:
            value = DEFAULT_PROGRAM_UPDATE_LEVEL
        self.ui.update_level.clear()
        for level, description in PROGRAM_UPDATE_LEVELS.items():
            self.ui.update_level.addItem(gettext_constants(description['title']), level)
        idx = self.ui.update_level.findData(value)
        if idx == -1:
            idx = self.ui.update_level.findData(DEFAULT_PROGRAM_UPDATE_LEVEL)
        self.ui.update_level.setCurrentIndex(idx)

    def save(self) -> None:
        """
        Save the current settings from the UI to the configuration.
        Adds error handling and logging for config and UI access.
        """
        logger = logging.getLogger(__name__)
        try:
            config = get_config()
            config.setting['server_host'] = self.ui.server_host.currentText().strip()
            config.setting['server_port'] = self.ui.server_port.value()
            config.setting['use_server_for_submission'] = self.ui.use_server_for_submission.isChecked()
            config.setting['analyze_new_files'] = self.ui.analyze_new_files.isChecked()
            config.setting['cluster_new_files'] = self.ui.cluster_new_files.isChecked()
            config.setting['ignore_file_mbids'] = self.ui.ignore_file_mbids.isChecked()
            config.setting['check_for_plugin_updates'] = self.ui.check_for_plugin_updates.isChecked()
            config.setting['check_for_updates'] = self.ui.check_for_updates.isChecked()
            config.setting['update_level'] = self.ui.update_level.currentData(QtCore.Qt.ItemDataRole.UserRole)
            config.setting['update_check_days'] = self.ui.update_check_days.value()
            logger.info("General options saved successfully.")
        except Exception as e:
            logger.error(f"Error saving general options: {e}")

    def update_server_host(self) -> None:
        """
        Check if the selected server is an official MusicBrainz server and show a warning if not.
        """
        host = self.ui.server_host.currentText().strip()
        if host and is_official_server(host):
            self.ui.server_host_primary_warning.hide()
        else:
            self.ui.server_host_primary_warning.show()

    def update_login_logout(self, error_msg: Optional[str] = None) -> None:
        """
        Update the UI for login/logout status and show error messages if needed.
        :param error_msg: Optional error message for failed login.
        """
        if self.deleted:
            return
        if self.tagger.webservice.oauth_manager.is_logged_in():
            config = get_config()
            self.ui.logged_in.setText(_("Logged in as <b>%s</b>.") % config.persist['oauth_username'])
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

    def login(self) -> None:
        """
        Start the login process via the tagger webservice API.
        Adds logging for login attempts.
        """
        logger = logging.getLogger(__name__)
        logger.info("Attempting user login.")
        self.tagger.mb_login(self.on_login_finished, self)

    def on_login_finished(self, successful: bool, error_msg: Optional[str] = None) -> None:
        """
        Callback after login attempt, updates the UI accordingly.
        Adds logging for login result.
        :param successful: Whether the login was successful.
        :param error_msg: Error message for failed login.
        """
        logger = logging.getLogger(__name__)
        if successful:
            logger.info("User login successful.")
        else:
            logger.error(f"User login failed: {error_msg}")
        self.update_login_logout(error_msg)

    def logout(self) -> None:
        """
        Start the logout process via the tagger webservice API.
        Adds logging for logout attempts.
        """
        logger = logging.getLogger(__name__)
        logger.info("Attempting user logout.")
        self.tagger.mb_logout(self.on_logout_finished)

    def on_logout_finished(self, successful: bool, error_msg: Optional[str] = None) -> None:
        """
        Callback after logout attempt, handles errors and updates the UI.
        Adds logging for logout result.
        :param successful: Whether the logout was successful.
        :param error_msg: Error message for failed logout.
        """
        logger = logging.getLogger(__name__)
        if successful:
            logger.info("User logout successful.")
        else:
            logger.error(f"User logout failed: {error_msg}")
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setWindowTitle(_("Logout error"))
            msg.setText(_(
                "A server error occurred while revoking access to the MusicBrainz server: %s\n"
                "\n"
                "Remove locally stored credentials anyway?"
            ) % error_msg)
            msg.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No
                | QtWidgets.QMessageBox.StandardButton.Retry)
            result = msg.exec()
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                oauth_manager = self.tagger.webservice.oauth_manager
                oauth_manager.forget_access_token()
                oauth_manager.forget_refresh_token()
            elif result == QtWidgets.QMessageBox.StandardButton.Retry:
                self.logout()
        self.update_login_logout()

    def restore_defaults(self) -> None:
        """
        Reset settings to default values and log out the user.
        """
        super().restore_defaults()
        self.logout()

    def _update_analyze_new_files(self, cluster_new_files: bool) -> None:
        """
        Disable the "analyze_new_files" option when "cluster_new_files" is enabled.
        :param cluster_new_files: State of "cluster_new_files".
        """
        if cluster_new_files:
            self.ui.analyze_new_files.setChecked(False)

    def _update_cluster_new_files(self, analyze_new_files: bool) -> None:
        """
        Disable the "cluster_new_files" option when "analyze_new_files" is enabled.
        :param analyze_new_files: State of "analyze_new_files".
        """
        if analyze_new_files:
            self.ui.cluster_new_files.setChecked(False)


register_options_page(GeneralOptionsPage)

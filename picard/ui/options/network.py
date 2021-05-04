# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013, 2018, 2020 Laurent Monin
# Copyright (C) 2013, 2020-2021 Philipp Wolfer
# Copyright (C) 2016-2017 Sambhav Kothari
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


from picard.config import (
    BoolOption,
    IntOption,
    TextOption,
    get_config,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_network import Ui_NetworkOptionsPage


class NetworkOptionsPage(OptionsPage):

    NAME = "network"
    TITLE = N_("Network")
    PARENT = "advanced"
    SORT_ORDER = 10
    ACTIVE = True
    HELP_URL = '/config/options_network.html'

    options = [
        BoolOption("setting", "use_proxy", False),
        TextOption("setting", "proxy_type", "http"),
        TextOption("setting", "proxy_server_host", ""),
        IntOption("setting", "proxy_server_port", 80),
        TextOption("setting", "proxy_username", ""),
        TextOption("setting", "proxy_password", ""),
        BoolOption("setting", "browser_integration", True),
        IntOption("setting", "browser_integration_port", 8000),
        BoolOption("setting", "browser_integration_localhost_only", True),
        IntOption("setting", "network_transfer_timeout_seconds", 30),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_NetworkOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.web_proxy.setChecked(config.setting["use_proxy"])
        if config.setting["proxy_type"] == 'socks':
            self.ui.proxy_type_socks.setChecked(True)
        else:
            self.ui.proxy_type_http.setChecked(True)
        self.ui.server_host.setText(config.setting["proxy_server_host"])
        self.ui.server_port.setValue(config.setting["proxy_server_port"])
        self.ui.username.setText(config.setting["proxy_username"])
        self.ui.password.setText(config.setting["proxy_password"])
        self.ui.transfer_timeout.setValue(config.setting["network_transfer_timeout_seconds"])
        self.ui.browser_integration.setChecked(config.setting["browser_integration"])
        self.ui.browser_integration_port.setValue(config.setting["browser_integration_port"])
        self.ui.browser_integration_localhost_only.setChecked(
            config.setting["browser_integration_localhost_only"])

    def save(self):
        config = get_config()
        config.setting["use_proxy"] = self.ui.web_proxy.isChecked()
        if self.ui.proxy_type_socks.isChecked():
            config.setting["proxy_type"] = 'socks'
        else:
            config.setting["proxy_type"] = 'http'
        config.setting["proxy_server_host"] = self.ui.server_host.text()
        config.setting["proxy_server_port"] = self.ui.server_port.value()
        config.setting["proxy_username"] = self.ui.username.text()
        config.setting["proxy_password"] = self.ui.password.text()
        self.tagger.webservice.setup_proxy()
        transfer_timeout = self.ui.transfer_timeout.value()
        config.setting["network_transfer_timeout_seconds"] = transfer_timeout
        self.tagger.webservice.set_transfer_timeout(transfer_timeout)
        config.setting["browser_integration"] = self.ui.browser_integration.isChecked()
        config.setting["browser_integration_port"] = self.ui.browser_integration_port.value()
        config.setting["browser_integration_localhost_only"] = \
            self.ui.browser_integration_localhost_only.isChecked()
        self.update_browser_integration()

    def update_browser_integration(self):
        if self.ui.browser_integration.isChecked():
            self.tagger.browser_integration.start()
        else:
            self.tagger.browser_integration.stop()


register_options_page(NetworkOptionsPage)

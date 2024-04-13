# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013, 2018, 2020-2021, 2023-2024 Laurent Monin
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
    BoolSetting,
    IntSetting,
    TextSetting,
    get_config,
)
from picard.const import (
    CACHE_SIZE_DISPLAY_UNIT,
    CACHE_SIZE_IN_BYTES,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.ui.ui_options_network import Ui_NetworkOptionsPage


class NetworkOptionsPage(OptionsPage):

    NAME = 'network'
    TITLE = N_("Network")
    PARENT = 'advanced'
    SORT_ORDER = 10
    ACTIVE = True
    HELP_URL = "/config/options_network.html"

    options = [
        BoolSetting('use_proxy', False, title=N_("Use a web proxy server")),
        TextSetting('proxy_type', 'http', title=N_("Type of proxy server")),
        TextSetting('proxy_server_host', '', title=N_("Proxy server address")),
        IntSetting('proxy_server_port', 80, title=N_("Proxy server port")),
        TextSetting('proxy_username', '', title=N_("Proxy username")),
        TextSetting('proxy_password', '', title=N_("Proxy password")),
        BoolSetting('browser_integration', True, title=N_("Browser integration")),
        IntSetting('browser_integration_port', 8000, title=N_("Default listening port")),
        BoolSetting('browser_integration_localhost_only', True, title=N_("Listen only on localhost")),
        IntSetting('network_transfer_timeout_seconds', 30, title=N_("Request timeout in seconds")),
        IntSetting('network_cache_size_bytes', CACHE_SIZE_IN_BYTES, title=N_("Network cache size in bytes")),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_NetworkOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.ui.web_proxy.setChecked(config.setting['use_proxy'])
        if config.setting['proxy_type'] == 'socks':
            self.ui.proxy_type_socks.setChecked(True)
        else:
            self.ui.proxy_type_http.setChecked(True)
        self.ui.server_host.setText(config.setting['proxy_server_host'])
        self.ui.server_port.setValue(config.setting['proxy_server_port'])
        self.ui.username.setText(config.setting['proxy_username'])
        self.ui.password.setText(config.setting['proxy_password'])
        self.ui.transfer_timeout.setValue(config.setting['network_transfer_timeout_seconds'])
        self.ui.browser_integration.setChecked(config.setting['browser_integration'])
        self.ui.browser_integration_port.setValue(config.setting['browser_integration_port'])
        self.ui.browser_integration_localhost_only.setChecked(
            config.setting['browser_integration_localhost_only'])
        self.cachesize2display(config)

    def save(self):
        config = get_config()
        config.setting['use_proxy'] = self.ui.web_proxy.isChecked()
        if self.ui.proxy_type_socks.isChecked():
            config.setting['proxy_type'] = 'socks'
        else:
            config.setting['proxy_type'] = 'http'
        config.setting['proxy_server_host'] = self.ui.server_host.text()
        config.setting['proxy_server_port'] = self.ui.server_port.value()
        config.setting['proxy_username'] = self.ui.username.text()
        config.setting['proxy_password'] = self.ui.password.text()
        self.tagger.webservice.setup_proxy()
        transfer_timeout = self.ui.transfer_timeout.value()
        config.setting['network_transfer_timeout_seconds'] = transfer_timeout
        self.tagger.webservice.set_transfer_timeout(transfer_timeout)
        config.setting['browser_integration'] = self.ui.browser_integration.isChecked()
        config.setting['browser_integration_port'] = self.ui.browser_integration_port.value()
        config.setting['browser_integration_localhost_only'] = \
            self.ui.browser_integration_localhost_only.isChecked()
        self.tagger.update_browser_integration()
        self.display2cachesize(config)

    def display2cachesize(self, config):
        try:
            cache_size = int(self.ui.network_cache_size.text())
        except ValueError:
            return
        config.setting['network_cache_size_bytes'] = int(cache_size * CACHE_SIZE_DISPLAY_UNIT)
        self.tagger.webservice.set_cache_size()

    def cachesize2display(self, config):
        cache_size = self.tagger.webservice.get_valid_cache_size()
        value = int(cache_size / CACHE_SIZE_DISPLAY_UNIT)
        self.ui.network_cache_size.setText(str(value))


register_options_page(NetworkOptionsPage)

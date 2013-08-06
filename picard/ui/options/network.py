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

from PyQt4 import QtCore
from picard import config
from picard.ui.options import OptionsPage, register_options_page
from picard.ui.ui_options_network import Ui_NetworkOptionsPage


class NetworkOptionsPage(OptionsPage):

    NAME = "network"
    TITLE = N_("Network")
    PARENT = "advanced"
    SORT_ORDER = 10
    ACTIVE = True

    options = [
        config.BoolOption("setting", "use_proxy", False),
        config.TextOption("setting", "proxy_server_host", ""),
        config.IntOption("setting", "proxy_server_port", 80),
        config.TextOption("setting", "proxy_username", ""),
        config.TextOption("setting", "proxy_password", ""),
        config.BoolOption("setting", "browser_integration", True),
        config.IntOption("setting", "browser_integration_port", 8000),
    ]

    def __init__(self, parent=None):
        super(NetworkOptionsPage, self).__init__(parent)
        self.ui = Ui_NetworkOptionsPage()
        self.ui.setupUi(self)
        self.ui.browser_integration.clicked.connect(self.update_browser_integration)

    def load(self):
        self.ui.web_proxy.setChecked(config.setting["use_proxy"])
        self.ui.server_host.setText(config.setting["proxy_server_host"])
        self.ui.server_port.setValue(config.setting["proxy_server_port"])
        self.ui.username.setText(config.setting["proxy_username"])
        self.ui.password.setText(config.setting["proxy_password"])
        self.ui.browser_integration.setChecked(config.setting["browser_integration"])
        self.ui.browser_integration_port.setValue(config.setting["browser_integration_port"])
        QtCore.QObject.connect(self.ui.browser_integration_port,
                               QtCore.SIGNAL('valueChanged(int)'),
                               self.change_browser_integration_port)

    def save(self):
        config.setting["use_proxy"] = self.ui.web_proxy.isChecked()
        config.setting["proxy_server_host"] = unicode(self.ui.server_host.text())
        config.setting["proxy_server_port"] = self.ui.server_port.value()
        config.setting["proxy_username"] = unicode(self.ui.username.text())
        config.setting["proxy_password"] = unicode(self.ui.password.text())
        self.tagger.xmlws.setup_proxy()
        config.setting["browser_integration"] = self.ui.browser_integration.isChecked()
        config.setting["browser_integration_port"] = self.ui.browser_integration_port.value()

    def update_browser_integration(self):
        if self.ui.browser_integration.isChecked():
            self.tagger.browser_integration.start()
        else:
            self.tagger.browser_integration.stop()

    def change_browser_integration_port(self, port):
        config.setting["browser_integration_port"] = self.ui.browser_integration_port.value()


register_options_page(NetworkOptionsPage)

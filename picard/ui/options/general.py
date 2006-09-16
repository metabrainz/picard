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

from PyQt4 import QtCore, QtGui
from picard.api import IOptionsPage
from picard.component import Component, implements
from picard.config import BoolOption, IntOption, TextOption

class GeneralOptionsPage(Component):

    implements(IOptionsPage)

    options = [
        TextOption("setting", "server_host", "musicbrainz.org"),
        IntOption("setting", "server_port", 80),
        TextOption("setting", "username", ""),
        TextOption("setting", "password", ""),
    ]

    def get_page_info(self):
        return _(u"General"), "general", None, 1

    def get_page_widget(self, parent=None):
        from picard.ui.ui_options_general import Ui_Form
        self.widget = QtGui.QWidget(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self.widget)
        self.ui.server_host.setText(self.config.setting["server_host"])
        self.ui.server_port.setValue(self.config.setting["server_port"])
        self.ui.username.setText(self.config.setting["username"])
        self.ui.password.setText(self.config.setting["password"])
        return self.widget

    def save_options(self):
        self.config.setting["server_host"] = unicode(self.ui.server_host.text())
        self.config.setting["server_port"] = self.ui.server_port.value()
        self.config.setting["username"] = unicode(self.ui.username.text())
        self.config.setting["password"] = unicode(self.ui.password.text())

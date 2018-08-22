# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2008 Philipp Wolfer
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

from picard.ui import PicardDialog
from picard.ui.ui_passworddialog import Ui_PasswordDialog


class PasswordDialog(PicardDialog):

    def __init__(self, authenticator, reply, parent=None):
        super().__init__(parent)
        self._authenticator = authenticator
        self.ui = Ui_PasswordDialog()
        self.ui.setupUi(self)
        self.ui.info_text.setText(
            _("The server %s requires you to login. Please enter your username and password.") %
            reply.url().host())
        self.ui.username.setText(reply.url().userName())
        self.ui.password.setText(reply.url().password())
        self.ui.buttonbox.accepted.connect(self.set_new_password)

    def set_new_password(self):
        self._authenticator.setUser(self.ui.username.text())
        self._authenticator.setPassword(self.ui.password.text())
        self.accept()


class ProxyDialog(PicardDialog):

    def __init__(self, authenticator, proxy, parent=None):
        super().__init__(parent)
        self._authenticator = authenticator
        self._proxy = proxy
        self.ui = Ui_PasswordDialog()
        self.ui.setupUi(self)
        self.ui.info_text.setText(_("The proxy %s requires you to login. Please enter your username and password.")
                                  % config.setting["proxy_server_host"])
        self.ui.username.setText(config.setting["proxy_username"])
        self.ui.password.setText(config.setting["proxy_password"])
        self.ui.buttonbox.accepted.connect(self.set_proxy_password)

    def set_proxy_password(self):
        config.setting["proxy_username"] = self.ui.username.text()
        config.setting["proxy_password"] = self.ui.password.text()
        self._authenticator.setUser(self.ui.username.text())
        self._authenticator.setPassword(self.ui.password.text())
        self.accept()

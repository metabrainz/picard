# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008, 2021 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2012, 2014 Lukáš Lalinský
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013-2014, 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
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


from picard.config import get_config
from picard.i18n import gettext as _

from picard.ui import PicardDialog
from picard.ui.forms.ui_passworddialog import Ui_PasswordDialog


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
        config = get_config()
        self.ui.info_text.setText(_("The proxy %s requires you to login. Please enter your username and password.")
                                  % config.setting['proxy_server_host'])
        self.ui.username.setText(config.setting['proxy_username'])
        self.ui.password.setText(config.setting['proxy_password'])
        self.ui.buttonbox.accepted.connect(self.set_proxy_password)

    def set_proxy_password(self):
        config = get_config()
        config.setting['proxy_username'] = self.ui.username.text()
        config.setting['proxy_password'] = self.ui.password.text()
        self._authenticator.setUser(self.ui.username.text())
        self._authenticator.setPassword(self.ui.password.text())
        self.accept()

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
from picard.ui.ui_passworddialog import Ui_PasswordDialog
from picard.config import Option, BoolOption
from picard.const import PUID_SUBMIT_HOST, PUID_SUBMIT_PORT

class PasswordDialog(QtGui.QDialog):

    options = [
        BoolOption("persist", "save_authentication", True),
    ]

    def __init__(self, authenticator, host, port, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self._authenticator = authenticator
        self.ui = Ui_PasswordDialog()
        self.ui.setupUi(self)
        self.ui.info_text.setText(_("The server %s requires you to login. Please enter your username and password.") % host)
        # TODO: Implement proper password storage for arbitrary servers
        if self._is_musicbrainz_server(host, port):
            self.ui.save_authentication.setChecked(self.config.persist["save_authentication"])
            self.ui.username.setText(self.config.setting["username"])
            self.ui.password.setText(self.config.setting["password"])
        else:
            self.ui.save_authentication.setChecked(False)
            self.ui.save_authentication.hide()
        self.connect(self.ui.buttonbox, QtCore.SIGNAL('accepted()'), self.set_new_password)
        
    def set_new_password(self):
        self.config.persist["save_authentication"] = self.ui.save_authentication.isChecked()
        if self.config.persist["save_authentication"]:
            self.config.setting["username"] = unicode(self.ui.username.text())
            self.config.setting["password"] = unicode(self.ui.password.text()).encode('rot13')
        self._authenticator.setUser(unicode(self.ui.username.text()))
        self._authenticator.setPassword(unicode(self.ui.password.text()))
        self.accept()
        
    def _is_musicbrainz_server(self, host, port):
        return host == self.config.setting["server_host"] and port == self.config.setting["server_port"] \
            or host == PUID_SUBMIT_HOST and port == PUID_SUBMIT_PORT
        

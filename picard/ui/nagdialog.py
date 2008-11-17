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

from PyQt4 import QtCore, QtGui
from picard.ui.ui_nagdialog import Ui_NagDialog
from picard.util import webbrowser2
import random


class NagDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_NagDialog()
        self.ui.setupUi(self)
        
        if (random.randint(0, 25) == 17):
            self.ui.info_text.setText('Please consider donating high quality chocolate for using this tagger application. Mail chocolate to:\n\nMetaBrainz Foundation\n3565 South Higuera St, Suite B\nSan Luis Obispo, CA 93401\nUnited States')
        
        self.ui.button_box.addButton(_('Donate'), QtGui.QDialogButtonBox.YesRole)
        self.ui.button_box.addButton(_('Later'), QtGui.QDialogButtonBox.NoRole)
        self.connect(self.ui.button_box, QtCore.SIGNAL('accepted()'), self.donate)
        self.connect(self.ui.button_box, QtCore.SIGNAL('rejected()'), self.reject)
        
    def donate(self):
        webbrowser2.open('http://metabrainz.org/donate/index.html')
        self.accept()
        
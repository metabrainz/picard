# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

# for people who really can't install Qt 4.2 :(
if not hasattr(QtGui, 'QDialogButtonBox'):
    class FakeQDialogButtonBox(QtGui.QWidget):
        AcceptRole = 0
        RejectRole = 1
        HelpRole = 4
        def __init__(self, parent=None):
            QtGui.QWidget.__init__(self, parent)
            self.hbox = QtGui.QHBoxLayout(self)
            self.hbox.setMargin(0)
            self.hbox.addStretch()
        def setOrientation(self, orientation):
            pass
        def addButton(self, button, role):
            self.hbox.addWidget(button)
            if role == self.AcceptRole:
                self.connect(button, QtCore.SIGNAL('clicked()'), self, QtCore.SIGNAL('accepted()'))
            elif role == self.RejectRole:
                self.connect(button, QtCore.SIGNAL('clicked()'), self, QtCore.SIGNAL('rejected()'))
            elif role == self.HelpRole:
                self.connect(button, QtCore.SIGNAL('clicked()'), self, QtCore.SIGNAL('helpRequested()'))
    QtGui.QDialogButtonBox = FakeQDialogButtonBox

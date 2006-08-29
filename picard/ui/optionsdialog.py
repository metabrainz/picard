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

class OptionsDialog(QtGui.QDialog):
    
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()
        
    def setupUi(self):
        self.setWindowTitle(_("Options"))
        
        self.splitter = QtGui.QSplitter(self)
        
        self.treeWidget = QtGui.QTreeWidget(self.splitter)
        self.splitter.addWidget(self.treeWidget)
        self.splitter.addWidget(QtGui.QWidget())
        
        self.okButton = QtGui.QPushButton(_("OK"), self)
        self.connect(self.okButton, QtCore.SIGNAL("clicked()"), self.onOk)
        self.cancelButton = QtGui.QPushButton(_("Cancel"), self)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.onCancel)
        
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton, 0)
        buttonLayout.addWidget(self.cancelButton, 0)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.splitter)
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)
        
    def onOk(self):
        print "ok"
        self.close()
        
    def onCancel(self):
        print "cancel"
        self.close()

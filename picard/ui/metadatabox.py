# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
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

class MetadataBox(QtGui.QGroupBox):
    
    def __init__(self, parent, title):
        QtGui.QGroupBox.__init__(self, title)
        self.metadata = None
        self.setupUi()
    
    def setupUi(self):
        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setSpacing(2)

        
        self.titleEdit = QtGui.QLineEdit(self)
        self.artistEdit = QtGui.QLineEdit(self)
        self.albumEdit = QtGui.QLineEdit(self)        
        #self.titleEdit = QtGui.QComboBox(self)
        #self.titleEdit.addItem(u"The Prodigy")
        #self.titleEdit.addItem(u"Faithless")
        #self.titleEdit.setEditable(True)
        #self.titleEdit.setAutoCompletion(True)
        #self.titleEdit.lineEdit().setText(u"")
        
        #self.artistEdit = QtGui.QComboBox(self)
        #self.artistEdit.setEditable(True)
        
        #self.albumEdit = QtGui.QComboBox(self)
        #self.albumEdit.setEditable(True)
        
        self.gridlayout.addWidget(QtGui.QLabel(_("Title:")), 0, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.titleEdit, 0, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Artist:")), 1, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.artistEdit, 1, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Album:")), 2, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.albumEdit, 2, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Track#:")), 3, 0, QtCore.Qt.AlignRight)

        self.trackNumEdit = QtGui.QLineEdit(self)
        sizePolicy = self.trackNumEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(2)
        self.trackNumEdit.setSizePolicy(sizePolicy)
        
        self.timeEdit = QtGui.QLineEdit(self)
        sizePolicy = self.timeEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(2)
        self.timeEdit.setSizePolicy(sizePolicy)
        
        #self.dateEdit = QtGui.QDateEdit(self)
        self.dateEdit = QtGui.QLineEdit(self)
        self.dateEdit.setInputMask("0000-00-00")
        sizePolicy = self.dateEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(4)
        self.dateEdit.setSizePolicy(sizePolicy)
        
        self.gridlayout.addWidget(self.trackNumEdit, 3, 1)
        self.gridlayout.addWidget(QtGui.QLabel(_("Time:")), 3, 2, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.timeEdit, 3, 3)
        self.gridlayout.addWidget(QtGui.QLabel(_("Date:")), 3, 4, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.dateEdit, 3, 5)
        
        self.lookupButton = QtGui.QPushButton(_("Lookup"), self)
        self.connect(self.lookupButton, QtCore.SIGNAL("clicked()"), self.lookup)
        
        self.gridlayout.addWidget(self.lookupButton, 3, 6)
        
        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLineEdit(self), 1)
        #hbox.addWidget(QtGui.QLabel(_("Genre:")), 0)
        #hbox.addWidget(QtGui.QLineEdit(self), 2)
        #self.gridlayout.addLayout(hbox, 4, 1, 1, 5)

        self.vbox = QtGui.QVBoxLayout(self)
        self.vbox.addLayout(self.gridlayout, 0)
        self.vbox.addStretch(1)

    def setDisabled(self, val):
        self.titleEdit.setDisabled(val)
        self.artistEdit.setDisabled(val)
        self.albumEdit.setDisabled(val)
        self.trackNumEdit.setDisabled(val)
        self.timeEdit.setDisabled(val)
        self.dateEdit.setDisabled(val)                
        self.lookupButton.setDisabled(val)

    def setTitle(self, text):
        self.titleEdit.setText(text)

    def setArtist(self, text):
        self.artistEdit.setText(text)

    def setAlbum(self, text):
        self.albumEdit.setText(text)

    def clear(self):
        self.setTitle(u"")
        self.setArtist(u"")
        self.setAlbum(u"")
        
    def setMetadata(self, metadata):
        self.metadata = metadata
        
    def lookup(self):
        self.emit(QtCore.SIGNAL("lookup"), self.metadata)


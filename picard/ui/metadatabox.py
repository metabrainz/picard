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
from picard.util import formatTime

class MetadataBox(QtGui.QGroupBox):
    
    def __init__(self, parent, title, readOnly=False):
        QtGui.QGroupBox.__init__(self, title)
        self.metadata = None
        self.readOnly = readOnly
        self.setupUi()

    def setupUi(self):
        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.setSpacing(2)

        self.titleEdit = QtGui.QLineEdit(self)
        self.titleEdit.setReadOnly(self.readOnly)

        self.artistEdit = QtGui.QLineEdit(self)
        self.artistEdit.setReadOnly(self.readOnly)

        self.albumEdit = QtGui.QLineEdit(self)        
        self.albumEdit.setReadOnly(self.readOnly)

        self.trackNumEdit = QtGui.QLineEdit(self)
        self.trackNumEdit.setReadOnly(self.readOnly)
        sizePolicy = self.trackNumEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(2)
        self.trackNumEdit.setSizePolicy(sizePolicy)

        self.lengthEdit = QtGui.QLineEdit(self)
        self.lengthEdit.setReadOnly(True)
        sizePolicy = self.lengthEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(2)
        self.lengthEdit.setSizePolicy(sizePolicy)

        self.dateEdit = QtGui.QLineEdit(self)
        self.dateEdit.setReadOnly(self.readOnly)
        self.dateEdit.setInputMask("0000-00-00")
        sizePolicy = self.dateEdit.sizePolicy()
        sizePolicy.setHorizontalStretch(4)
        self.dateEdit.setSizePolicy(sizePolicy)

        self.gridlayout.addWidget(QtGui.QLabel(_("Title:")), 0, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.titleEdit, 0, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Artist:")), 1, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.artistEdit, 1, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Album:")), 2, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.albumEdit, 2, 1, 1, 6)
        self.gridlayout.addWidget(QtGui.QLabel(_("Track#:")), 3, 0, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.trackNumEdit, 3, 1)
        self.gridlayout.addWidget(QtGui.QLabel(_("Time:")), 3, 2, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.lengthEdit, 3, 3)
        self.gridlayout.addWidget(QtGui.QLabel(_("Date:")), 3, 4, QtCore.Qt.AlignRight)
        self.gridlayout.addWidget(self.dateEdit, 3, 5)

        self.lookupButton = QtGui.QPushButton(_("Lookup"), self)
        self.connect(self.lookupButton, QtCore.SIGNAL("clicked()"), self.lookup)

        self.gridlayout.addWidget(self.lookupButton, 3, 6)

        self.vbox = QtGui.QVBoxLayout(self)
        self.vbox.addLayout(self.gridlayout, 0)
        self.vbox.addStretch(1)

    def setDisabled(self, val):
        self.titleEdit.setDisabled(val)
        self.artistEdit.setDisabled(val)
        self.albumEdit.setDisabled(val)
        self.trackNumEdit.setDisabled(val)
        self.lengthEdit.setDisabled(val)
        self.dateEdit.setDisabled(val)                
        self.lookupButton.setDisabled(val)

    def clear(self):
        self.titleEdit.clear()
        self.artistEdit.clear()
        self.albumEdit.clear()
        self.lengthEdit.clear()
        self.trackNumEdit.clear()
        self.dateEdit.clear()

    def setMetadata(self, metadata):
        self.metadata = metadata
        if metadata:
            text = metadata.get(u"TITLE", u"")
            self.titleEdit.setText(text)
            text = metadata.get(u"ARTIST", u"")
            self.artistEdit.setText(text)
            text = metadata.get(u"ALBUM", u"")
            self.albumEdit.setText(text)
            text = metadata.get(u"TRACKNUMBER", u"")
            self.trackNumEdit.setText(text)
            text = formatTime(metadata.get("~#length", 0))
            self.lengthEdit.setText(text)
            text = metadata.get(u"DATE", u"")
            self.dateEdit.setText(text)
        else:
            self.clear()

    def lookup(self):
        self.emit(QtCore.SIGNAL("lookup"), self.metadata)


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

class CoverArtBox(QtGui.QGroupBox):
    
    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, _("Cover Art"))
        self.setupUi()

    def test(self):
        self.emit(QtCore.SIGNAL("TestSignal"), 1, 4)
        
    def setupUi(self):
        self.layout = QtGui.QVBoxLayout()
        
        #cover = QtGui.QPixmap("cover.jpg")
        #cover = cover.scaled(105, 105, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation);
        
        img = QtGui.QPixmap(":/images/CoverArtShadow.png")
        #painter = QtGui.QPainter(img)
        #painter.drawPixmap(1,1,cover)
        #painter.end()
        
        self.coverArt = QtGui.QLabel()
        self.coverArt.setPixmap(img)
        self.coverArt.setAlignment(QtCore.Qt.AlignTop)
        
        #amazonLayout = QtGui.QHBoxLayout()
        
        #self.amazonBuyLabel = QtGui.QLabel('<a href="http://www.amazon.com/">Buy</a> | <a href="http://www.amazon.com/">Info</a>')
        #self.amazonBuyLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        #self.amazonInfoLabel = QtGui.QLabel('')
        #self.amazonInfoLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        
        #amazonLayout.addWidget(self.amazonBuyLabel)
        #amazonLayout.addWidget(self.amazonInfoLabel)
        
        self.layout.addWidget(self.coverArt, 0)        
        #self.layout.addWidget(self.amazonBuyLabel, 1)        
        self.setLayout(self.layout)
        

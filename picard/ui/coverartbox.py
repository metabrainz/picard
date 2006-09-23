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

class CoverArtBox(QtGui.QGroupBox):

    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, _("Cover Art"))
        self.layout = QtGui.QVBoxLayout()
        self.data = None
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.coverArt = QtGui.QLabel()
        self.coverArt.setPixmap(self.shadow)
        self.coverArt.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addWidget(self.coverArt, 0)        
        self.setLayout(self.layout)

    def show(self):
        self.__set_data(self.data, True)
        QtGui.QGroupBox.show(self)

    def __set_data(self, data, force=False):
        if not force and self.data == data:
            return

        self.data = data
        if not force and self.isHidden():
            return

        if self.data:
            cover = QtGui.QPixmap(self.shadow)
            pixmap = QtGui.QPixmap(105, 105)
            pixmap.loadFromData(self.data)
            pixmap = pixmap.scaled(105, 105, QtCore.Qt.IgnoreAspectRatio,
                                   QtCore.Qt.SmoothTransformation)
            painter = QtGui.QPainter(cover)
            painter.drawPixmap(1, 1, pixmap)
            painter.end()
            self.coverArt.setPixmap(cover)
        else:
            self.coverArt.setPixmap(self.shadow)

    def set_metadata(self, metadata):
        data = None
        if metadata and "~artwork" in metadata:
            data = metadata["~artwork"][0][1]
        self.__set_data(data)


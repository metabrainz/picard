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


class RatingWidget(QtGui.QWidget):

    def __init__(self, parent=None, rating=0, maximum=5):
        super(RatingWidget, self).__init__(parent)
        self._maximum = maximum
        self._rating = rating
        self._highlight = 0
        
        self._starSize = 15
        self._starSpacing = 4
        
        self.setMouseTracking(True)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                                             QtGui.QSizePolicy.Minimum))
        
    def setRating(self, rating):
        assert 0 <= rating <= self._maximum
        if rating != self._rating:
            self._rating = rating
            self.update()
        
    def getRating(self):
        return self._rating
    
    def _setHighlight(self, highlight):
        assert 0 <= highlight <= self._maximum
        if highlight != self._highlight:
            self._highlight = highlight
            self.update()
        
    def setMaximum(self, maximum):
        assert maximum > 0
        self._maximum = maximum
        if self._rating > self._maximum:
            self._rating = self._maximum
        self.updateGeometry()
        self.update()
        
    def getMaximum(self):
        return self._maximum
    
    def sizeHint(self):
        return self.minimumSizeHint()
    
    def minimumSizeHint(self):
        return QtCore.QSize(self._maximum * (self._starSize + self._starSpacing),
                            self._starSize)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            rating = self._getRatingFromPosition(event.x())
            if self._rating == rating:
                rating = 0
            self.setRating(rating)
            event.accept()
        else:
            QWidget.mousePressEvent(self, event)
            
    def mouseMoveEvent(self, event):
        self._setHighlight(self._getRatingFromPosition(event.x()))
        event.accept()
        
    def leaveEvent(self, event):
        self._setHighlight(0)
        event.accept()
        
    def _getRatingFromPosition(self, position):
        rating = int(position / (self._starSize + self._starSpacing)) + 1
        if rating > self._maximum:
            rating = self._maximum
        return rating
        
    def paintEvent(self, event=None):
        # FIXME: Draw prettier stars, maybe use some nice bitmaps
        painter =  QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(self.palette().color(QtGui.QPalette.Light))
        offset = 0
        for i in range(1, self._maximum+1):
            if (i <= self._rating):
                painter.setBrush(self.palette().color(QtGui.QPalette.Highlight))
            elif (i <= self._highlight):
                painter.setBrush(self.palette().color(QtGui.QPalette.Mid))
            else:
                painter.setBrush(self.palette().color(QtGui.QPalette.Light))
            self._drawStar(painter, offset)
            offset += self._starSize + self._starSpacing
            
    def _drawStar(self, painter, offset):
        painter.drawPolygon(QtCore.QPointF(offset + self._starSize*0.50, 0),
                            QtCore.QPointF(offset + self._starSize*0.63, self._starSize*0.37),
                            QtCore.QPointF(offset + self._starSize,      self._starSize*0.38),
                            QtCore.QPointF(offset + self._starSize*0.71, self._starSize*0.62),
                            QtCore.QPointF(offset + self._starSize*0.82, self._starSize),
                            QtCore.QPointF(offset + self._starSize*0.50, self._starSize*0.78),
                            QtCore.QPointF(offset + self._starSize*0.18, self._starSize),
                            QtCore.QPointF(offset + self._starSize*0.30, self._starSize*0.62),
                            QtCore.QPointF(offset + 0,                   self._starSize*0.38),
                            QtCore.QPointF(offset + self._starSize*0.37, self._starSize*0.37))

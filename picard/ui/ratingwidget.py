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

from PyQt5 import QtCore, QtGui, QtWidgets
from picard import config


class RatingWidget(QtWidgets.QWidget):

    def __init__(self, parent, track):
        super().__init__(parent)
        self._track = track
        self._maximum = config.setting["rating_steps"] - 1
        self._rating = int(track.metadata["~rating"] or 0)
        self._highlight = 0
        self._star_pixmap = QtGui.QPixmap(":/images/star.png")
        self._star_gray_pixmap = QtGui.QPixmap(":/images/star-gray.png")
        self._star_size = 16
        self._star_spacing = 2
        self._offset = 16
        self._width = self._maximum * (self._star_size + self._star_spacing) + self._offset
        self._height = self._star_size + 6
        self.setMaximumSize(self._width, self._height)
        self.setMinimumSize(self._width, self._height)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.setMouseTracking(True)

    def sizeHint(self):
        return QtCore.QSize(self._width, self._height)

    def _setHighlight(self, highlight):
        assert 0 <= highlight <= self._maximum
        if highlight != self._highlight:
            self._highlight = highlight
            self.update()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            x = event.x()
            if x < self._offset:
                return
            rating = self._getRatingFromPosition(x)
            if self._rating == rating:
                rating = 0
            self._rating = rating
            self._update_track()
            self.update()
            event.accept()

    def mouseMoveEvent(self, event):
        self._setHighlight(self._getRatingFromPosition(event.x()))
        event.accept()

    def leaveEvent(self, event):
        self._setHighlight(0)
        event.accept()

    def _getRatingFromPosition(self, position):
        rating = int((position - self._offset) / (self._star_size + self._star_spacing)) + 1
        if rating > self._maximum:
            rating = self._maximum
        return rating

    def _update_track(self):
        track = self._track
        track.metadata["~rating"] = string_(self._rating)
        if config.setting["submit_ratings"]:
            ratings = {("recording", track.id): self._rating}
            self.tagger.mb_api.submit_ratings(ratings, None)

    def paintEvent(self, event=None):
        painter = QtGui.QPainter(self)
        offset = self._offset
        for i in range(1, self._maximum + 1):
            if i <= self._rating or i <= self._highlight:
                pixmap = self._star_pixmap
            else:
                pixmap = self._star_gray_pixmap
            painter.drawPixmap(offset, 3, pixmap)
            offset += self._star_size + self._star_spacing

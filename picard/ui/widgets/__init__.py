# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)


class ElidedLabel(QtWidgets.QLabel):
    """A QLabel that elides the displayed text with ellipsis when resized."""

    def __init__(self, parent=None):
        self._full_label = ""
        super().__init__(parent)

    def setText(self, text):
        self._full_label = text
        self._update_text()

    def resizeEvent(self, event):
        self._update_text()

    def _update_text(self):
        metrics = QtGui.QFontMetrics(self.font())
        # Elide the text. On some setups, e.g. using the Breeze theme, the
        # text does not properly fit into width(), as a workaround subtract
        # 2 pixels from the available width.
        elided_label = metrics.elidedText(self._full_label,
                                          QtCore.Qt.ElideRight,
                                          self.width() - 2)
        super().setText(elided_label)

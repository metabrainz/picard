# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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
        if self._full_label and elided_label != self._full_label:
            self.setToolTip(self._full_label)
        else:
            self.setToolTip("")


class ActiveLabel(QtWidgets.QLabel):
    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()

    def __init__(self, active=True, drops=False, *args):
        super().__init__(*args)
        self.setActive(active)

    def setActive(self, active):
        self.active = active
        if self.active:
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.setCursor(QtGui.QCursor())

    def mouseReleaseEvent(self, event):
        if self.active and event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()


class ClickableSlider(QtWidgets.QSlider):
    """A slider implementation where the user can select any slider position by clicking."""

    def mousePressEvent(self, event):
        self._set_position_from_mouse_event(event)

    def mouseMoveEvent(self, event):
        self._set_position_from_mouse_event(event)

    def _set_position_from_mouse_event(self, event):
        value = QtWidgets.QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), event.x(), self.width())
        self.setValue(value)


class Popover(QtWidgets.QFrame):
    """A generic popover implementation.

    The popover opens relative to its parent, either above or below the parent.
    Subclass this widget and add child widgets for a custom popover.
    """

    def __init__(self, parent, position='bottom'):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.position = position

    def show(self):
        super().show()
        self.update_position()

    def update_position(self):
        parent = self.parent()
        x = -(self.width() - parent.width()) / 2
        if self.position == 'top':
            y = -self.height()
        else:  # bottom
            y = parent.height()
        pos = parent.mapToGlobal(QtCore.QPoint(x, y))
        screen_number = QtWidgets.QApplication.desktop().screenNumber()
        screen = QtGui.QGuiApplication.screens()[screen_number]
        screen_size = screen.availableVirtualSize()
        if pos.x() < 0:
            pos.setX(0)
        if pos.x() + self.width() > screen_size.width():
            pos.setX(screen_size.width() - self.width())
        if pos.y() < 0:
            pos.setY(0)
        if pos.y() + self.height() > screen_size.height():
            pos.setY(screen_size.height() - self.height())
        self.move(pos)


class SliderPopover(Popover):
    """A popover containing a single slider."""

    value_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent, position, label, value):
        super().__init__(parent, position)
        vbox = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(label, self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self.label)

        self.slider = ClickableSlider(self)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(self.value_changed)
        vbox.addWidget(self.slider)

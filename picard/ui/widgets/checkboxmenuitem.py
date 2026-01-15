# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

from PyQt6 import (
    QtGui,
    QtWidgets,
)


class CheckboxMenuItem(QtWidgets.QWidget):
    def __init__(self, menu: QtWidgets.QMenu, action: QtGui.QAction, text: str, parent=None):
        super().__init__(parent=parent)
        self._menu = menu
        action.setCheckable(True)
        self._action = action
        self._active = False
        self._setup_layout(text)
        self._menu.hovered.connect(self._on_hover)
        self._action.changed.connect(self._action_changed)
        self.checkbox.toggled.connect(self._action.setChecked)

    def _setup_layout(self, text: str):
        layout = QtWidgets.QVBoxLayout(self)
        style = self.style()
        layout.setContentsMargins(
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutLeftMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameVMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_LayoutRightMargin),
            style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameVMargin),
        )
        layout.addStretch(1)
        self.checkbox = self._create_checkbox_widget(text)
        layout.addWidget(self.checkbox)

    def _action_changed(self):
        self.checkbox.setChecked(self._action.isChecked())

    def _create_checkbox_widget(self, text: str):
        return QtWidgets.QCheckBox(text, parent=self)

    def _on_hover(self, action: QtGui.QAction):
        active = action == self._action
        self.set_active(active)
        if active:
            self.checkbox.setFocus()

    def set_active(self, active: bool):
        self._active = active
        palette = self.palette()
        if active:
            textcolor = palette.highlightedText().color()
        else:
            textcolor = palette.text().color()
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, textcolor)
        self.checkbox.setPalette(palette)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.checkbox.setDown(True)
        event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self.checkbox.isDown():
            self.checkbox.toggle()
        self.checkbox.setDown(False)
        event.accept()

    def enterEvent(self, e):
        self._menu.setActiveAction(self._action)
        self.set_active(True)

    def leaveEvent(self, e):
        self.set_active(False)

    def paintEvent(self, e):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        option.state = QtWidgets.QStyle.StateFlag.State_None
        if self.isEnabled():
            option.state |= QtWidgets.QStyle.StateFlag.State_Enabled
        if self._active:
            option.state |= QtWidgets.QStyle.StateFlag.State_Selected
        painter.drawControl(QtWidgets.QStyle.ControlElement.CE_MenuItem, option)

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025-2026 Philipp Wolfer
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)


class CheckboxMenuItem(QtWidgets.QWidget):
    """Custom checkable menu item.

    This widget provides a custom checkable menu item that can be used in a QMenu.
    It is similar to a standard QAction checkable item, but the menu does not close
    when the item is toggled. This is suitable for selectable items, where the user
    might want to toggle multiple items without closing the menu.
    """

    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, menu: QtWidgets.QMenu, action: QtGui.QAction, text: str, parent=None):
        super().__init__(parent=parent)
        self._menu = menu
        action.setCheckable(True)
        self._action = action
        self._text = text
        self._active = False
        self._pressed = False
        self.setEnabled(action.isEnabled())
        self._menu.hovered.connect(self._on_hover)
        self._action.toggled.connect(self.toggled.emit)
        self._action.enabledChanged.connect(self.setEnabled)

    def sizeHint(self):
        font_metrics = self.fontMetrics()
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        style = self.style()
        content_size = style.itemTextRect(
            font_metrics, QtCore.QRect(), QtCore.Qt.AlignmentFlag.AlignLeft, self.isEnabled(), self._text
        )
        return style.sizeFromContents(
            QtWidgets.QStyle.ContentsType.CT_MenuItem,
            option,
            QtCore.QSize(content_size.width(), content_size.height()),
            self,
        )

    def _on_hover(self, action: QtGui.QAction):
        active = action == self._action
        self.set_active(active)

    def set_active(self, active: bool):
        changed = self._active != active
        self._active = active
        if self._active:
            self.setFocus()
        if changed:
            self.repaint()

    def keyPressEvent(self, event: QtGui.QKeyEvent | None):
        if event is None:
            return
        if event.key() in {QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Space}:
            self._action.toggle()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent | None):
        if event is None:
            return
        self._pressed = True
        event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent | None):
        if event is None:
            return
        if self._pressed:
            self._action.toggle()
        self._pressed = False
        event.accept()

    def enterEvent(self, e):
        self.set_active(True)
        self._menu.setActiveAction(self._action)

    def leaveEvent(self, e):
        self.set_active(False)

    def paintEvent(self, e):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        option.text = self._text
        if self._action.isCheckable():
            option.checkType = QtWidgets.QStyleOptionMenuItem.CheckType.NonExclusive
        else:
            option.checkType = QtWidgets.QStyleOptionMenuItem.CheckType.NotCheckable
        option.checked = self._action.isChecked()
        option.state = QtWidgets.QStyle.StateFlag.State_None
        if self.isEnabled():
            option.state |= QtWidgets.QStyle.StateFlag.State_Enabled
        if self._active:
            option.state |= QtWidgets.QStyle.StateFlag.State_Selected
            option.state |= QtWidgets.QStyle.StateFlag.State_HasFocus
        if self._pressed:
            option.state |= QtWidgets.QStyle.StateFlag.State_Sunken
        else:
            option.state |= QtWidgets.QStyle.StateFlag.State_Raised
        painter.drawControl(QtWidgets.QStyle.ControlElement.CE_MenuItem, option)


def create_checkable_menu_item(
    menu_bar: QtWidgets.QMenuBar | None, menu: QtWidgets.QMenu, title: str, checked: bool
) -> QtGui.QAction:
    """Create a checkable menu item for a menu.

    On most platforms this creates a custom checkable menu item using CheckboxMenuItem.

    If the menu bar is a native menu bar (e.g. on macOS), a normal menu action is
    created, as a custom widget does not integrate well into the global menu and the
    color scheme of the global menu can differ from the application's color scheme.
    """
    if menu_bar and menu_bar.isNativeMenuBar():
        action = QtGui.QAction(title, menu)
        action.setCheckable(True)
    else:
        action = QtWidgets.QWidgetAction(menu)
        checkbox = CheckboxMenuItem(menu, action, title)
        action.setDefaultWidget(checkbox)

    action.setChecked(checked)
    return action

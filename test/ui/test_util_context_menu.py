# Picard, the next-generation MusicBrainz tagger
#
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

"""Regression tests for keyboard-triggered context-menu positioning.

The keyboard "context menu"/"menu" key (and Shift+F10) makes Qt synthesize a
``QContextMenuEvent`` whose position does *not* track the mouse cursor. Without
special handling the resulting menu opens in the wrong place (or, for handlers
that early-return on ``itemAt(pos)`` being ``None``, does not open at all).

These tests cover the shared helpers in ``picard.ui.util`` that compute a sane
anchor for keyboard-triggered menus.
"""

from unittest.mock import patch

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

import pytest

from picard.ui.util import (
    context_menu_global_pos,
    context_menu_item,
    is_keyboard_context_menu_event,
    keyboard_menu_anchor_global_pos,
)


def _context_menu_event(reason, pos=None):
    if pos is None:
        pos = QtCore.QPoint(0, 0)
    return QtGui.QContextMenuEvent(reason, pos, QtGui.QCursor.pos())


@pytest.fixture()
def list_widget(qapp):
    widget = QtWidgets.QListWidget()
    for i in range(5):
        widget.addItem(f"item {i}")
    widget.resize(200, 200)
    widget.show()
    yield widget
    widget.deleteLater()


@pytest.fixture()
def text_edit(qapp):
    widget = QtWidgets.QPlainTextEdit()
    widget.setPlainText("line1\nline2\nline3")
    widget.resize(200, 200)
    widget.show()
    yield widget
    widget.deleteLater()


@pytest.fixture()
def plain_widget(qapp):
    widget = QtWidgets.QWidget()
    widget.resize(200, 200)
    widget.show()
    yield widget
    widget.deleteLater()


class TestIsKeyboardContextMenuEvent:
    def test_keyboard_reason_is_detected(self):
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
        assert is_keyboard_context_menu_event(event) is True

    def test_mouse_reason_is_not_keyboard(self):
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Mouse, QtCore.QPoint(10, 10))
        assert is_keyboard_context_menu_event(event) is False

    def test_other_reason_is_not_keyboard(self):
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Other, QtCore.QPoint(10, 10))
        assert is_keyboard_context_menu_event(event) is False


class TestContextMenuGlobalPos:
    def test_mouse_event_uses_event_global_pos(self, list_widget):
        list_widget.setCurrentRow(2)
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Mouse, QtCore.QPoint(15, 15))
        pos = context_menu_global_pos(list_widget, event)
        assert pos == event.globalPos()

    def test_keyboard_event_anchors_at_current_item(self, list_widget):
        list_widget.setCurrentRow(3)
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
        pos = context_menu_global_pos(list_widget, event)
        # Anchor is the bottom-left of the current item's rect (in global coords),
        # which must differ from the meaningless event.globalPos() for keyboard.
        index = list_widget.currentIndex()
        expected = list_widget.viewport().mapToGlobal(list_widget.visualRect(index).bottomLeft())
        assert pos == expected


class TestKeyboardAnchorItemView:
    def test_anchors_at_current_item_bottom_left(self, list_widget):
        list_widget.setCurrentRow(1)
        index = list_widget.currentIndex()
        expected = list_widget.viewport().mapToGlobal(list_widget.visualRect(index).bottomLeft())
        assert keyboard_menu_anchor_global_pos(list_widget) == expected

    def test_no_current_item_anchors_at_viewport_origin(self, list_widget):
        list_widget.setCurrentIndex(QtCore.QModelIndex())
        list_widget.clearSelection()
        expected = list_widget.viewport().mapToGlobal(QtCore.QPoint(0, 0))
        assert keyboard_menu_anchor_global_pos(list_widget) == expected


class TestKeyboardAnchorTextEdit:
    def test_anchors_at_cursor_rect(self, text_edit):
        cursor = text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        text_edit.setTextCursor(cursor)
        expected = text_edit.viewport().mapToGlobal(text_edit.cursorRect().bottomLeft())
        assert keyboard_menu_anchor_global_pos(text_edit) == expected


class TestKeyboardAnchorHeaderView:
    def test_anchors_below_header(self, qapp):
        table = QtWidgets.QTableWidget(3, 3)
        table.resize(300, 200)
        table.show()
        try:
            header = table.horizontalHeader()
            expected = header.mapToGlobal(QtCore.QPoint(0, header.height()))
            assert keyboard_menu_anchor_global_pos(header) == expected
        finally:
            table.deleteLater()


class TestKeyboardAnchorPlainWidget:
    def test_anchors_at_widget_top_left(self, plain_widget):
        expected = plain_widget.mapToGlobal(QtCore.QPoint(0, 0))
        assert keyboard_menu_anchor_global_pos(plain_widget) == expected


class TestContextMenuItem:
    def test_mouse_uses_item_at_position(self, list_widget):
        list_widget.setCurrentRow(0)
        index = list_widget.model().index(3, 0)
        pos = list_widget.visualRect(index).center()
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Mouse, pos)
        assert context_menu_item(list_widget, event) is list_widget.item(3)

    def test_keyboard_uses_current_item(self, list_widget):
        list_widget.setCurrentRow(2)
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
        assert context_menu_item(list_widget, event) is list_widget.item(2)

    def test_mouse_on_empty_space_returns_none(self, list_widget):
        empty_pos = QtCore.QPoint(0, list_widget.viewport().height() * 4)
        event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Mouse, empty_pos)
        assert context_menu_item(list_widget, event) is None


class TestPluginTreeWidgetContextMenu:
    def _tree(self):
        from picard.ui.widgets.pluginlistwidget import PluginTreeWidget

        tree = PluginTreeWidget()
        tree.setColumnCount(1)
        for i in range(5):
            QtWidgets.QTreeWidgetItem(tree, [f"plugin {i}"])
        tree.resize(300, 200)
        tree.show()
        return tree

    def test_keyboard_emits_current_item_and_anchor(self, qapp):
        tree = self._tree()
        try:
            current = tree.topLevelItem(3)
            tree.setCurrentItem(current)
            captured = {}
            tree.context_menu_requested.connect(lambda item, pos: captured.update(item=item, pos=pos))
            event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
            QtWidgets.QApplication.sendEvent(tree, event)
            assert captured['item'] is current
            expected = keyboard_menu_anchor_global_pos(tree)
            assert captured['pos'] == expected
        finally:
            tree.deleteLater()


class TestLogListViewContextMenu:
    def test_keyboard_emits_anchor(self, qapp):
        from picard.ui.logview import LogListView

        view = LogListView()
        model = QtGui.QStandardItemModel()
        for i in range(6):
            model.appendRow(QtGui.QStandardItem(f"line {i}"))
        view.setModel(model)
        view.resize(300, 150)
        view.show()
        try:
            view.setCurrentIndex(model.index(4, 0))
            captured = {}
            view.context_menu_requested.connect(lambda pos: captured.update(pos=pos))
            event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
            QtWidgets.QApplication.sendEvent(view, event)
            assert captured['pos'] == keyboard_menu_anchor_global_pos(view)
        finally:
            view.deleteLater()


class TestSearchButtonContextMenu:
    def _button(self):
        from picard.ui.mainwindow import SearchButton

        button = SearchButton()
        button.resize(40, 30)
        button.show()
        return button

    def test_keyboard_drops_menu_below_button(self, qapp):
        button = self._button()
        try:
            captured = {}
            with patch.object(QtWidgets.QMenu, 'exec', lambda self, pos: captured.update(pos=pos)):
                event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Keyboard)
                QtWidgets.QApplication.sendEvent(button, event)
            expected = button.mapToGlobal(button.rect().bottomLeft())
            assert captured['pos'] == expected
        finally:
            button.deleteLater()

    def test_mouse_uses_event_global_pos(self, qapp):
        button = self._button()
        try:
            captured = {}
            event = _context_menu_event(QtGui.QContextMenuEvent.Reason.Mouse, QtCore.QPoint(5, 5))
            with patch.object(QtWidgets.QMenu, 'exec', lambda self, pos: captured.update(pos=pos)):
                QtWidgets.QApplication.sendEvent(button, event)
            assert captured['pos'] == event.globalPos()
        finally:
            button.deleteLater()

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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


"""Tests for the ``plugin_tools_rebuilt`` signal (PICARD-3465).

The Plugin Tools menu is rebuilt whenever a tools-menu action is registered or
a plugin is enabled/disabled. Each rebuild recreates its actions in the default
(enabled) state, so plugins need a notification to reapply per-action state.
``Signaler.plugin_tools_rebuilt`` provides that notification and must fire after
every rebuild -- both when the menu ends up populated and when it ends up empty
(and therefore hidden).
"""

from unittest.mock import Mock

from PyQt6 import QtGui, QtWidgets

from picard.extension_points.plugin_tools_menu import (
    ext_point_plugin_tools_items,
    signaler,
)
from picard.plugin3.api_impl import PluginApi

import pytest

from picard.ui.mainwindow import MainWindow


class _ToolsAction(QtGui.QAction):
    """Minimal stand-in for a registered Plugin Tools action."""

    MENU: tuple = ()

    def __init__(self, parent=None):
        super().__init__("Do Thing", parent=parent)

    @classmethod
    def display_menu(cls):
        return cls.MENU


@pytest.fixture
def registered_tools_action():
    """Register a tools-menu action for the test and clean it up afterwards.

    The action is registered under this test module (not a ``picard.plugins.*``
    module), so ``ext_point_plugin_tools_items`` stores it under the ``None``
    (internal) key and always yields it, regardless of enabled-plugin config.
    """
    ext_point_plugin_tools_items.register(__name__, _ToolsAction)
    try:
        yield _ToolsAction
    finally:
        ext_point_plugin_tools_items.unregister(__name__, lambda item: item is _ToolsAction)


@pytest.fixture
def mock_mainwindow(qapp):
    """A Mock(spec=MainWindow) with the real _make_plugin_tools_menu bound.

    Uses a real QMenu for ``plugin_tools_menu`` so menuAction()/clear() behave.
    """
    window = Mock(spec=MainWindow)
    window.plugin_tools_menu = QtWidgets.QMenu()
    window._make_plugin_tools_menu = MainWindow._make_plugin_tools_menu.__get__(window, MainWindow)
    return window


def _connect_recorder():
    """Return (callback, calls_list) recording each emission of the signal."""
    calls: list[int] = []

    def _on_rebuilt():
        calls.append(1)

    signaler.plugin_tools_rebuilt.connect(_on_rebuilt)
    return _on_rebuilt, calls


def test_signal_fires_when_menu_populated(mock_mainwindow, registered_tools_action):
    callback, calls = _connect_recorder()
    try:
        mock_mainwindow._make_plugin_tools_menu()
    finally:
        signaler.plugin_tools_rebuilt.disconnect(callback)

    # The signal fired exactly once ...
    assert calls == [1]
    # ... the menu is visible ...
    assert mock_mainwindow.plugin_tools_menu.menuAction().isVisible() is True
    # ... and the registered action was added.
    titles = [a.text() for a in mock_mainwindow.plugin_tools_menu.actions() if a.menu() is None]
    assert titles == ["Do Thing"]


def test_signal_fires_when_menu_empty(mock_mainwindow):
    # No actions registered -> menu ends up empty and hidden.
    callback, calls = _connect_recorder()
    try:
        mock_mainwindow._make_plugin_tools_menu()
    finally:
        signaler.plugin_tools_rebuilt.disconnect(callback)

    # The signal still fired exactly once ...
    assert calls == [1]
    # ... and the menu was hidden.
    assert mock_mainwindow.plugin_tools_menu.menuAction().isVisible() is False


def test_signal_not_emitted_without_menu(mock_mainwindow):
    # If there is no menu yet, the method returns early and must not emit.
    mock_mainwindow.plugin_tools_menu = None
    callback, calls = _connect_recorder()
    try:
        mock_mainwindow._make_plugin_tools_menu()
    finally:
        signaler.plugin_tools_rebuilt.disconnect(callback)

    assert calls == []


def test_menu_rebuild_does_not_duplicate_actions(mock_mainwindow, registered_tools_action):
    # Rebuilding twice must not accumulate duplicate actions (menu is cleared).
    callback, calls = _connect_recorder()
    try:
        mock_mainwindow._make_plugin_tools_menu()
        mock_mainwindow._make_plugin_tools_menu()
    finally:
        signaler.plugin_tools_rebuilt.disconnect(callback)

    assert calls == [1, 1]
    titles = [a.text() for a in mock_mainwindow.plugin_tools_menu.actions() if a.menu() is None]
    assert titles == ["Do Thing"]


def test_api_connect_plugin_tools_menu_rebuilt_receives_signal():
    # The PluginApi accessor wires a plugin callback to the signal without the
    # plugin importing UI or extension-point internals.
    calls: list[int] = []

    def plugin_callback():
        calls.append(1)

    # Bind the unbound method onto a bare object; it only touches the module
    # level signaler, so no full PluginApi construction is required.
    class _Api:
        connect_plugin_tools_menu_rebuilt = PluginApi.connect_plugin_tools_menu_rebuilt

    api = _Api()
    api.connect_plugin_tools_menu_rebuilt(plugin_callback)
    try:
        signaler.plugin_tools_rebuilt.emit()
    finally:
        signaler.plugin_tools_rebuilt.disconnect(plugin_callback)

    assert calls == [1]

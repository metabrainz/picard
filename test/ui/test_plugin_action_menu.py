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


"""Tests for adding plugin actions to (sub)menus based on their MENU path.

Regression tests for PICARD-3438: plugin actions with a MENU attribute must be
placed in the appropriate submenu for both the context menus and the main menu
bar "Plugin Tools" section. Both call sites share
``picard.extension_points.item_actions.add_action_to_menu``.
"""

from PyQt6 import QtGui, QtWidgets

from picard.extension_points.item_actions import add_action_to_menu


def _make_action_class(title, menu):
    """Build a minimal QAction subclass mimicking BaseAction's MENU contract."""

    class _Action(QtGui.QAction):
        MENU = menu

        def __init__(self):
            super().__init__(title)

    return _Action


def _submenu_titles(menu):
    """Return the titles of the submenus directly under ``menu``."""
    return [a.menu().title() for a in menu.actions() if a.menu() is not None]


def _action_titles(menu):
    """Return the titles of the leaf actions directly under ``menu``."""
    return [a.text() for a in menu.actions() if a.menu() is None]


def test_action_without_menu_added_to_root(qapp):
    root = QtWidgets.QMenu()
    submenus = {}

    add_action_to_menu(_make_action_class("Do Thing", ()), root, submenus)

    assert _action_titles(root) == ["Do Thing"]
    assert _submenu_titles(root) == []
    assert submenus == {}


def test_action_with_single_level_menu_creates_submenu(qapp):
    root = QtWidgets.QMenu()
    submenus = {}

    add_action_to_menu(_make_action_class("Do Thing", ("Tools",)), root, submenus)

    assert _submenu_titles(root) == ["Tools"]
    assert _action_titles(root) == []
    tools = submenus[("Tools",)]
    assert _action_titles(tools) == ["Do Thing"]


def test_action_with_nested_menu_creates_nested_submenus(qapp):
    root = QtWidgets.QMenu()
    submenus = {}

    add_action_to_menu(_make_action_class("Deep", ("A", "B", "C")), root, submenus)

    assert set(submenus.keys()) == {("A",), ("A", "B"), ("A", "B", "C")}
    assert _submenu_titles(root) == ["A"]
    assert _submenu_titles(submenus[("A",)]) == ["B"]
    assert _submenu_titles(submenus[("A", "B")]) == ["C"]
    assert _action_titles(submenus[("A", "B", "C")]) == ["Deep"]


def test_actions_sharing_menu_path_reuse_submenu(qapp):
    root = QtWidgets.QMenu()
    submenus = {}

    add_action_to_menu(_make_action_class("First", ("Shared",)), root, submenus)
    add_action_to_menu(_make_action_class("Second", ("Shared",)), root, submenus)

    # Only one "Shared" submenu is created and both actions go into it.
    assert _submenu_titles(root) == ["Shared"]
    shared = submenus[("Shared",)]
    assert _action_titles(shared) == ["First", "Second"]


def test_action_parent_is_target_submenu(qapp):
    root = QtWidgets.QMenu()
    submenus = {}

    add_action_to_menu(_make_action_class("Child", ("Parent",)), root, submenus)

    target = submenus[("Parent",)]
    action = _action_titles_and_objects(target)["Child"]
    assert action.parent() is target


def _action_titles_and_objects(menu):
    return {a.text(): a for a in menu.actions() if a.menu() is None}

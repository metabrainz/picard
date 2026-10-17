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


"""Regression tests for the Plugin Tools menu rebuild (PICARD-3479).

On macOS the Plugin Tools menu is part of the native (global) menu bar. The
submenu ``QMenu`` objects created for plugin menu paths are referenced by
AppKit ``NSMenuItem`` instances. The old rebuild called ``QMenu.clear()``,
destroying and recreating those submenu objects on every rebuild; a later
focus switch then sent ``setSubmenu:`` to a freed ``NSMenuItem`` and crashed
with EXC_BAD_ACCESS.

The crash itself is macOS-specific and cannot be reproduced in a headless
Linux CI. These tests lock in the invariant that the fix relies on: rebuilding
must *reuse* the submenu ``QMenu`` objects rather than destroying and
recreating them.
"""

from unittest.mock import Mock

from PyQt6 import (
    QtGui,
    QtWidgets,
)

from test.picardtestcase import PicardTestCase

from picard.extension_points.item_actions import (
    BaseAction,
    remove_leaf_actions,
)
from picard.extension_points.plugin_tools_menu import ext_point_plugin_tools_items

from picard.ui.mainwindow import MainWindow


_PLUGIN_MODULE = 'test.fake_tools_action'


class _FakeToolsAction(BaseAction):
    NAME = 'FakeToolsAction'
    TITLE = 'Fake Tools Action'
    MENU = ('Fake Submenu',)
    __module__ = _PLUGIN_MODULE

    def callback(self, objs):
        pass


class TestRemoveLeafActions(PicardTestCase):
    """Unit tests for remove_leaf_actions()."""

    def test_removes_leaf_actions_but_keeps_submenus(self):
        menu = QtWidgets.QMenu()
        leaf = QtGui.QAction('leaf', menu)
        menu.addAction(leaf)
        menu.addSeparator()
        submenu = menu.addMenu('submenu')
        submenu_action = submenu.menuAction()

        remove_leaf_actions(menu)

        remaining = menu.actions()
        # The submenu's own action must survive; leaf action and separator gone.
        self.assertIn(submenu_action, remaining)
        self.assertNotIn(leaf, remaining)
        # The submenu QMenu object itself must be preserved (not destroyed).
        self.assertIs(menu.actions()[-1].menu(), submenu)

    def test_idempotent_on_empty_menu(self):
        menu = QtWidgets.QMenu()
        remove_leaf_actions(menu)
        self.assertEqual(menu.actions(), [])


class TestPluginToolsMenuRebuild(PicardTestCase):
    """The rebuild must reuse submenu QMenu objects across invocations."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.extension_points.item_actions')
        # Register the fake plugin tools action for the duration of the test.
        ext_point_plugin_tools_items.register(_PLUGIN_MODULE, _FakeToolsAction)
        self.addCleanup(ext_point_plugin_tools_items.unregister_module, None)

    def _make_window_stub(self):
        """A MainWindow stub exposing only what _make_plugin_tools_menu needs."""
        window = Mock(spec=MainWindow)
        window.plugin_tools_menu = QtWidgets.QMenu('&Plugin Tools')
        window._plugin_tools_submenus = {}
        window._make_plugin_tools_menu = MainWindow._make_plugin_tools_menu.__get__(window, MainWindow)
        return window

    def test_rebuild_reuses_submenu_objects(self):
        window = self._make_window_stub()

        window._make_plugin_tools_menu()
        submenus_after_first = dict(window._plugin_tools_submenus)
        self.assertIn(('Fake Submenu',), submenus_after_first)
        submenu_obj = submenus_after_first[('Fake Submenu',)]

        # Rebuild again (as happens on plugin_state_changed / focus-related churn).
        window._make_plugin_tools_menu()

        # The submenu QMenu object must be the SAME instance, not recreated.
        self.assertIs(window._plugin_tools_submenus[('Fake Submenu',)], submenu_obj)

    def test_rebuild_does_not_duplicate_leaf_actions(self):
        window = self._make_window_stub()

        window._make_plugin_tools_menu()
        submenu = window._plugin_tools_submenus[('Fake Submenu',)]
        count_after_first = len(submenu.actions())

        window._make_plugin_tools_menu()
        count_after_second = len(submenu.actions())

        self.assertEqual(count_after_first, count_after_second)
        self.assertGreaterEqual(count_after_first, 1)

    def test_menu_visible_when_actions_present(self):
        window = self._make_window_stub()
        window._make_plugin_tools_menu()
        self.assertTrue(window.plugin_tools_menu.menuAction().isVisible())

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2026 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2026 Laurent Monin
# Copyright (C) 2013-2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2021 Petit Minion
# Copyright (C) 2023 certuna
# Copyright (C) 2024 Suryansh Shakya
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
    QtGui,
    QtWidgets,
)

from picard import tagger_instance
from picard.plugin import ExtensionPoint
from picard.util.display_title_base import (
    HasDisplayTitle,
    HasMenuItems,
)


class BaseAction(QtGui.QAction, HasDisplayTitle, HasMenuItems):
    """Base class for plugin actions.

    Subclasses should set the `TITLE` and optionally the `MENU` attributes to define the
    action's display title and menu path and implement the `callback` method to define
    the action's behavior.
    """

    # Name of the action to display in the menu.
    TITLE: str | tuple[str, str, str] = "Unknown"

    # Menu path for the action. Each item in the tuple is a submenu name.
    # The action will be added as a child to the last submenu in the tuple.
    MENU: tuple[str, ...] = tuple()

    def __init__(self, parent=None):
        super().__init__(self.display_title(), parent=parent)
        self.tagger = tagger_instance()
        self.triggered.connect(self.__callback)
        self.translate_menu()

    def __callback(self):
        objs = self.tagger.window.selected_objects
        try:
            self.callback(objs)
        except Exception:
            # Avoid circular import: extension_points loaded early before picard.log is fully initialized
            from picard import log

            if hasattr(self, 'api'):
                plugin_id = getattr(self.api, 'plugin_id', 'unknown')
            else:
                plugin_id = None
            log.error("Error in action %s (plugin: %s):", self.display_title(), plugin_id, exc_info=True)

    def callback(self, objs):
        raise NotImplementedError


def add_action_to_menu(
    action_class: type[BaseAction],
    root_menu: QtWidgets.QMenu,
    submenus: dict[tuple[str, ...], QtWidgets.QMenu],
) -> None:
    """Instantiate a plugin action and add it to the appropriate (sub)menu.

    The action's ``MENU`` attribute defines an optional menu path. Each item in
    the path is a submenu name; the action is added as a child of the last
    submenu. Submenus are created on demand and shared via the ``submenus``
    cache so that actions sharing a menu path end up in the same submenu.

    Parameters
    ----------
    action_class : type[BaseAction]
        The plugin action class to instantiate.
    root_menu : QtWidgets.QMenu
        The menu that serves as the root of the action's menu path.
    submenus : dict[tuple[str, ...], QtWidgets.QMenu]
        Cache mapping a menu path prefix to its created submenu. Callers should
        reuse the same dict across all actions added to ``root_menu``.
    """
    action_menu = root_menu
    menu_path: tuple[str, ...] = ()
    for menu_name in action_class.MENU:
        menu_path += (menu_name,)
        submenu = submenus.get(menu_path)
        if submenu is None:
            submenu = action_menu.addMenu(menu_name)
            assert submenu is not None  # addMenu(str) always returns a QMenu
            submenus[menu_path] = submenu
        action_menu = submenu
    action = action_class()
    action.setParent(action_menu)  # Set parent to keep action alive
    action_menu.addAction(action)


ext_point_album_actions = ExtensionPoint[type[BaseAction]](label='album_actions')
ext_point_cluster_actions = ExtensionPoint[type[BaseAction]](label='cluster_actions')
ext_point_clusterlist_actions = ExtensionPoint[type[BaseAction]](label='clusterlist_actions')
ext_point_file_actions = ExtensionPoint[type[BaseAction]](label='file_actions')
ext_point_track_actions = ExtensionPoint[type[BaseAction]](label='track_actions')


def register_album_action(action: type[BaseAction]) -> None:
    ext_point_album_actions.register(action.__module__, action)


def register_cluster_action(action: type[BaseAction]) -> None:
    ext_point_cluster_actions.register(action.__module__, action)


def register_clusterlist_action(action: type[BaseAction]) -> None:
    ext_point_clusterlist_actions.register(action.__module__, action)


def register_file_action(action: type[BaseAction]) -> None:
    ext_point_file_actions.register(action.__module__, action)


def register_track_action(action: type[BaseAction]) -> None:
    ext_point_track_actions.register(action.__module__, action)

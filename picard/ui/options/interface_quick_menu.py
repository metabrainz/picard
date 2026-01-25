# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
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
    QtCore,
    QtWidgets,
)

from picard import log
from picard.config import (
    get_config,
    get_quick_menu_items,
)
from picard.const.defaults import DEFAULT_QUICK_MENU_ITEMS
from picard.extension_points.options_pages import register_options_page
from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.forms.ui_options_interface_quick_menu import (
    Ui_InterfaceQuickMenuOptionsPage,
)
from picard.ui.options import OptionsPage


class InterfaceQuickMenuOptionsPage(OptionsPage):
    NAME = 'interface_quick_menu'
    TITLE = N_("Quick Settings Menu")
    PARENT = 'interface'
    SORT_ORDER = 40
    ACTIVE = True
    HELP_URL = "/config/options_interface_quick_menu.html"

    OPTIONS = (('quick_menu_items', ['quick_menu_items']),)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_InterfaceQuickMenuOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        config = get_config()
        self.menu_items = config.setting['quick_menu_items']
        self._make_tree()

    def _make_child_item(self, name, title, checked):
        item = QtWidgets.QTreeWidgetItem([_(title)])
        item.setData(0, QtCore.Qt.ItemDataRole.UserRole, name)
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
        state = QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        item.setCheckState(0, state)
        return item

    def _make_tree(self):
        self.ui.quick_menu_items.clear()
        for group in get_quick_menu_items():
            expand = False

            title = _(group['title'])
            parent = group.get('parent', '')
            name = group['name']

            widget_item = QtWidgets.QTreeWidgetItem([title])
            widget_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, name)
            widget_item.setFlags(
                QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsAutoTristate
            )
            widget_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            for setting in group['options']:
                checked = self.menu_items and setting.name in self.menu_items
                expand |= checked
                widget_item.addChild(self._make_child_item(setting.name, setting.title, checked))
            added = False
            if parent:
                # Find parent item
                for i in range(self.ui.quick_menu_items.topLevelItemCount()):
                    tl_item = self.ui.quick_menu_items.topLevelItem(i)
                    if tl_item.data(0, QtCore.Qt.ItemDataRole.UserRole) == parent:
                        tl_item.addChild(widget_item)
                        added = True
                        break
                if not added:
                    log.warning("Parent '%s' not found for quick settings group '%s'", parent, name)
            if not added:
                self.ui.quick_menu_items.addTopLevelItem(widget_item)
            widget_item.setExpanded(expand)

    def save(self):
        config = get_config()
        config.setting['quick_menu_items'] = list(self._get_selected_options())

    def _get_settings_from_children(self, parent_item, settings=None):
        """Recursively get settings from child items.

        Args:
            parent_item (QtWidgets.QTreeWidgetItem): Parent item
            settings (set): Set to add settings keys to
        """
        if settings is None:
            settings = set()
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            if item.childCount():
                self._get_settings_from_children(item, settings)
            elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
                settings.add(item.data(0, QtCore.Qt.ItemDataRole.UserRole))

    def _get_selected_options(self):
        checked_items = set()
        for i in range(self.ui.quick_menu_items.topLevelItemCount()):
            tl_item = self.ui.quick_menu_items.topLevelItem(i)
            for j in range(tl_item.childCount()):
                item = tl_item.child(j)
                if item.childCount():
                    self._get_settings_from_children(item, checked_items)
                elif item.checkState(0) == QtCore.Qt.CheckState.Checked:
                    checked_items.add(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
        return checked_items

    def restore_defaults(self):
        self.menu_items = DEFAULT_QUICK_MENU_ITEMS
        self._make_tree()


register_options_page(InterfaceQuickMenuOptionsPage)

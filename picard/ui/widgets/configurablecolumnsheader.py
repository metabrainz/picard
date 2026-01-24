# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012 Lukáš Lalinský
# Copyright (C) 2007 Robert Kaye
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Hendrik van Antwerpen
# Copyright (C) 2008-2011, 2014-2015, 2018-2024 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 Nikolai Prokoschenko
# Copyright (C) 2011 Tim Blechmann
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Your Name
# Copyright (C) 2012-2013 Wieland Hoffmann
# Copyright (C) 2013-2014, 2016, 2018-2024 Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from functools import partial

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.i18n import gettext as _

from picard.ui.columns import (
    ColumnGroups,
    ImageColumn,
)
from picard.ui.itemviews.custom_columns.manager_dialog import CustomColumnsManagerDialog
from picard.ui.widgets.checkboxmenuitem import CheckboxMenuItem
from picard.ui.widgets.lockableheaderview import LockableHeaderView


class ConfigurableColumnsHeader(LockableHeaderView):
    def __init__(self, columns, parent=None):
        super().__init__(QtCore.Qt.Orientation.Horizontal, parent)
        self._columns = columns
        self._always_visible_columns = set(self._columns.always_visible_columns())
        self._visible_columns = set(self._always_visible_columns)
        self.unsorted()

        self.sortIndicatorChanged.connect(self.on_sort_indicator_changed)

    def unsorted(self):
        # enable sorting, but don't actually use it by default
        # XXX it would be nice to be able to go to the 'no sort' mode, but the
        #     internal model that QTreeWidget uses doesn't support it
        self.setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def show_column(self, column, show):
        if column in self._always_visible_columns:
            # Always visible
            # Still execute following to ensure it is shown
            show = True
        self.parent().setColumnHidden(column, not show)
        if show:
            self._visible_columns.add(column)
        else:
            self._visible_columns.discard(column)

    def _create_checkbox_action(self, menu, text, checked, enabled, callback):
        """Create a QWidgetAction with a QCheckBox that doesn't close the menu on toggle.

        Parameters
        ----------
        menu : QtWidgets.QMenu
            The parent menu for the action.
        text : str
            The label text for the checkbox.
        checked : bool
            Whether the checkbox should be checked.
        enabled : bool
            Whether the checkbox should be enabled.
        callback : callable
            The callback to connect to the checkbox's toggled signal.

        Returns
        -------
        tuple[QtWidgets.QWidgetAction, QtWidgets.QCheckBox]
            A tuple containing the configured action and its checkbox widget.
        """
        action = QtWidgets.QWidgetAction(menu)
        action.setChecked(checked)
        checkbox = CheckboxMenuItem(menu, action, text)
        checkbox.setEnabled(enabled)
        checkbox.toggled.connect(callback)
        action.setDefaultWidget(checkbox)
        return action, checkbox

    def _add_column_actions(self, menu):
        """Add column visibility toggle actions to the menu.

        Parameters
        ----------
        menu : QtWidgets.QMenu
            The menu to add actions to.

        Returns
        -------
        list[QtWidgets.QCheckBox]
            List of column checkboxes for dynamic state updates.
        """
        group_map = {}
        for group in ColumnGroups.all_groups():
            group_map[group.title] = QtWidgets.QMenu(_(group.title), menu)
            menu.addMenu(group_map[group.title])

        column_checkboxes = []
        for i, column in enumerate(self._columns):
            if i in self._always_visible_columns:
                continue

            group = getattr(column, 'column_group', None)
            target_menu = group_map[group.title] if group and group.title in group_map else menu
            action, checkbox = self._create_checkbox_action(
                target_menu,
                _(column.title),
                i in self._visible_columns,
                not self.is_locked,
                partial(self.show_column, i),
            )
            column_checkboxes.append(checkbox)
            target_menu.addAction(action)

        for group_menu in group_map.values():
            if group_menu.isEmpty():
                group_menu.setEnabled(False)

        return column_checkboxes

    def _add_restore_action(self, menu):
        """Add restore defaults action to the menu.

        Parameters
        ----------
        menu : QtWidgets.QMenu
            The menu to add the action to.

        Returns
        -------
        QtGui.QAction
            The restore action for dynamic state updates.
        """
        restore_action = QtGui.QAction(_("Restore default columns"), self.parent())
        restore_action.setEnabled(not self.is_locked)
        restore_action.triggered.connect(self.restore_defaults)
        menu.addAction(restore_action)
        return restore_action

    def _add_lock_action(self, menu):
        """Add lock columns action to the menu.

        Parameters
        ----------
        menu : QtWidgets.QMenu
            The menu to add the action to.

        Returns
        -------
        QtWidgets.QCheckBox
            The lock checkbox for connecting dynamic callbacks.
        """
        lock_action, lock_checkbox = self._create_checkbox_action(
            menu,
            _("Lock columns"),
            self.is_locked,
            True,
            lambda: None,  # Callback set later
        )
        menu.addAction(lock_action)
        return lock_checkbox

    def _add_manage_action(self, menu):
        """Add manage custom columns action to the menu.

        Parameters
        ----------
        menu : QtWidgets.QMenu
            The menu to add the action to.

        Returns
        -------
        QtGui.QAction
            The manage action for dynamic state updates.
        """

        def _open_manager():
            dlg = CustomColumnsManagerDialog(parent=self)
            dlg.exec()

        manage_action = QtGui.QAction(_("Manage custom columns…"), menu)
        manage_action.setEnabled(not self.is_locked)
        manage_action.triggered.connect(_open_manager)
        menu.addAction(manage_action)
        return manage_action

    def _create_lock_toggle_callback(self, column_checkboxes, restore_action, manage_action):
        """Create callback for lock toggle that updates dependent UI elements.

        Parameters
        ----------
        column_checkboxes : list[QtWidgets.QCheckBox]
            Column checkboxes to enable/disable.
        restore_action : QtGui.QAction
            Restore action to enable/disable.
        manage_action : QtGui.QAction
            Manage action to enable/disable.

        Returns
        -------
        callable
            Callback function that updates all dependent elements.
        """

        def _on_lock_toggled(is_locked):
            self.lock(is_locked)
            for checkbox in column_checkboxes:
                checkbox.setEnabled(not is_locked)
            restore_action.setEnabled(not is_locked)
            manage_action.setEnabled(not is_locked)

        return _on_lock_toggled

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        column_checkboxes = self._add_column_actions(menu)
        menu.addSeparator()
        restore_action = self._add_restore_action(menu)
        manage_action = self._add_manage_action(menu)
        menu.addSeparator()
        lock_checkbox = self._add_lock_action(menu)

        # Wire lock toggle to update dependent UI elements
        lock_toggle_callback = self._create_lock_toggle_callback(column_checkboxes, restore_action, manage_action)
        lock_checkbox.toggled.disconnect()
        lock_checkbox.toggled.connect(lock_toggle_callback)

        menu.exec(event.globalPos())
        event.accept()

    def restore_defaults(self):
        self.parent().restore_default_columns()

    def sync_visible_columns(self):
        """Synchronize _visible_columns with actual column visibility state.

        This should be called when new columns are added to ensure the context menu
        checkboxes reflect the actual visibility state.
        """
        # Update always visible columns in case they changed
        self._always_visible_columns = set(self._columns.always_visible_columns())

        # For each column, check if it's actually visible in the table
        for i in range(len(self._columns)):
            if i in self._always_visible_columns:
                # Always visible columns should always be in _visible_columns
                self._visible_columns.add(i)
            else:
                # For other columns, check if they're actually hidden
                is_hidden = self.parent().isColumnHidden(i)
                if not is_hidden:
                    self._visible_columns.add(i)
                else:
                    self._visible_columns.discard(i)

    def paintSection(self, painter, rect, index):
        # The Manage Custom Columns dialog may mutate the `self._columns` list.
        # Guard against transient mismatches between header section count and
        # the underlying columns list during live add/remove operations.
        # see: picard/ui/itemviews/custom_columns/manager_dialog.py
        try:
            column = self._columns[index]
        except IndexError:
            column = None

        # Always paint the default header section once
        super().paintSection(painter, rect, index)

        # Overlay custom painting for image columns
        if isinstance(column, ImageColumn):
            column.paint(painter, rect)

    def on_sort_indicator_changed(self, index, order):
        try:
            unsorted = not self._columns[index].sortable
        except IndexError as e:
            log.warning("Defaulting to unsorted due to invalid index %r: %s", index, e)
            unsorted = True
        if unsorted:
            self.unsorted()

    def lock(self, is_locked):
        super().lock(is_locked)

    def __str__(self):
        name = getattr(self.parent(), 'NAME', str(self.parent().__class__.__name__))
        return f"{name}'s header"

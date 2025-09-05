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

from picard.i18n import gettext as _

from picard.ui.columns import ImageColumn
from picard.ui.itemviews.custom_columns.manager_dialog import CustomColumnsManagerDialog
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

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        parent = self.parent()

        for i, column in enumerate(self._columns):
            if i in self._always_visible_columns:
                continue
            action = QtGui.QAction(_(column.title), parent)
            action.setCheckable(True)
            action.setChecked(i in self._visible_columns)
            action.setEnabled(not self.is_locked)
            action.triggered.connect(partial(self.show_column, i))
            menu.addAction(action)

        menu.addSeparator()
        restore_action = QtGui.QAction(_("Restore default columns"), parent)
        restore_action.setEnabled(not self.is_locked)
        restore_action.triggered.connect(self.restore_defaults)
        menu.addAction(restore_action)

        lock_action = QtGui.QAction(_("Lock columns"), parent)
        lock_action.setCheckable(True)
        lock_action.setChecked(self.is_locked)
        lock_action.toggled.connect(self.lock)
        menu.addAction(lock_action)

        menu.addSeparator()

        def _open_manager():
            dlg = CustomColumnsManagerDialog(parent=self)
            dlg.exec()

        manage_action = QtGui.QAction(_("Manage Custom Columns…"), menu)
        manage_action.setEnabled(not self.is_locked and CustomColumnsManagerDialog is not None)
        manage_action.triggered.connect(_open_manager)
        menu.addAction(manage_action)

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
        if index < 0 or not self._columns[index].sortable:
            self.unsorted()

    def lock(self, is_locked):
        super().lock(is_locked)

    def __str__(self):
        name = getattr(self.parent(), 'NAME', str(self.parent().__class__.__name__))
        return f"{name}'s header"

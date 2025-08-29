# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Registry for adding, removing and fetching custom columns."""

from __future__ import annotations

from picard.ui.itemviews.custom_columns.column import CustomColumn
from picard.ui.itemviews.custom_columns.shared import (
    RECOGNIZED_VIEWS,
    get_recognized_view_columns,
)


class CustomColumnsRegistry:
    """Registry for custom columns and utilities to add them to views."""

    def __init__(self):
        self._by_key = {}

    def register(
        self,
        column: CustomColumn,
        *,
        add_to: set[str] | frozenset[str] | list[str] | tuple[str, ...] | None = None,
    ) -> None:
        """Register column and insert into views.

        Parameters
        ----------
        column
                The column instance to register.
        add_to
                Collection of views to add to, e.g. {"FILE_VIEW", "ALBUM_VIEW"}.
        """
        self._by_key[column.key] = column

        # Local import: These column collections are mutable module-level objects that
        # may be modified by plugins or other parts of the application at runtime.
        # Importing at registration time ensures we always get the current state
        # of these collections, not a stale reference from module load time.
        targets = set(str(v).upper() for v in (add_to or RECOGNIZED_VIEWS))
        view_columns = get_recognized_view_columns()
        for target in targets:
            cols = view_columns.get(target)

            # If the target is an unknown view, raise an error
            if cols is None:
                raise ValueError(f"Unknown view identifier: {target}")

            self._insert_column(cols, column)

    def _insert_column(self, target_columns, column: CustomColumn) -> None:
        """Insert column into target columns list and apply width to existing headers.

        Parameters
        ----------
        target_columns
                The columns collection to insert into.
        column
                The column to insert.
        """
        # Remove any existing entries with the same key (idempotent registration)
        self._remove_all_by_key(target_columns, column.key)

        # Always append at the end
        position = len(target_columns)

        # Insert the column
        target_columns.insert(position, column)

        # Apply width settings to existing UI headers
        self._apply_column_width_to_headers(target_columns, column, position)

    def _remove_all_by_key(self, target_columns, key: str) -> None:
        """Remove all occurrences of a column key from target columns.

        Parameters
        ----------
        target_columns
                The columns collection to remove from.
        key
                The column key to remove.
        """
        while True:
            try:
                pos = target_columns.pos(key)
                del target_columns[pos]
            except KeyError:
                break

    def _apply_column_width_to_headers(self, target_columns, column: CustomColumn, position: int) -> None:
        """Apply column width settings to existing UI headers.

        Parameters
        ----------
        target_columns
                The columns collection.
        column
                The column with width settings.
        position
                The position of the column in the collection.
        """
        try:
            # Try to import Qt and get application instance
            from PyQt6 import QtWidgets

            app = QtWidgets.QApplication.instance()
            if not app or not isinstance(app, QtWidgets.QApplication):
                return

            # Apply width to all matching widgets
            for widget in app.allWidgets():
                self._apply_width_to_widget(widget, target_columns, column, position)

        except ImportError:
            # Qt not available - running in non-GUI environment
            pass
        except Exception:
            # Other errors shouldn't break registration
            pass

    def _apply_width_to_widget(self, widget, target_columns, column: CustomColumn, position: int) -> None:
        """Apply column width to a specific widget if it matches.

        Parameters
        ----------
        widget
                The widget to potentially update.
        target_columns
                The columns collection to match against.
        column
                The column with width settings.
        position
                The position of the column.
        """
        try:
            # Check if this widget uses our target columns
            if getattr(widget, 'columns', None) is not target_columns:
                return

            # Get the header (might be a property or method)
            header = getattr(widget, 'header', None)
            if callable(header):
                header = header()
            if header is None:
                return

            # Apply width if specified
            width = column.width if column.width is not None else getattr(target_columns, 'default_width', None)
            if width is not None:
                header.resizeSection(position, int(width))

            # Set resize mode
            from PyQt6.QtWidgets import QHeaderView

            is_resizable = getattr(column, 'resizeable', True)
            mode = QHeaderView.ResizeMode.Interactive if is_resizable else QHeaderView.ResizeMode.Fixed
            header.setSectionResizeMode(position, mode)

        except Exception:
            # Best effort - don't break on individual widget failures
            pass

    def unregister(self, key: str) -> CustomColumn | None:
        """Unregister column and remove from views.

        Parameters
        ----------
        key
                Column key.

        Returns
        -------
        CustomColumn | None
                The removed column or None.
        """
        column = self._by_key.pop(key, None)
        if not column:
            return None

        # Use centralized helper to fetch current view columns
        for cols in get_recognized_view_columns().values():
            self._remove_all_by_key(cols, key)

        return column

    def get(self, key: str) -> CustomColumn | None:
        """Return column by key.

        Parameters
        ----------
        key
                Column key.

        Returns
        -------
        CustomColumn | None
                The column or None.
        """
        return self._by_key.get(key)


registry = CustomColumnsRegistry()

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


class CustomColumnsRegistry:
    """Registry for custom columns and utilities to add them to views."""

    def __init__(self):
        self._by_key = {}

    def register(
        self,
        column: CustomColumn,
        *,
        add_to_file_view: bool = True,
        add_to_album_view: bool = True,
        insert_after_key: str | None = None,
    ) -> None:
        """Register column and insert into views.

        Parameters
        ----------
        column
                The column instance to register.
        add_to_file_view
                If True, add to file view.
        add_to_album_view
                If True, add to album view.
        insert_after_key
                Insert after this key if present, else append.
        """
        self._by_key[column.key] = column
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS, FILEVIEW_COLUMNS

        def _insert(target_columns, col: CustomColumn):
            if insert_after_key:
                try:
                    pos = target_columns.pos(insert_after_key) + 1
                except KeyError:
                    pos = len(target_columns)
            else:
                pos = len(target_columns)
            target_columns.insert(pos, col)

        if add_to_file_view:
            _insert(FILEVIEW_COLUMNS, column)
        if add_to_album_view:
            _insert(ALBUMVIEW_COLUMNS, column)

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
        from picard.ui.itemviews.columns import ALBUMVIEW_COLUMNS, FILEVIEW_COLUMNS

        for cols in (FILEVIEW_COLUMNS, ALBUMVIEW_COLUMNS):
            try:
                pos = cols.pos(key)
                del cols[pos]
            except KeyError:
                pass
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

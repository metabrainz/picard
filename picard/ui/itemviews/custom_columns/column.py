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

"""Custom column type that delegates value and optional sort to a provider."""

from __future__ import annotations

from picard.ui.columns import Column, ColumnAlign, ColumnSortType
from picard.ui.itemviews.custom_columns.protocols import ColumnValueProvider, SortKeyProvider


class CustomColumn(Column):
    """A column whose value is computed by a provider for each row object."""

    def __init__(
        self,
        title: str,
        key: str,
        provider: ColumnValueProvider,
        width: int | None = None,
        align: ColumnAlign = ColumnAlign.LEFT,
        sort_type: ColumnSortType = ColumnSortType.TEXT,
        always_visible: bool = False,
    ):
        """Create custom column.

        Parameters
        ----------
        title
            Display title of the column.
        key
            Internal key used to identify the column.
        provider
            Provide computation of values.
        width
            Optional fixed width in pixels.
        align
            Set text alignment.
        sort_type
            Set sorting behavior of the column.
        always_visible
            If True, hide the column visibility toggle.
        """
        sortkey_fn = (
            provider.sort_key  # type: ignore[attr-defined]
            if (sort_type == ColumnSortType.SORTKEY and isinstance(provider, SortKeyProvider))
            else None
        )
        super().__init__(
            title,
            key,
            width=width,
            align=align,
            sort_type=sort_type,
            sortkey=sortkey_fn,
            always_visible=always_visible,
            status_icon=False,
        )
        self.provider = provider

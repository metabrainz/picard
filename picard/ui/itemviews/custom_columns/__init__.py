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

"""Public API for custom columns: types, factories and registry."""

from __future__ import annotations

from picard.ui.itemviews.custom_columns.column import CustomColumn
from picard.ui.itemviews.custom_columns.factory import (
    _create_custom_column,
    make_callable_column,
    make_field_column,
    make_provider_column,
    make_script_column,
    make_transformed_column,
)
from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    SortKeyProvider,
)
from picard.ui.itemviews.custom_columns.registry import registry
from picard.ui.itemviews.custom_columns.sorting_adapters import (
    ArticleInsensitiveAdapter,
    CachedSortAdapter,
    CasefoldSortAdapter,
    CompositeSortAdapter,
    DescendingCasefoldSortAdapter,
    DescendingNaturalSortAdapter,
    DescendingNumericSortAdapter,
    LengthSortAdapter,
    NaturalSortAdapter,
    NullsFirstAdapter,
    NullsLastAdapter,
    NumericSortAdapter,
    ReverseAdapter,
)


__all__ = [
    "ColumnValueProvider",
    "SortKeyProvider",
    "CustomColumn",
    "make_field_column",
    "make_provider_column",
    "make_script_column",
    "make_callable_column",
    "make_transformed_column",
    "registry",
    "_create_custom_column",
    # Sorting adapters
    "CasefoldSortAdapter",
    "DescendingCasefoldSortAdapter",
    "NumericSortAdapter",
    "DescendingNumericSortAdapter",
    "NaturalSortAdapter",
    "DescendingNaturalSortAdapter",
    "LengthSortAdapter",
    "ArticleInsensitiveAdapter",
    "CompositeSortAdapter",
    "NullsLastAdapter",
    "NullsFirstAdapter",
    "CachedSortAdapter",
    "ReverseAdapter",
]

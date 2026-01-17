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

from picard.ui.itemviews.custom_columns.column import (
    CustomColumn,
    DelegateColumn,
    IconColumn,
)
from picard.ui.itemviews.custom_columns.factory import (
    _create_custom_column,
    make_callable_column,
    make_delegate_column,
    make_field_column,
    make_numeric_field_column,
    make_provider_column,
    make_script_column,
    make_transformed_column,
)
from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    DelegateProvider,
    HeaderIconProvider,
    SortKeyProvider,
)
from picard.ui.itemviews.custom_columns.registry import registry
from picard.ui.itemviews.custom_columns.sorting_adapters import (
    ArticleInsensitiveAdapter,
    CachedSortAdapter,
    CasefoldSortAdapter,
    CompositeSortAdapter,
    LengthSortAdapter,
    LocaleAwareSortAdapter,
    NaturalSortAdapter,
    NullsFirstAdapter,
    NullsLastAdapter,
    NumericSortAdapter,
)


__all__ = [
    "ColumnValueProvider",
    "DelegateProvider",
    "SortKeyProvider",
    "HeaderIconProvider",
    "CustomColumn",
    "DelegateColumn",
    "IconColumn",
    "make_field_column",
    "make_numeric_field_column",
    "make_provider_column",
    "make_script_column",
    "make_callable_column",
    "make_transformed_column",
    "make_delegate_column",
    "registry",
    "_create_custom_column",
    # Sorting adapters
    "CasefoldSortAdapter",
    "NumericSortAdapter",
    "NaturalSortAdapter",
    "LengthSortAdapter",
    "LocaleAwareSortAdapter",
    "ArticleInsensitiveAdapter",
    "CompositeSortAdapter",
    "NullsLastAdapter",
    "NullsFirstAdapter",
    "CachedSortAdapter",
]

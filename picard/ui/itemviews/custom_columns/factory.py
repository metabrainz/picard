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

"""Factory helpers to create common custom column types."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6 import QtCore

from picard.item import Item
from picard.script import ScriptParser

from picard.ui.columns import (
    ColumnAlign,
    ColumnSortType,
)
from picard.ui.itemviews.custom_columns.column import CustomColumn, DelegateColumn, IconColumn
from picard.ui.itemviews.custom_columns.protocols import (
    ColumnValueProvider,
    DelegateProvider,
    HeaderIconProvider,
    SortKeyProvider,
)
from picard.ui.itemviews.custom_columns.providers import (
    CallableProvider,
    FieldReferenceProvider,
    TransformProvider,
)
from picard.ui.itemviews.custom_columns.script_provider import ChainedValueProvider
from picard.ui.itemviews.custom_columns.sorting_adapters import NumericSortAdapter


def _infer_sort_type(provider: ColumnValueProvider, sort_type: ColumnSortType | None) -> ColumnSortType:
    """Infer column sort type from provider capability.

    Parameters
    ----------
    provider
        The value provider.
    sort_type
        Explicit sort type or None to infer.

    Returns
    -------
    ColumnSortType
        The resolved sort type.
    """
    if sort_type is not None:
        return sort_type
    if isinstance(provider, SortKeyProvider):
        return ColumnSortType.SORTKEY
    return ColumnSortType.TEXT


def _create_custom_column(
    title: str,
    key: str,
    provider: ColumnValueProvider,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    sort_type: ColumnSortType | None = None,
    status_icon: bool = False,
) -> CustomColumn:
    """Create `CustomColumn`.

    Parameters
    ----------
    title, key, provider, width, align, always_visible, sort_type
        See `CustomColumn` for details.

    Returns
    -------
    CustomColumn
        The configured column.
    """
    inferred_sort_type = _infer_sort_type(provider, sort_type)
    # If explicitly requested SORTKEY but provider cannot supply a sort_key,
    # downgrade to TEXT to avoid invalid configuration
    if inferred_sort_type == ColumnSortType.SORTKEY and not isinstance(provider, SortKeyProvider):
        inferred_sort_type = ColumnSortType.TEXT
    return CustomColumn(
        title,
        key,
        provider,
        width=width,
        align=align,
        sort_type=inferred_sort_type,
        always_visible=always_visible,
        status_icon=status_icon,
    )


def make_field_column(
    title: str,
    key: str,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    sort_type: ColumnSortType = ColumnSortType.TEXT,
    status_icon: bool = False,
) -> CustomColumn:
    """Create column that displays a field via `obj.column(key)`.

    Parameters
    ----------
    title, key, width, align, always_visible
        Column configuration.

    Returns
    -------
    CustomColumn
        The field column.
    """
    provider = FieldReferenceProvider(key)
    return _create_custom_column(
        title,
        key,
        provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=sort_type,
        status_icon=status_icon,
    )


def make_numeric_field_column(
    title: str,
    key: str,
    parser: Callable[[str], float] | None = None,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    status_icon: bool = False,
) -> CustomColumn:
    """Create column that displays a field with numeric sorting.

    Parameters
    ----------
    title, key, width, align, always_visible, status_icon
        Column configuration.
    parser : Callable[[str], float] | None, optional
        Function to parse the field value to a numeric value for sorting.
        If None, uses the default float() parser.

    Returns
    -------
    CustomColumn
        The numeric field column with proper sorting.
    """
    base_provider = FieldReferenceProvider(key)
    numeric_provider = NumericSortAdapter(base_provider, parser=parser)
    return _create_custom_column(
        title,
        key,
        numeric_provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=ColumnSortType.SORTKEY,
        status_icon=status_icon,
    )


def make_script_column(
    title: str,
    key: str,
    script: str,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    max_runtime_ms: int | None = None,
    cache_size: int | None = None,
    parser: ScriptParser | None = None,
    parser_factory: Callable[[], ScriptParser] | None = None,
) -> CustomColumn:
    """Create column whose value is computed by a script.

    Parameters
    ----------
    title, key, script, width, align, always_visible, max_runtime_ms, cache_size
        Column and provider configuration.

    Returns
    -------
    CustomColumn
        The script-backed column.
    """
    provider = ChainedValueProvider(
        script,
        max_runtime_ms=max_runtime_ms,
        cache_size=cache_size,
        parser=parser,
        parser_factory=parser_factory,
    )
    return _create_custom_column(
        title,
        key,
        provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=ColumnSortType.TEXT,
    )


def make_callable_column(
    title: str,
    key: str,
    func: Callable[[Item], str],
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    sort_type: ColumnSortType | None = None,
    status_icon: bool = False,
) -> CustomColumn:
    """Create column backed by a Python callable.

    Parameters
    ----------
    title, key, func, width, align, always_visible, sort_type
        Column and provider configuration.

    Returns
    -------
    CustomColumn
        The callable-backed column.
    """
    provider = CallableProvider(func)
    return _create_custom_column(
        title,
        key,
        provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=sort_type,
        status_icon=status_icon,
    )


def make_transformed_column(
    title: str,
    key: str,
    base: ColumnValueProvider | None = None,
    *,
    transform: Callable[[str], str] = lambda s: s,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
) -> CustomColumn:
    """Create column from a base provider transformed by a function.

    Parameters
    ----------
    title, key, base, transform, width, align, always_visible
        Column and provider configuration.

    Returns
    -------
    CustomColumn
        The transformed column.
    """
    base_provider = base or FieldReferenceProvider(key)
    provider = TransformProvider(base_provider, transform)
    return _create_custom_column(
        title,
        key,
        provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=ColumnSortType.TEXT,
    )


def make_provider_column(
    title: str,
    key: str,
    provider: ColumnValueProvider,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    sort_type: ColumnSortType | None = None,
) -> CustomColumn:
    """Create column backed directly by a provider with sort inference.

    Parameters
    ----------
    title, key, provider, width, align, always_visible, sort_type
        Column configuration. If ``sort_type`` is ``None`` it will be
        inferred from the provider's capabilities (``SORTKEY`` if the
        provider implements a ``sort_key`` method, otherwise ``TEXT``).

    Returns
    -------
    CustomColumn
        The provider-backed column.
    """
    return _create_custom_column(
        title,
        key,
        provider,
        width=width,
        align=align,
        always_visible=always_visible,
        sort_type=sort_type,
    )


def make_delegate_column(
    title: str,
    key: str,
    provider: DelegateProvider,
    *,
    width: int | None = None,
    align: ColumnAlign = ColumnAlign.LEFT,
    always_visible: bool = False,
    sort_type: ColumnSortType | None = None,
    size: QtCore.QSize | None = None,
    sort_provider: SortKeyProvider | None = None,
) -> DelegateColumn:
    """Create column that uses a delegate for custom rendering.

    Parameters
    ----------
    title, key, provider, width, align, always_visible, sort_type
        Column configuration.

    Returns
    -------
    DelegateColumn
        The delegate column.
    """
    resolved_sort_type = sort_type or ColumnSortType.TEXT
    return DelegateColumn(
        title,
        key,
        provider,
        width=width,
        align=align,
        sort_type=resolved_sort_type,
        always_visible=always_visible,
        size=size,
        sort_provider=sort_provider,
    )


def make_icon_header_column(
    title: str,
    key: str,
    provider: HeaderIconProvider,
    *,
    icon_width: int,
    icon_height: int,
    border: int = 0,
) -> IconColumn:
    """Create an icon header column from a header icon provider.

    Parameters
    ----------
    title, key
        Column configuration.
    provider
        Object implementing `HeaderIconProvider`.
    icon_width, icon_height, border
        Header icon sizing and border.
    """
    column = IconColumn(title, key, provider, width=None)
    column.set_header_icon_size(icon_width, icon_height, border)
    return column

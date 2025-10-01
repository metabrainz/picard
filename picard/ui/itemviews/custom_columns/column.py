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

from PyQt6 import QtCore, QtGui

from picard.ui.columns import (
    Column,
    ColumnAlign,
    ColumnSortType,
    ImageColumn,
)
from picard.ui.itemviews.custom_columns.protocols import (
    CacheInvalidatable,
    ColumnValueProvider,
    DelegateProvider,
    HeaderIconProvider,
    SortKeyProvider,
)


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
        *,
        status_icon: bool = False,
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
            status_icon=status_icon,
        )
        self.provider = provider

    def invalidate_cache(self, obj=None):  # pragma: no cover - UI-driven
        """Invalidate any caches on the provider if supported.

        Parameters
        ----------
        obj
            Optional item to invalidate for; if omitted, clears entire cache.
        """
        if isinstance(self.provider, CacheInvalidatable):
            # type: ignore[attr-defined]
            self.provider.invalidate(obj)  # noqa: PGH003


class DelegateColumn(Column):
    """A column that uses a delegate for custom rendering and optional sorting."""

    def __init__(
        self,
        title: str,
        key: str,
        provider: DelegateProvider,
        width: int | None = None,
        align: ColumnAlign = ColumnAlign.LEFT,
        sort_type: ColumnSortType = ColumnSortType.TEXT,
        always_visible: bool = False,
        size: QtCore.QSize | None = None,
        *,
        status_icon: bool = False,
        sort_provider: SortKeyProvider | None = None,
    ):
        """Create delegate column.

        Parameters
        ----------
        title
            Display title of the column.
        key
            Internal key used to identify the column.
        provider
            Provide delegate class and data for rendering.
        width
            Optional fixed width in pixels.
        align
            Set text alignment.
        sort_type
            Set sorting behavior of the column.
        always_visible
            If True, hide the column visibility toggle.
        size
            Preferred delegate size.
        """

        sortkey_fn = None
        if sort_type == ColumnSortType.SORTKEY:
            if isinstance(sort_provider, SortKeyProvider):
                sortkey_fn = sort_provider.sort_key  # type: ignore[assignment]
            elif isinstance(provider, SortKeyProvider):
                # Fallback for backward compatibility if provider implements sorting
                sortkey_fn = provider.sort_key  # type: ignore[assignment]

        super().__init__(
            title,
            key,
            width=width,
            align=align,
            sort_type=sort_type,
            sortkey=sortkey_fn,
            always_visible=always_visible,
            status_icon=status_icon,
        )
        self.delegate_provider = provider
        self.size = size if size is not None else QtCore.QSize(16, 16)  # Default icon size

    @property
    def delegate_class(self):
        """Get the delegate class for this column."""
        return self.delegate_provider.get_delegate_class()


class IconColumn(ImageColumn):
    """A column that paints a header icon provided by a `HeaderIconProvider`.

    The header icon is constructed lazily via the provider to avoid creating
    Qt objects before the application is initialized.
    """

    _header_icon: QtGui.QIcon | None = None

    def __init__(self, title: str, key: str, provider: HeaderIconProvider, *, width: int | None = None) -> None:
        super().__init__(
            title,
            key,
            width=width,
            align=ColumnAlign.LEFT,
            sort_type=ColumnSortType.TEXT,
            sortkey=None,
            always_visible=False,
            status_icon=False,
        )
        self._provider = provider
        self.header_icon_size = QtCore.QSize(0, 0)
        self.header_icon_border = 0
        self.size = QtCore.QSize(0, 0)

    @property
    def header_icon(self) -> QtGui.QIcon | None:
        """Get the header icon for this column.

        Returns
        -------
        QtGui.QIcon | None
            The header icon, or None if no icon is available.
        """
        if self._header_icon is None:
            self._header_icon = self._provider.get_icon()
        return self._header_icon

    def set_header_icon_size(self, width: int, height: int, border: int) -> None:
        """Set the header icon size and border.

        Parameters
        ----------
        width : int
            Width of the icon in pixels.
        height : int
            Height of the icon in pixels.
        border : int
            Border size around the icon in pixels.
        """
        self.header_icon_size = QtCore.QSize(width, height)
        self.header_icon_border = border
        self.size = QtCore.QSize(width + 2 * border, height + 2 * border)
        self.width = self.size.width()

    def paint(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:  # pragma: no cover - GUI rendering
        """Paint the header icon in the specified rectangle.

        Parameters
        ----------
        painter : QtGui.QPainter
            The painter to use for drawing.
        rect : QtCore.QRect
            The rectangle where the icon should be painted.
        """
        icon = self.header_icon
        if not icon:
            return
        h = self.header_icon_size.height()
        w = self.header_icon_size.width()
        border = self.header_icon_border
        padding_v = (rect.height() - h) // 2
        target_rect = QtCore.QRect(rect.x() + border, rect.y() + padding_v, w, h)
        painter.drawPixmap(target_rect, icon.pixmap(self.header_icon_size))

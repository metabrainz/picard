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

"""Shared helpers for custom columns."""

from __future__ import annotations

from typing import Iterable

from picard.i18n import gettext as _

from picard.ui.columns import ColumnAlign


# Public identifiers for views used in configuration and API
VIEW_FILE: str = "FILE_VIEW"
VIEW_ALBUM: str = "ALBUM_VIEW"

# Default order when both are selected
DEFAULT_ADD_TO: str = f"{VIEW_FILE},{VIEW_ALBUM}"

RECOGNIZED_VIEWS: set[str] = {VIEW_FILE, VIEW_ALBUM}

_ALIGN_TOKEN_TO_ENUM: dict[str, ColumnAlign] = {
    "LEFT": ColumnAlign.LEFT,
    "RIGHT": ColumnAlign.RIGHT,
}


def parse_add_to(add_to: str | None) -> set[str]:
    """Parse a comma-separated ``add_to`` string into normalized view tokens.

    Parameters
    ----------
    add_to : str | None
        Comma-separated list of view identifiers (e.g., ``"FILE_VIEW,ALBUM_VIEW"``).
        If falsy, defaults to both views as defined by ``DEFAULT_ADD_TO``.

    Returns
    -------
    set[str]
        Set of recognized, upper-cased view identifiers.

    Notes
    -----
    Unknown tokens are ignored. Recognition is case-insensitive and whitespace
    around tokens is stripped before matching.
    """

    raw: str = add_to or DEFAULT_ADD_TO
    tokens: Iterable[str] = (t.strip().upper() for t in raw.split(",") if t.strip())
    return {t for t in tokens if t in RECOGNIZED_VIEWS}


def format_add_to(views: Iterable[str]) -> str:
    """Format view identifiers into a normalized, comma-separated string.

    Parameters
    ----------
    views : Iterable[str]
        Iterable of view identifiers (case-insensitive).

    Returns
    -------
    str
        Comma-separated identifiers. Order follows ``DEFAULT_ADD_TO`` for
        recognized views; any additional (unrecognized) tokens are appended in
        alphabetical order for forward-compatibility.
    """

    view_set: set[str] = {v.strip().upper() for v in views if v}
    ordered: list[str] = [v for v in DEFAULT_ADD_TO.split(",") if v in view_set]
    # Include any additional tokens (forward-compat) at the end in alpha order
    extras: list[str] = sorted([v for v in view_set if v not in RECOGNIZED_VIEWS])
    return ",".join([*ordered, *extras])


def get_recognized_view_columns():
    """Return mapping of recognized view identifiers to their columns collections.

    Returns
    -------
    dict[str, Any]
        Mapping from view id (e.g., ``FILE_VIEW``) to the corresponding
        columns collection. Performed via a local import to avoid stale
        references and import-time side effects.
    """

    from picard.ui.itemviews.columns import (
        ALBUMVIEW_COLUMNS,
        FILEVIEW_COLUMNS,
    )

    return {
        VIEW_FILE: FILEVIEW_COLUMNS,
        VIEW_ALBUM: ALBUMVIEW_COLUMNS,
    }


def get_align_options() -> list[tuple[str, ColumnAlign]]:
    """Return alignment options for UI selection.

    Returns
    -------
    list[tuple[str, ColumnAlign]]
        Pairs of translated, lowercase labels and corresponding
        :class:`~picard.ui.columns.ColumnAlign` values.
    """

    return [(_("left"), _ALIGN_TOKEN_TO_ENUM["LEFT"]), (_("right"), _ALIGN_TOKEN_TO_ENUM["RIGHT"])]


def normalize_align_name(name: str | ColumnAlign | None) -> ColumnAlign:
    """Normalize arbitrary alignment input to a :class:`ColumnAlign` value.

    Parameters
    ----------
    name : str | ColumnAlign | None
        User-provided alignment token (e.g., ``"left"``/``"RIGHT"``), an
        existing :class:`ColumnAlign` value, or ``None``.

    Returns
    -------
    ColumnAlign
        Normalized alignment value. Defaults to ``ColumnAlign.LEFT`` when the
        input is falsy or unrecognized.
    """

    if isinstance(name, ColumnAlign):
        return name
    token = (name or "").strip().upper()
    return _ALIGN_TOKEN_TO_ENUM.get(token, ColumnAlign.LEFT)


def display_align_label(name: str | ColumnAlign | None) -> str:
    """Return translated, lowercase label for an alignment value.

    Parameters
    ----------
    name : str | ColumnAlign | None
        Alignment token or enum; handled case-insensitively.

    Returns
    -------
    str
        Translated label (``"left"`` or ``"right"``).
    """

    enum_val = normalize_align_name(name)
    return _("right") if enum_val == ColumnAlign.RIGHT else _("left")

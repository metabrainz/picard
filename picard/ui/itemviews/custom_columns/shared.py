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

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable
import uuid

from picard.i18n import (
    N_,
    gettext as _,
)

from picard.ui.columns import ColumnAlign


# Public table column indices for specs table and shared header labels
class ColumnIndex(IntEnum):
    TITLE = 0
    TYPE = 1
    EXPRESSION = 2
    ALIGN = 3
    WIDTH = 4


# Public headers for specs-related UIs (manager table, dialogs, etc.)
COLUMN_INPUT_FIELD_NAMES: dict[ColumnIndex, str] = {
    ColumnIndex.TITLE: _("Column Title"),
    ColumnIndex.TYPE: _("Type"),
    ColumnIndex.EXPRESSION: _("Expression"),
    ColumnIndex.ALIGN: _("Align"),
    ColumnIndex.WIDTH: _("Width"),
}


# Public identifiers for views used in configuration and API
VIEW_FILE: str = "FILE_VIEW"
VIEW_ALBUM: str = "ALBUM_VIEW"

# Default order when both are selected
DEFAULT_ADD_TO: str = f"{VIEW_FILE},{VIEW_ALBUM}"

RECOGNIZED_VIEWS: set[str] = {VIEW_FILE, VIEW_ALBUM}

ALIGN_LEFT_NAME: str = "LEFT"
ALIGN_RIGHT_NAME: str = "RIGHT"
_ALIGN_TOKEN_TO_ENUM: dict[str, ColumnAlign] = {
    ALIGN_LEFT_NAME: ColumnAlign.LEFT,
    ALIGN_RIGHT_NAME: ColumnAlign.RIGHT,
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


@dataclass(frozen=True, slots=True)
class ViewPresentation:
    """Presentation metadata for a selectable view.

    Notes
    -----
    ``title`` and ``tooltip`` are NOT translated here. They are marked for
    translation using ``N_()`` and must be wrapped in ``_()`` at the usage
    site (e.g., UI code) to request the localized strings.

    Attributes
    ----------
    id : str
        Stable identifier of the view (e.g., ``FILE_VIEW``).
    title : str
        Untranslated title string; wrap with ``_()`` when used.
    tooltip : str
        Untranslated tooltip string; wrap with ``_()`` when used.
    """

    id: str
    title: str
    tooltip: str


_VIEW_TITLES: dict[str, str] = {
    VIEW_FILE: N_("File view"),
    VIEW_ALBUM: N_("Album view"),
}

_VIEW_TOOLTIPS: dict[str, str] = {
    VIEW_FILE: N_("Show this column in the Files view."),
    VIEW_ALBUM: N_("Show this column in the Albums view."),
}


def get_ordered_view_presentations() -> tuple[ViewPresentation, ...]:
    """Return ordered presentations for all recognized views.

    Returns
    -------
    tuple[ViewPresentation, ...]
        View presentations ordered according to ``DEFAULT_ADD_TO`` first,
        then any remaining recognized views in alphabetical order.
    """

    default_order = [v for v in DEFAULT_ADD_TO.split(",") if v in RECOGNIZED_VIEWS]
    remaining = sorted([v for v in RECOGNIZED_VIEWS if v not in default_order])
    ordered_ids = [*default_order, *remaining]
    return tuple(
        ViewPresentation(
            id=vid,
            title=_VIEW_TITLES.get(vid, vid),
            tooltip=_VIEW_TOOLTIPS.get(vid, ""),
        )
        for vid in ordered_ids
    )


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

    return [(N_("left"), _ALIGN_TOKEN_TO_ENUM["LEFT"]), (N_("right"), _ALIGN_TOKEN_TO_ENUM["RIGHT"])]


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


def next_incremented_title(base_title: str, existing_titles: set[str]) -> str:
    """Generate the next incremented title by appending a numeric suffix.

    Parameters
    ----------
    base_title : str
        The base title to increment.
    existing_titles : set[str]
        Set of existing titles to avoid conflicts.

    Returns
    -------
    str
        The next available incremented title with format "base_title (N)".

    Examples
    --------
    >>> next_incremented_title("Album", {"Album", "Album (1)"})
    'Album (2)'
    """
    suffix = 1
    candidate: str = f"{base_title} ({suffix})"
    while candidate in existing_titles:
        suffix += 1
        candidate = f"{base_title} ({suffix})"
    return candidate


def generate_new_key() -> str:
    """Generate a new unique key for a custom column.

    Returns
    -------
    str
        A freshly generated unique key.
    """
    return str(uuid.uuid4())


# Mapping of user-friendly names to sorting adapter class names
SORTING_ADAPTER_NAMES: dict[str, str] = {
    N_("Default"): "",  # No adapter (use default sorting)
    N_("Case Insensitive"): "CasefoldSortAdapter",
    N_("Case Insensitive - Descending"): "DescendingCasefoldSortAdapter",
    N_("Numeric"): "NumericSortAdapter",
    N_("Numeric - Descending"): "DescendingNumericSortAdapter",
    N_("Natural"): "NaturalSortAdapter",
    N_("Natural - Descending"): "DescendingNaturalSortAdapter",
    N_("By Value Length"): "LengthSortAdapter",
    N_("Article Insensitive"): "ArticleInsensitiveAdapter",
    N_("Empty Values Last"): "NullsLastAdapter",
    N_("Empty Values First"): "NullsFirstAdapter",
}


def get_sorting_adapter_options() -> tuple[tuple[str, str], ...]:
    """Return sorting adapter options for UI selection.

    Returns
    -------
    tuple[tuple[str, str], ...]
        Sorted pairs of user-friendly display names and corresponding adapter class names.
        The "Default" option always appears first.
    """
    # Get the Default item directly
    default_name = N_("Default")
    default_item = (default_name, SORTING_ADAPTER_NAMES[default_name])

    # Get other items (excluding Default) and sort them
    other_items = sorted(
        [(name, class_name) for name, class_name in SORTING_ADAPTER_NAMES.items() if name != default_name],
        key=lambda x: x[0],
    )

    # Return tuple with Default first, then sorted others
    return tuple([default_item] + other_items)

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2021, 2024-2026 Laurent Monin
# Copyright (C) 2019-2022 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

"""UI-independent default interface color values.

This module holds the default color values for the light and dark themes as
plain, pre-normalized ``#rrggbb`` strings. It deliberately has no dependencies
(no PyQt6, no picard.i18n, no picard.config) so that core modules such as
``picard.options`` can seed the ``interface_colors`` / ``interface_colors_dark``
options without importing the GUI layer.

Human-readable color descriptions (and the interactive, theme-aware
``InterfaceColors`` class that reads/writes config and reacts to theme
changes) live in ``picard.ui.colors``; that module builds on the values
defined here.

The values below are the Qt-normalized form (``QColor(value).name()``) of the
historical named/short-hex definitions, so the option defaults remain
byte-identical to previous releases. When changing a color, keep it in
``#rrggbb`` lower-case form.
"""

# Default color values per theme, keyed by color id.
DEFAULT_INTERFACE_COLORS = {
    'light': {
        'entity_error': '#c80000',
        'entity_pending': '#808080',
        'entity_saved': '#00aa00',
        'first_cover_hl': '#b8860b',
        'log_debug': '#800080',
        'log_error': '#ff0000',
        'log_info': '#000000',
        'log_warning': '#ff8c00',
        'match_similarity_low': '#df7d7d',
        'profile_hl_bg': '#f9f906',
        'profile_hl_fg': '#000000',
        'syntax_hl_error': '#ff0000',
        'syntax_hl_escape': '#8b0000',
        'syntax_hl_func': '#0000ff',
        'syntax_hl_noop': '#a9a9a9',
        'syntax_hl_special': '#0000ff',
        'syntax_hl_unicode': '#8b0000',
        'syntax_hl_var': '#008b8b',
        'tagstatus_added': '#008000',
        'tagstatus_changed': '#b8860b',
        'tagstatus_removed': '#ff0000',
    },
    'dark': {
        'entity_error': '#c80000',
        'entity_pending': '#808080',
        'entity_saved': '#00aa00',
        'first_cover_hl': '#ffa500',
        'log_debug': '#dda0dd',
        'log_error': '#ff0000',
        'log_info': '#ffffff',
        'log_warning': '#ff8c00',
        'match_similarity_low': '#df7d7d',
        'profile_hl_bg': '#1c71d8',
        'profile_hl_fg': '#ffffff',
        'syntax_hl_error': '#f16161',
        'syntax_hl_escape': '#4bef1f',
        'syntax_hl_func': '#ff57a0',
        'syntax_hl_noop': '#04e7d5',
        'syntax_hl_special': '#ff57a0',
        'syntax_hl_unicode': '#4bef1f',
        'syntax_hl_var': '#fcbb51',
        'tagstatus_added': '#008000',
        'tagstatus_changed': '#b8860b',
        'tagstatus_removed': '#ff0000',
    },
}


def default_interface_colors(dark_theme):
    """Return a ``{color_id: #rrggbb}`` mapping of default colors for a theme.

    A fresh copy is returned so callers may mutate it safely.
    """
    key = 'dark' if dark_theme else 'light'
    return dict(DEFAULT_INTERFACE_COLORS[key])

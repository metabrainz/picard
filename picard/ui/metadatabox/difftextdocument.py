# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

"""Qt display layer for diff highlighting in the metadata box.

This module bridges the pure diff logic (tagdiffhtml) with Qt,
providing color resolution from the theme and QTextDocument creation
for rendering.
"""

from PyQt6 import QtGui

from picard.ui.colors import interface_colors
from picard.ui.metadatabox.tagdiffhtml import (
    compute_diff,
    highlight_full,
)


def _get_diff_colors() -> tuple[str, str]:
    """Return (removed_bg, added_bg) as CSS rgba strings with transparency."""
    removed = interface_colors.get_qcolor('tagstatus_removed')
    added = interface_colors.get_qcolor('tagstatus_added')
    removed_bg = f'rgba({removed.red()}, {removed.green()}, {removed.blue()}, 60)'
    added_bg = f'rgba({added.red()}, {added.green()}, {added.blue()}, 60)'
    return removed_bg, added_bg


def compute_diff_html(
    old_text: str,
    new_text: str,
    text_color: QtGui.QColor,
) -> tuple[str | None, str | None]:
    """Compute diff HTML using the current theme colors.

    Resolves Qt theme colors and delegates to the pure diff logic.

    Args:
        old_text: The original text string.
        new_text: The new text string.
        text_color: QColor for the base text.

    Returns:
        A tuple (old_html, new_html) with highlighted differences.
        Returns (None, None) if inputs are identical.
    """
    if old_text == new_text:
        return None, None
    removed_bg, added_bg = _get_diff_colors()
    return compute_diff(old_text, new_text, removed_bg, added_bg, text_color.name())


def compute_full_diff_html(
    old_text: str,
    new_text: str,
    text_color: QtGui.QColor,
) -> tuple[str | None, str | None]:
    """Highlight entire old/new strings as fully replaced.

    Used for opaque values (MBIDs, etc.) where character-level diff
    is meaningless.

    Args:
        old_text: The original text string.
        new_text: The new text string.
        text_color: QColor for the base text.

    Returns:
        A tuple (old_html, new_html) with full-string highlights.
        Returns (None, None) if inputs are identical.
    """
    if old_text == new_text:
        return None, None
    removed_bg, added_bg = _get_diff_colors()
    return highlight_full(old_text, new_text, removed_bg, added_bg, text_color.name())


def create_diff_document(html: str, font: QtGui.QFont) -> QtGui.QTextDocument:
    """Create a QTextDocument configured for rendering diff HTML.

    Args:
        html: HTML string with diff markup.
        font: QFont to use for the document.

    Returns:
        A QTextDocument ready for painting.
    """
    doc = QtGui.QTextDocument()
    doc.setDefaultFont(font)
    doc.setDocumentMargin(2)
    doc.setHtml(html)
    return doc

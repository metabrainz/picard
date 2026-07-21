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

This module provides QTextDocument creation for rendering diff HTML
produced by the tagdiffhtml module.
"""

from PyQt6 import QtGui


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

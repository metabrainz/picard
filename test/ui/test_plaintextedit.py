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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6 import QtCore
from PyQt6.QtGui import (
    QColor,
    QTextCharFormat,
    QTextCursor,
)

import pytest

from picard.ui.widgets.plaintextedit import PlainTextEdit


MONOSPACE = "Monospace"


@pytest.fixture()
def edit(qapp):
    widget = PlainTextEdit(None, font_family=MONOSPACE)
    yield widget
    widget.deleteLater()


def _paste(widget, text):
    mime = QtCore.QMimeData()
    mime.setText(text)
    widget.insertFromMimeData(mime)


def test_rich_text_disabled(edit):
    assert edit.acceptRichText() is False


def test_font_family_applied_to_widget_and_document(edit):
    assert edit.font().family() == MONOSPACE
    assert edit.document().defaultFont().family() == MONOSPACE


def test_no_font_family_leaves_document_default(qapp):
    widget = PlainTextEdit(None)
    try:
        # Without an explicit family we do not touch the document default font.
        assert widget.acceptRichText() is False
    finally:
        widget.deleteLater()


def test_paste_after_blank_line_keeps_default_font(edit):
    """Reproduces the reported bug generically: paste after a blank line."""
    edit.setPlainText("first line")
    cursor = edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    edit.setTextCursor(cursor)
    edit.textCursor().insertText("\n\n")

    _paste(edit, "pasted")

    # Document default font remains monospace, so the effective render is stable.
    assert edit.document().defaultFont().family() == MONOSPACE
    cursor = edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    families = cursor.charFormat().fontFamilies()
    if families:
        assert MONOSPACE in families


def test_paste_strips_foreign_font_and_color(edit):
    """Even if the current char format carries foreign formatting, paste resets it."""
    # Simulate the current char format having a different font and color, as can
    # happen after various editor interactions.
    fmt = QTextCharFormat()
    fmt.setFontFamilies(["Some Serif Font"])
    fmt.setForeground(QColor("red"))
    edit.setCurrentCharFormat(fmt)

    _paste(edit, "pasted text")

    cursor = edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    pasted_format = cursor.charFormat()
    families = pasted_format.fontFamilies()
    # The pasted run must not carry the foreign serif family.
    assert "Some Serif Font" not in families


def test_clean_pasted_text_hook_is_used(qapp):
    class UpperEdit(PlainTextEdit):
        def clean_pasted_text(self, text):
            return text.upper()

    widget = UpperEdit(None, font_family=MONOSPACE)
    try:
        _paste(widget, "hello")
        assert widget.toPlainText() == "HELLO"
    finally:
        widget.deleteLater()


def test_insert_from_mime_data_handles_none_source(edit):
    # Should not raise if given an empty/None-like source text.
    mime = QtCore.QMimeData()
    edit.insertFromMimeData(mime)
    assert edit.toPlainText() == ""

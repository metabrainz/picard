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


"""A ``QTextEdit`` base class for editing plain text / code.

``QTextEdit`` is a rich-text widget. When it is (mis)used to edit plain text or
code, two related problems appear on paste:

1. Rich clipboard content (HTML) brings its own fonts, colors and sizes, which
   get inserted verbatim.
2. Even for plain text, the inserted run can carry a character format that
   differs from the widget's intended font. This is most visible when pasting
   after an empty line: the current character format has reverted to the
   application default font and the pasted text picks that up, changing the
   editor font for the rest of the session.

``PlainTextEdit`` centralizes the fix so every code/plain-text editor behaves
consistently:

- Rich text input is disabled (``setAcceptRichText(False)``).
- The widget font and the document *default* font are kept in sync, so text
  always falls back to the intended font instead of the application default.
- ``insertFromMimeData`` strips formatting from pasted content and re-applies
  the widget's default character format, so a paste can never carry foreign
  fonts, colors or sizes into the document.

Subclasses that need to transform pasted text further (for example to escape
control characters) should override :meth:`clean_pasted_text`.
"""

from PyQt6 import (
    QtCore,
    QtGui,
)
from PyQt6.QtWidgets import QTextEdit


class PlainTextEdit(QTextEdit):
    """``QTextEdit`` configured for editing plain text / code.

    Parameters
    ----------
    parent : QtWidgets.QWidget | None
        Parent widget.
    font_family : str | None
        Optional font family to force (e.g. a monospace family). When given it
        is applied both to the widget and to the document default font so that
        typed or pasted text always renders in that family.
    """

    def __init__(self, parent=None, *, font_family: str | None = None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        if font_family is not None:
            # Apply the font family to both the widget and the document default
            # font. Setting only the current character format (setFontFamily) is
            # not enough: the document default font stays at the application
            # default and text reverts to it whenever the current character
            # format is reset (e.g. on an empty line). Setting the document
            # default font makes the chosen family the reliable fallback.
            font = QtGui.QFont(self.font())
            font.setFamily(font_family)
            self.setFont(font)
            if document := self.document():
                document.setDefaultFont(font)

    def clean_pasted_text(self, text: str) -> str:
        """Transform pasted text before insertion.

        The base implementation returns the text unchanged. Subclasses can
        override this to, for example, escape control characters.
        """
        return text

    def insertFromMimeData(self, source):  # noqa: N802 (Qt-style API)
        text = self.clean_pasted_text(source.text() if source is not None else '')
        # Create a new data object with plain text only. Modifying the existing
        # one does not work on Windows when copying from outside the Qt app.
        cleaned = QtCore.QMimeData()
        cleaned.setText(text)

        # Insert using the widget's default character format so pasted text
        # never carries a foreign font/color/size, and never reverts to the
        # application default font. Leaving this format active also keeps text
        # typed right after the paste consistent with the editor font.
        default_format = QtGui.QTextCharFormat()
        default_format.setFont(self.font())
        self.setCurrentCharFormat(default_format)
        super().insertFromMimeData(cleaned)

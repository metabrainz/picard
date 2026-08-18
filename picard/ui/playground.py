# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Bob Swift
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


from collections.abc import Callable

from PyQt6.QtCore import (
    QSignalBlocker,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QTextBlockFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from picard.i18n import gettext as _

from picard.ui.colors import (
    interface_colors,
    stylesheet_validation_error,
)


class Playground(QGroupBox):
    """Self-contained playground widget.

    A group box containing an optional error label and a QPlainTextEdit
    for entering test data. The error label is hidden by default and
    shown only when set_error() is called.
    """

    textChanged = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setFlat(True)
        font = self.font()
        font.setItalic(True)
        self.setFont(font)

        layout = QVBoxLayout(self)

        self._error_label = QLabel(self)
        self._error_label.setStyleSheet(stylesheet_validation_error())
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        self._text_edit = QPlainTextEdit(self)
        layout.addWidget(self._text_edit)

        self._text_edit.textChanged.connect(self.textChanged.emit)

    def _skip_hl(self, text: str) -> str:
        """Wrap text in an HTML span with the skip (red) highlight color."""
        color = self._highlight_color('tagstatus_removed')
        return f'<span style="background-color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()}); padding: 2px;">{text}</span>'

    def _match_hl(self, text: str) -> str:
        """Wrap text in an HTML span with the match (green) highlight color."""
        color = self._highlight_color('tagstatus_added')
        return f'<span style="background-color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()}); padding: 2px;">{text}</span>'

    def set_description(self, description: str, match_meaning: str, skip_meaning: str) -> None:
        """Configure the playground tooltip and placeholder text.

        Sets a tooltip and placeholder on the playground widget with a
        consistent layout. All string parameters must already be translated
        by the caller.

        Args:
            description: What the playground does (e.g., "Enter file paths to test, one per line.")
            match_meaning: What green/match means (e.g., "the file path matches")
            skip_meaning: What red/skip means (e.g., "the file path does not match")
        """
        from html import escape

        not_preserved = _("This playground will not be preserved on exit.")
        tooltip = ("<p>%(description)s</p><p>%(skip_line)s<br/>%(match_line)s</p><p><i>%(not_preserved)s</i></p>") % {
            'description': escape(description),
            'skip_line': self._skip_hl(escape(_("Red: %s.") % skip_meaning)),
            'match_line': self._match_hl(escape(_("Green: %s.") % match_meaning)),
            'not_preserved': escape(not_preserved),
        }
        self.setToolTip(tooltip)
        self._text_edit.setPlaceholderText(description)

    def set_error(self, message: str) -> None:
        """Show an error message above the text area.

        Args:
            message: The error message to display.
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def clear_error(self) -> None:
        """Hide the error message."""
        self._error_label.setText("")
        self._error_label.setVisible(False)

    def toPlainText(self) -> str:
        """Return the playground text content."""
        return self._text_edit.toPlainText()

    @staticmethod
    def _highlight_color(color_key):
        alpha = 90 if interface_colors.dark_theme else 60
        color = interface_colors.get_qcolor(color_key)
        color.setAlpha(alpha)
        return color

    def _get_fmt_match(self) -> QTextBlockFormat:
        """Return the block format for matching lines."""
        fmt = QTextBlockFormat()
        fmt.setBackground(self._highlight_color('tagstatus_added'))
        return fmt

    def _get_fmt_skip(self) -> QTextBlockFormat:
        """Return the block format for non-matching lines."""
        fmt = QTextBlockFormat()
        fmt.setBackground(self._highlight_color('tagstatus_removed'))
        return fmt

    def _get_fmt_clear(self) -> QTextBlockFormat:
        """Return the block format for cleared (neutral) lines."""
        fmt = QTextBlockFormat()
        fmt.clearBackground()
        return fmt

    def _set_line_fmt(self, lineno, textformat):
        cursor = QTextCursor(self._text_edit.document().findBlockByNumber(lineno))
        cursor.setBlockFormat(textformat)

    def update(self, match_function: Callable[[str], bool] | None = None) -> None:
        """Update the playground to color-code each line depending on whether it passes the match function.

        Args:
            match_function: A function that takes a string and returns True if the string matches, otherwise False. Default is None.
        """
        fmt_match = self._get_fmt_match()
        fmt_skip = self._get_fmt_skip()
        fmt_clear = self._get_fmt_clear()

        text = self._text_edit.toPlainText()
        lines = text.splitlines()
        # Add an empty string to the list of lines to process if the playground text ends with a new line. This is to
        # ensure that the blank line at the end of the playground widget doesn't inherit the color from the previous line.
        if text and text[-1] in "\n\r":
            lines.append('')
        with QSignalBlocker(self._text_edit):
            for lineno, line in enumerate(lines):
                line = line.strip()
                if not line or match_function is None:
                    fmt = fmt_clear
                elif match_function(line):
                    fmt = fmt_match
                else:
                    fmt = fmt_skip
                self._set_line_fmt(lineno, fmt)

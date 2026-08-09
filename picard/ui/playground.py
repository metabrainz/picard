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

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import (
    QTextBlockFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import QPlainTextEdit

from picard.ui.colors import interface_colors


class Playground:
    """Playground widget update manager"""

    def __init__(self, playground_widget: QPlainTextEdit) -> None:
        """Initialize the Playground with a QPlainTextEdit widget.

        Args:
            playground_widget (QPlainTextEdit): The playground widget to update.
        """
        self.playground_widget = playground_widget

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
        cursor = QTextCursor(self.playground_widget.document().findBlockByNumber(lineno))
        cursor.setBlockFormat(textformat)

    def update(self, match_function: Callable[[str], bool] | None = None) -> None:
        """Update the playground widget to color-code each line depending on whether it passes the match function.

        Args:
            match_function: A function that takes a string and returns True if the string matches, otherwise False. Default is None.
        """
        fmt_match = self._get_fmt_match()
        fmt_skip = self._get_fmt_skip()
        fmt_clear = self._get_fmt_clear()

        text = self.playground_widget.toPlainText()
        lines = text.splitlines()
        # Add an empty string to the list of lines to process if the playground text ends with a new line. This is to
        # ensure that the blank line at the end of the playground widget doesn't inherit the color from the previous line.
        if text and text[-1] in "\n\r":
            lines.append('')
        with QSignalBlocker(self.playground_widget):
            for lineno, line in enumerate(lines):
                line = line.strip()
                if not line or match_function is None:
                    fmt = fmt_clear
                elif match_function(line):
                    fmt = fmt_match
                else:
                    fmt = fmt_skip
                self._set_line_fmt(lineno, fmt)

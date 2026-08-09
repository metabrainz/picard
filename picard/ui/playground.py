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

    def _set_line_fmt(self, lineno, textformat):
        obj = self.playground_widget
        if lineno < 0:
            # use current cursor position
            cursor = obj.textCursor()
        else:
            cursor = QTextCursor(obj.document().findBlockByNumber(lineno))
        obj.blockSignals(True)
        cursor.setBlockFormat(textformat)
        obj.blockSignals(False)

    def update(self, match_function: Callable[[str], bool] | None = None) -> None:
        """Update the playground widget to color-code each line depending on whether it passes the match function.

        Args:
            match_function: A function that takes a string and returns True if the string matches, otherwise False. Default is None.
        """
        fmt_match = QTextBlockFormat()
        fmt_match.setBackground(self._highlight_color('tagstatus_added'))

        fmt_skip = QTextBlockFormat()
        fmt_skip.setBackground(self._highlight_color('tagstatus_removed'))

        fmt_clear = QTextBlockFormat()
        fmt_clear.clearBackground()

        self._set_line_fmt(-1, fmt_clear)

        for lineno, line in enumerate(self.playground_widget.toPlainText().splitlines()):
            line = line.strip()
            if not line or match_function is None:
                fmt = fmt_clear
            elif match_function(line):
                fmt = fmt_match
            else:
                fmt = fmt_skip
            self._set_line_fmt(lineno, fmt)

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

        self.fmt_match = QTextBlockFormat()
        self.fmt_match.setBackground(self._highlight_color('tagstatus_added'))

        self.fmt_skip = QTextBlockFormat()
        self.fmt_skip.setBackground(self._highlight_color('tagstatus_removed'))

        self.fmt_clear = QTextBlockFormat()
        self.fmt_clear.clearBackground()

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

    def update(self, match_function: callable = None) -> None:
        """Update the playground widget to color-code each line depending on whether it passes the match function.

        Args:
            match_function (callable): A function that takes a string and returns True if the string matches, otherwise False. Default is None.
        """
        self._set_line_fmt(-1, self.fmt_clear)

        if match_function is None:
            return

        for lineno, line in enumerate(self.playground_widget.toPlainText().splitlines()):
            line = line.strip()
            fmt = self.fmt_clear
            if line:
                if match_function(line):
                    fmt = self.fmt_match
                else:
                    fmt = self.fmt_skip
            self._set_line_fmt(lineno, fmt)

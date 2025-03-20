# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

import math

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)


class FormattedTextDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None, markup_format='html'):
        """
        A QStyledItemDelegate that renders formatted text in a QTreeWidget.

        :param markup_format: Specify the format of the markup, either "html" or "markdown".
        """
        super().__init__(parent)
        self.markup_format = markup_format

    def paint(self, painter, option, index):
        # Initialize the style option
        self.initStyleOption(option, index)

        # Draw the background
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            fill_brush = option.palette.highlight()
            text_color_role = QtGui.QPalette.ColorRole.HighlightedText
        else:
            fill_brush = option.palette.base()
            text_color_role = QtGui.QPalette.ColorRole.Text
        painter.fillRect(option.rect, fill_brush)

        # Get the formatted text from the model
        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if not text:
            return

        # Create a QTextDocument to render the formatted text
        doc = self._create_doc(text, option)

        # Set the text color based on the current palette
        text_color = option.palette.color(text_color_role)
        doc.setDefaultStyleSheet(f"body {{ color: {text_color.name()}; }}")

        # Draw the text
        painter.save()
        painter.translate(option.rect.topLeft())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        # Provide a size hint based on the QTextDocument's size
        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if not text:
            return super().sizeHint(option, index)

        # Create a QTextDocument to render the formatted text
        doc = self._create_doc(text, option)

        return QtCore.QSize(
            math.ceil(doc.idealWidth()),
            math.ceil(doc.size().height()))

    def _create_doc(self, text, option):
        doc = QtGui.QTextDocument()
        if self.markup_format == 'html':
            doc.setHtml(text)
        elif self.markup_format == 'markdown':
            doc.setMarkdown(text)
        else:
            doc.setPlainText(text)

        doc.setDefaultFont(option.font)
        doc.setTextWidth(option.rect.width())
        text_option = doc.defaultTextOption()
        text_option.setWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        doc.setDefaultTextOption(text_option)
        return doc

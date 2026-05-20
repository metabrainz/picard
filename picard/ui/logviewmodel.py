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

import logging

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from PyQt6.QtCore import Qt

from picard import log

from picard.ui.colors import interface_colors


LevelRole = Qt.ItemDataRole.UserRole + 1


class LogItemModel(QtCore.QAbstractListModel):
    """Model storing log entries with level-based foreground colors."""

    def __init__(self, log_tail, parent=None):
        super().__init__(parent)
        self._items = []
        self._log_tail = log_tail
        self._prev_pos = -1
        self._color_cache = {}
        self.refresh_colors()

    def rowCount(self, parent=None):
        return len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return item.message
        if role == Qt.ItemDataRole.ForegroundRole:
            return self._get_color(item.level)
        if role == LevelRole:
            return item.level
        return None

    def _get_color(self, level):
        color = self._color_cache.get(level)
        if color is None:
            feat = log.levels_features.get(level)
            if feat:
                color = interface_colors.get_qcolor(feat.color_key)
            else:
                color = interface_colors.get_qcolor('log_info')
            self._color_cache[level] = color
        return color

    def refresh_colors(self):
        """Reload colors from config and repaint."""
        interface_colors.load_from_config()
        self._color_cache.clear()
        if self._items:
            self.dataChanged.emit(
                self.index(0),
                self.index(len(self._items) - 1),
                [Qt.ItemDataRole.ForegroundRole],
            )

    def append_from_tail(self):
        """Append new entries from the log tail since last read."""
        new_items = list(self._log_tail.contents(self._prev_pos))
        if not new_items:
            return
        start = len(self._items)
        self.beginInsertRows(QtCore.QModelIndex(), start, start + len(new_items) - 1)
        self._items.extend(new_items)
        self._prev_pos = new_items[-1].pos
        self.endInsertRows()

    def clear_entries(self):
        """Clear all entries and reset tail position."""
        self.beginResetModel()
        self._items.clear()
        self._prev_pos = -1
        self.endResetModel()

    def get_all_text(self):
        """Return all log messages as plain text for saving."""
        return '\n'.join(item.message for item in self._items)

    def level_at(self, row):
        """Return the log level for a given row."""
        if 0 <= row < len(self._items):
            return self._items[row].level
        return logging.NOTSET


class LogFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Proxy model that filters log entries by minimum level and text pattern."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_level = logging.NOTSET
        self._text_re = None

    def set_min_level(self, level):
        if level != self._min_level:
            self._min_level = level
            self.invalidateFilter()

    def set_text_filter(self, pattern_re):
        """Set compiled regex for text filtering, or None to show all."""
        self._text_re = pattern_re
        self.invalidateFilter()

    @property
    def min_level(self):
        return self._min_level

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        level = index.data(LevelRole)
        if level is None:
            return False
        if level < self._min_level:
            return False
        if self._text_re:
            text = index.data(Qt.ItemDataRole.DisplayRole) or ''
            if not self._text_re.search(text):
                return False
        return True


class LogItemDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate that paints log entries with optional highlight spans."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlight_re = None

    def set_highlight(self, pattern_re):
        """Set compiled regex for highlight, or None to clear."""
        self._highlight_re = pattern_re

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        painter.save()

        # Let the style draw the background (handles theme, alternating rows, etc.)
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.drawPrimitive(QtWidgets.QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        # Determine text color
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            text_color = option.palette.highlightedText().color()
        else:
            fg = index.data(Qt.ItemDataRole.ForegroundRole)
            text_color = fg if fg else option.palette.text().color()

        text = index.data(Qt.ItemDataRole.DisplayRole) or ''
        rect = option.rect.adjusted(2, 0, -2, 0)
        fm = option.fontMetrics

        # Draw highlight borders around matches
        if self._highlight_re and text:
            hl_color = option.palette.highlight().color()
            painter.setPen(QtGui.QPen(hl_color, 1.0))
            for match in self._highlight_re.finditer(text):
                start_x = fm.horizontalAdvance(text[: match.start()])
                match_w = fm.horizontalAdvance(text[match.start() : match.end()])
                hl_rect = QtCore.QRectF(
                    rect.x() + start_x,
                    rect.y() + 1,
                    match_w,
                    rect.height() - 2,
                )
                painter.drawRect(hl_rect)

        # Draw text
        painter.setPen(text_color)
        painter.setFont(option.font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ''
        widget = option.widget
        if widget:
            available_width = widget.viewport().width() - 4
        else:
            available_width = option.rect.width() - 4
        layout = self._create_layout(text, option.font, available_width)
        return QtCore.QSize(
            int(layout.boundingRect().width()) + 4,
            max(int(layout.boundingRect().height()), option.fontMetrics.height()),
        )

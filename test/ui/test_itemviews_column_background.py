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

from unittest.mock import Mock

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.ui.columns import Columns
from picard.ui.itemviews import TreeItem
from picard.ui.itemviews.basetreeview import BaseTreeView
from picard.ui.itemviews.columns import create_common_columns


class _ColumnsTreeWidget(QtWidgets.QTreeWidget):
    """Minimal tree widget exposing a mutable `columns` like the real views."""

    def __init__(self, columns):
        super().__init__()
        self.columns = columns
        self.setColumnCount(len(columns))


def _make_item(columns):
    tree = _ColumnsTreeWidget(columns)
    obj = Mock()
    obj.column = Mock(return_value='')
    obj.ui_item = None
    item = TreeItem(obj)
    tree.addTopLevelItem(item)
    return tree, item


def test_added_column_receives_row_tint_background(qapp):
    # Regression test for PICARD-3510: after a custom column is added to a view
    # that already has tinted rows, the new column's cell must receive the
    # row's background tint instead of Qt's default (opaque white) brush.
    columns = Columns(create_common_columns()[:3], default_width=100)
    tree, item = _make_item(columns)

    tint = QtGui.QColor('#334455')
    # Initial render: all current columns get the tint.
    item.update_colums_text(bgcolor=tint)
    for i in range(len(columns)):
        assert item.background(i).color().name() == tint.name()

    # A new column is appended at runtime (as the manager dialog does).
    columns.append(create_common_columns()[6])  # 'discsubtitle'
    tree.setColumnCount(len(columns))
    new_index = len(columns) - 1

    # Before re-applying colors, the new cell carries no explicit brush.
    assert item.background(new_index).style() == QtCore.Qt.BrushStyle.NoBrush

    # Re-applying the row's background (what the fix does via refresh_theme)
    # must tint the new column too.
    item.update_colums_text(bgcolor=tint)
    assert item.background(new_index).color().name() == tint.name()


def test_refresh_all_items_data_reapplies_colors(qapp):
    # The column-change refresh path must re-apply the row's background to every
    # column (so a newly added column is tinted, not left white) and recurse
    # into children. Items that tint expose _item_colors(); the refresh must use
    # it instead of calling update_colums_text() with no colours.
    tint = QtGui.QColor('#334455')
    calls = []

    class _TintItem:
        """A track/file-like item that tints via _item_colors()."""

        def __init__(self, children=()):
            self._children = list(children)

        def _item_colors(self):
            return (None, tint)

        def update_colums_text(self, color=None, bgcolor=None):
            calls.append((id(self), color, bgcolor))

        def childCount(self):
            return len(self._children)

        def child(self, i):
            return self._children[i]

    class _PlainItem:
        """A cluster/album-like item without _item_colors()."""

        def update_colums_text(self, color=None, bgcolor=None):
            calls.append((id(self), color, bgcolor))

        def childCount(self):
            return 0

        def child(self, i):  # pragma: no cover - no children
            raise IndexError(i)

    child = _TintItem()
    parent = _TintItem(children=[child])

    fake_view = Mock()
    fake_view.topLevelItemCount.return_value = 1
    fake_view.topLevelItem.return_value = parent

    BaseTreeView._refresh_all_items_data(fake_view)

    # Tinting items are refreshed WITH their background colour (not None), for
    # both the parent and its child.
    assert (id(parent), None, tint) in calls
    assert (id(child), None, tint) in calls

    # A plain item (no _item_colors) is refreshed without colours (text only).
    calls.clear()
    plain = _PlainItem()
    fake_view.topLevelItem.return_value = plain
    BaseTreeView._refresh_all_items_data(fake_view)
    assert calls == [(id(plain), None, None)]

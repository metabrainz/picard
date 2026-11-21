# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 The MusicBrainz Team
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


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.ui.itemviews.fixed_row_height import FixedRowHeightDelegate


def _make_view(texts, delegate_class=FixedRowHeightDelegate):
    view = QtWidgets.QTreeWidget()
    view.setColumnCount(1)
    view.setUniformRowHeights(True)
    view.setItemDelegate(delegate_class(view))
    items = [QtWidgets.QTreeWidgetItem([text]) for text in texts]
    view.addTopLevelItems(items)
    return view, items


def _large_font(view):
    font = QtGui.QFont(view.font())
    font.setPointSize(font.pointSize() * 4)
    return font


def _row_heights(view):
    view.resize(400, 300)
    view.show()
    return [view.visualItemRect(view.topLevelItem(i)).height() for i in range(view.topLevelItemCount())]


def test_uniform_rows_do_not_depend_on_first_row(qapp):
    """A first row needing a taller font (e.g. fallback font) must not resize the view."""
    reference, _items = _make_view(['Album', 'Album'])
    expected = _row_heights(reference)

    view, (first, _second) = _make_view(['Album\u200e', 'Album'])
    first.setFont(0, _large_font(view))
    assert _row_heights(view) == expected

    # Control: a plain delegate lets the first row dictate the height
    view, (first, _second) = _make_view(['Album\u200e', 'Album'], QtWidgets.QStyledItemDelegate)
    first.setFont(0, _large_font(view))
    assert _row_heights(view) != expected


def test_explicit_size_hint_role_is_honoured(qapp):
    view, (item,) = _make_view(['Album'])
    base = _row_heights(view)[0]
    item.setSizeHint(0, QtCore.QSize(10, base + 10))
    assert _row_heights(view)[0] == base + 10

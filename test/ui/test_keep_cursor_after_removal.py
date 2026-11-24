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


from PyQt6 import (
    QtCore,
    QtWidgets,
)

import pytest

from picard.ui.util import keep_cursor_after_removal


def _make_list(names):
    view = QtWidgets.QListWidget()
    view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
    view.addItems(names)
    return view


def _select(view, rows):
    selection_model = view.selectionModel()
    for row in rows:
        selection_model.select(view.model().index(row, 0), QtCore.QItemSelectionModel.SelectionFlag.Select)
    # Set the current index without altering the selection
    selection_model.setCurrentIndex(view.model().index(rows[0], 0), QtCore.QItemSelectionModel.SelectionFlag.NoUpdate)
    assert len(view.selectedIndexes()) == len(rows)


def _texts(view):
    return [view.item(row).text() for row in range(view.count())]


def _selected_texts(view):
    return [item.text() for item in view.selectedItems()]


@pytest.mark.parametrize(
    ('selected_rows', 'expected_current', 'expected_remaining'),
    [
        ([0], 'b', ['b', 'c', 'd']),
        ([1], 'c', ['a', 'c', 'd']),
        ([1, 2], 'd', ['a', 'd']),
        ([0, 2], 'd', ['b', 'd']),
        ([3], 'c', ['a', 'b', 'c']),
        ([2, 3], 'b', ['a', 'b']),
    ],
)
def test_cursor_moves_to_following_row(qapp, selected_rows, expected_current, expected_remaining):
    view = _make_list(['a', 'b', 'c', 'd'])
    _select(view, selected_rows)
    with keep_cursor_after_removal(view):
        for row in sorted(selected_rows, reverse=True):
            view.takeItem(row)
    assert _texts(view) == expected_remaining
    assert view.currentItem().text() == expected_current
    assert _selected_texts(view) == [expected_current]


def test_removing_all_rows(qapp):
    view = _make_list(['a', 'b'])
    _select(view, [0, 1])
    with keep_cursor_after_removal(view):
        view.takeItem(1)
        view.takeItem(0)
    assert _texts(view) == []
    assert not view.currentIndex().isValid()


def test_no_selection_is_a_no_op(qapp):
    view = _make_list(['a', 'b'])
    with keep_cursor_after_removal(view):
        pass
    assert not view.currentIndex().isValid()
    assert _selected_texts(view) == []

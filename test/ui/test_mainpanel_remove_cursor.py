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


from types import SimpleNamespace
from unittest.mock import Mock

from PyQt6 import (
    QtCore,
    QtWidgets,
)

from picard.ui.itemviews import (
    MainPanel,
    TreeItem,
)


class FakeObj:
    def __init__(self, name):
        self.name = name
        self.ui_item = None


def _add(parent, obj):
    item = TreeItem(obj)
    item.setText(0, obj.name)
    if isinstance(parent, QtWidgets.QTreeWidget):
        parent.addTopLevelItem(item)
    else:
        parent.addChild(item)
    return item


def _make_panel(view):
    return SimpleNamespace(_selected_view=view, _ignore_selection_changes=False, update_current_view=Mock())


def _current_obj(view):
    return view.currentItem().obj


def _selected_objs(view):
    return [item.obj for item in view.selectedItems()]


def _make_view():
    view = QtWidgets.QTreeWidget()
    view.setColumnCount(1)
    view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
    return view


def _sync_track_children(track_item, files):
    """Mimic TrackItem.update(): remove trailing child rows, reassign the others.

    A track with a single file shows it in the track row itself.
    """
    if len(files) == 1:
        files[0].ui_item = track_item
        track_item.takeChildren()
        return
    while track_item.childCount() > len(files):
        track_item.takeChild(len(files) - 1).obj = None
    for i, file in enumerate(files):
        track_item.child(i).obj = file


def test_removing_first_of_three_files_moves_to_next_file(qapp):
    view = _make_view()
    track1, track2 = FakeObj('t1'), FakeObj('t2')
    files = [FakeObj('f1'), FakeObj('f2'), FakeObj('f3')]
    track1_item = _add(view, track1)
    for file in files:
        _add(track1_item, file)
    _add(view, track2)
    view.expandAll()
    view.setCurrentItem(files[0].ui_item)

    def remove(objects):
        for obj in objects:
            files.remove(obj)
        _sync_track_children(track1_item, files)

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [files[0]])
    assert _current_obj(view).name == 'f2'
    assert [o.name for o in _selected_objs(view)] == ['f2']


def test_removing_first_of_two_files_moves_to_track_showing_remaining_file(qapp):
    view = _make_view()
    track1, track2 = FakeObj('t1'), FakeObj('t2')
    files = [FakeObj('f1'), FakeObj('f2')]
    track1_item = _add(view, track1)
    for file in files:
        _add(track1_item, file)
    _add(view, track2)
    view.expandAll()
    view.setCurrentItem(files[0].ui_item)

    def remove(objects):
        for obj in objects:
            files.remove(obj)
        _sync_track_children(track1_item, files)

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [files[0]])
    assert view.currentItem() is track1_item
    assert view.selectedItems() == [track1_item]


def test_removing_track_moves_to_next_track(qapp):
    # Removing a track only removes its files: the track row stays, but the
    # cursor moves on to the next track.
    view = _make_view()
    tracks = [FakeObj('t1'), FakeObj('t2'), FakeObj('t3')]
    for track in tracks:
        _add(view, track)
    view.setCurrentItem(tracks[1].ui_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), lambda objects: None, [tracks[1]])
    assert _current_obj(view).name == 't3'
    assert [o.name for o in _selected_objs(view)] == ['t3']


def test_removing_last_row_moves_to_previous(qapp):
    view = _make_view()
    objs = [FakeObj('a'), FakeObj('b')]
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)

    def remove(objects):
        for obj in objects:
            view.takeTopLevelItem(view.indexOfTopLevelItem(obj.ui_item))

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [objs[1]])
    assert _current_obj(view).name == 'a'
    assert [o.name for o in _selected_objs(view)] == ['a']


def test_removing_everything_falls_back_to_update_current_view(qapp):
    view = _make_view()
    obj = FakeObj('a')
    _add(view, obj)
    view.setCurrentItem(obj.ui_item)
    panel = _make_panel(view)

    MainPanel._remove_keeping_cursor(panel, lambda objects: view.clear(), [obj])
    assert view.topLevelItemCount() == 0
    panel.update_current_view.assert_called_once()


def test_removing_surviving_last_track_stays_on_it(qapp):
    # Removing the last track, without files, removes nothing: there is no row
    # below, so the cursor stays on it instead of moving up (repeated Del
    # would otherwise bounce between the last two tracks).
    view = _make_view()
    tracks = [FakeObj('t1'), FakeObj('t2'), FakeObj('t3')]
    for track in tracks:
        _add(view, track)
    view.setCurrentItem(tracks[2].ui_item)
    panel = _make_panel(view)

    for _i in range(2):
        MainPanel._remove_keeping_cursor(panel, lambda objects: None, _selected_objs(view))
        assert _current_obj(view).name == 't3'
        assert [o.name for o in _selected_objs(view)] == ['t3']


def test_removing_parent_skips_its_children(qapp):
    view = _make_view()
    album1, album2 = FakeObj('a1'), FakeObj('a2')
    album1_item = _add(view, album1)
    _add(album1_item, FakeObj('t1'))
    _add(view, album2)
    view.expandAll()
    view.setCurrentItem(album1_item)

    def remove(objects):
        for obj in objects:
            view.takeTopLevelItem(view.indexOfTopLevelItem(obj.ui_item))

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [album1])
    assert _current_obj(view).name == 'a2'
    assert [o.name for o in _selected_objs(view)] == ['a2']


def test_fallback_selects_current_row(qapp):
    # When no candidate row survives, the fallback selects the row Qt made current
    view = _make_view()
    objs = [FakeObj('a'), FakeObj('b'), FakeObj('c')]
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)
    other = FakeObj('d')

    def remove(objects):
        view.clear()
        item = _add(view, other)
        view.selectionModel().setCurrentIndex(
            view.indexFromItem(item), QtCore.QItemSelectionModel.SelectionFlag.NoUpdate
        )

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [objs[1]])
    assert _current_obj(view) is other
    assert _selected_objs(view) == [other]

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
# Copyright (C) 2026 Philipp Wolfer
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

from picard.cluster import Cluster
from picard.track import Track

from picard.ui.itemviews import (
    MainPanel,
    TreeItem,
)


def mock_obj(name, spec=None):
    item = Mock(spec=spec)
    item.name = name
    item.ui_item = None
    item.can_remove = True
    return item


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
    track1, track2 = mock_obj('t1'), mock_obj('t2')
    files = [mock_obj('f1'), mock_obj('f2'), mock_obj('f3')]
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
    track1, track2 = mock_obj('t1'), mock_obj('t2')
    files = [mock_obj('f1'), mock_obj('f2')]
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


def test_removing_item_moves_to_next_item(qapp):
    view = _make_view()
    objs = [mock_obj('t1'), mock_obj('t2'), mock_obj('t3')]
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), lambda objects: None, [objs[1]])
    assert _current_obj(view).name == 't3'
    assert [o.name for o in _selected_objs(view)] == ['t3']


def test_removing_track_stays_on_track(qapp):
    # Removing a track only removes its files: the cursor stays in the track.
    view = _make_view()
    tracks = [mock_obj(name='t1', spec=Track), mock_obj(name='t2', spec=Track), mock_obj(name='t3', spec=Track)]
    for track in tracks:
        _add(view, track)
    view.setCurrentItem(tracks[1].ui_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), lambda objects: None, [tracks[1]])
    assert _current_obj(view).name == 't2'
    assert [o.name for o in _selected_objs(view)] == ['t2']


def test_removing_non_removable_item_stays_on_item(qapp):
    # A non-removable item stays in place: the cursor does not move.
    view = _make_view()
    objs = [mock_obj(name='t1'), mock_obj(name='t2'), mock_obj(name='t3')]
    objs[1].can_remove = False
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), lambda objects: None, [objs[1]])
    assert _current_obj(view).name == 't2'
    assert [o.name for o in _selected_objs(view)] == ['t2']


def test_removing_special_cluster_item_stays_on_item(qapp):
    # A special cluster (e.g. unclustered files) stays: the cursor does not move.
    view = _make_view()
    objs = [mock_obj(name='t1'), mock_obj(name='t2', spec=Cluster), mock_obj(name='t3')]
    objs[1].special = True
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), lambda objects: None, [objs[1]])
    assert _current_obj(view).name == 't2'
    assert [o.name for o in _selected_objs(view)] == ['t2']


def test_removing_last_row_moves_to_previous(qapp):
    view = _make_view()
    objs = [mock_obj('a'), mock_obj('b')]
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
    obj = mock_obj('a')
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
    tracks = [mock_obj('t1'), mock_obj('t2'), mock_obj('t3')]
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
    album1, album2 = mock_obj('a1'), mock_obj('a2')
    album1_item = _add(view, album1)
    _add(album1_item, mock_obj('t1'))
    _add(view, album2)
    view.expandAll()
    view.setCurrentItem(album1_item)

    def remove(objects):
        for obj in objects:
            view.takeTopLevelItem(view.indexOfTopLevelItem(obj.ui_item))

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [album1])
    assert _current_obj(view).name == 'a2'
    assert [o.name for o in _selected_objs(view)] == ['a2']


def test_removing_child_moves_to_next_child(qapp):
    view = _make_view()
    parent1 = mock_obj('p1')
    child1, child2 = mock_obj('c1'), mock_obj('c2')
    parent1_item = _add(view, parent1)
    child1_item = _add(parent1_item, child1)
    _add(parent1_item, child2)
    view.expandAll()
    view.setCurrentItem(child1_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), _remove_rows, [child1])
    assert _current_obj(view).name == 'c2'
    assert [o.name for o in _selected_objs(view)] == ['c2']


def test_removing_last_child_moves_to_previous_child(qapp):
    view = _make_view()
    parent1, parent2 = mock_obj('p1'), mock_obj('p2')
    child1, child2 = mock_obj('c1'), mock_obj('c2')
    parent1_item = _add(view, parent1)
    _add(parent1_item, child1)
    child2_item = _add(parent1_item, child2)
    _add(view, parent2)
    view.expandAll()
    view.setCurrentItem(child2_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), _remove_rows, [child2])
    assert _current_obj(view).name == 'c1'
    assert [o.name for o in _selected_objs(view)] == ['c1']


def test_removing_last_remaining_child_moves_to_parent(qapp):
    view = _make_view()
    parent1, parent2 = mock_obj('p1'), mock_obj('p2')
    child1 = mock_obj('c1')
    parent1_item = _add(view, parent1)
    child1_item = _add(parent1_item, child1)
    _add(view, parent2)
    view.expandAll()
    view.setCurrentItem(child1_item)

    MainPanel._remove_keeping_cursor(_make_panel(view), _remove_rows, [child1])
    assert _current_obj(view).name == 'p1'
    assert [o.name for o in _selected_objs(view)] == ['p1']


def _remove_rows(objects):
    """Remove the rows of objects, whatever their level in the tree."""
    for obj in objects:
        item = obj.ui_item
        (item.parent() or item.treeWidget().invisibleRootItem()).removeChild(item)


def _select(view, *objs):
    view.setCurrentItem(objs[-1].ui_item)
    for obj in objs:
        obj.ui_item.setSelected(True)


def test_removing_all_children_moves_to_parent(qapp):
    # All siblings are removed together: the cursor goes to the parent, not to
    # a removed sibling and then to a row of another hierarchy level.
    view = _make_view()
    parent1, parent2 = mock_obj('p1'), mock_obj('p2')
    child1, child2 = mock_obj('c1'), mock_obj('c2')
    parent1_item = _add(view, parent1)
    _add(parent1_item, child1)
    _add(parent1_item, child2)
    _add(view, parent2)
    view.expandAll()
    _select(view, child1, child2)

    MainPanel._remove_keeping_cursor(_make_panel(view), _remove_rows, [child1, child2])
    assert _current_obj(view).name == 'p1'
    assert [o.name for o in _selected_objs(view)] == ['p1']


def test_removing_last_two_children_moves_to_remaining_sibling(qapp):
    # The previous sibling is removed too: use the nearest sibling that survives.
    view = _make_view()
    parent1, parent2 = mock_obj('p1'), mock_obj('p2')
    child1, child2, child3 = mock_obj('c1'), mock_obj('c2'), mock_obj('c3')
    parent1_item = _add(view, parent1)
    for child in (child1, child2, child3):
        _add(parent1_item, child)
    _add(view, parent2)
    view.expandAll()
    _select(view, child2, child3)

    MainPanel._remove_keeping_cursor(_make_panel(view), _remove_rows, [child2, child3])
    assert _current_obj(view).name == 'c1'
    assert [o.name for o in _selected_objs(view)] == ['c1']


def test_fallback_selects_current_row(qapp):
    # When no candidate row survives, the fallback selects the row Qt made current
    view = _make_view()
    objs = [mock_obj('a'), mock_obj('b'), mock_obj('c')]
    for obj in objs:
        _add(view, obj)
    view.setCurrentItem(objs[1].ui_item)
    other = mock_obj('d')

    def remove(objects):
        view.clear()
        item = _add(view, other)
        view.selectionModel().setCurrentIndex(
            view.indexFromItem(item), QtCore.QItemSelectionModel.SelectionFlag.NoUpdate
        )

    MainPanel._remove_keeping_cursor(_make_panel(view), remove, [objs[1]])
    assert _current_obj(view) is other
    assert _selected_objs(view) == [other]

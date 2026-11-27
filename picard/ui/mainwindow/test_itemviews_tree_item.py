# Picard, the next-generation MusicBrainz tagger
#
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

from unittest.mock import Mock

from picard.ui.itemviews import TreeItem


def test_tree_widget_obj_setter():
    obj1, obj2 = Mock(), Mock()
    item = TreeItem(obj1)
    assert item.obj == obj1
    assert obj1.ui_item == item
    item.obj = obj2
    assert item.obj == obj2
    assert obj2.ui_item == item
    assert obj1.ui_item is None


def test_tree_widget_obj_setter_to_none():
    obj1 = Mock()
    item = TreeItem(obj1)
    assert item.obj == obj1
    assert obj1.ui_item == item
    item.obj = None
    assert item.obj is None
    assert obj1.ui_item is None


def test_tree_widget_obj_setter_ignores_foreign_obj():
    obj1, obj2 = Mock(), Mock()
    item1, item2 = TreeItem(None), TreeItem(None)

    # obj1 references a different TreeItem
    item1.obj = obj1
    obj1.ui_item = item2

    # Updating item1.obj must not invalidate obj1.ui_item
    item1.obj = obj2

    assert item1.obj == obj2
    assert obj2.ui_item == item1
    assert obj1.ui_item == item2

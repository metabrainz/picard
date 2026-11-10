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

"""The "Other versions" menu of an album, built from picard.releasegroup.alternative_versions()."""

from unittest.mock import MagicMock

from PyQt6 import QtCore

import pytest

from picard.ui.itemviews.basetreeview import _build_other_versions_actions


def _version(release_id, name, extra=''):
    return {'id': release_id, 'name': name, 'extra': extra}


@pytest.fixture
def album():
    album = MagicMock()
    album.id = 'b'
    album.release_group.version_headings = 'Tracks / Year'
    return album


def _actions(qapp, album, alternatives):
    parent = QtCore.QObject()
    return parent, list(_build_other_versions_actions(parent, album, alternatives))


def test_a_heading_then_the_versions_divided_by_group(qapp, album):
    alternatives = [
        ((0, 0, 0), _version('a', 'A')),
        ((0, 0, 0), _version('b', 'B')),
        ((1, 0, 0), _version('c', 'C')),
    ]
    _parent, actions = _actions(qapp, album, alternatives)
    assert [action.text() for action in actions] == ['Tracks / Year', 'A', 'B', '', 'C']
    assert actions[3].isSeparator()
    assert not actions[0].isEnabled()


def test_the_version_of_the_album_is_checked(qapp, album):
    _parent, actions = _actions(qapp, album, [((0, 0, 0), _version('a', 'A')), ((0, 0, 0), _version('b', 'B'))])
    assert [action.isChecked() for action in actions[1:]] == [False, True]


def test_an_ampersand_of_a_name_is_shown_as_it_is(qapp, album):
    # A single & would make the next letter the shortcut key of the item.
    _parent, actions = _actions(qapp, album, [((0, 0, 0), _version('a', 'A&B Records'))])
    assert actions[1].text() == 'A&&B Records'


def test_the_disambiguation_is_the_tooltip(qapp, album):
    _parent, actions = _actions(qapp, album, [((0, 0, 0), _version('a', 'A', extra='Barcode: 123'))])
    assert actions[1].toolTip() == 'Barcode: 123'


def test_choosing_a_version_switches_the_album_to_it(qapp, album):
    _parent, actions = _actions(qapp, album, [((0, 0, 0), _version('a', 'A'))])
    actions[1].trigger()
    album.switch_release_version.assert_called_once()
    # The signal may pass the checked state along; the release ID comes first.
    assert album.switch_release_version.call_args.args[0] == 'a'

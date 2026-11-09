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

from unittest.mock import patch

from PyQt6 import (
    QtCore,
    QtWidgets,
)

import pytest

from picard.ui.options.profiles import ProfilesOptionsPage


KEY = 'list_of_scripts'
SCRIPTS = [(0, 'My script', True, '$noop()')]


@pytest.fixture()
def page(qapp, patch_tagger_instance):
    """Profiles page with one profile holding scripts and an unchecked "Tagger scripts" item."""
    patch_tagger_instance('picard.ui.options')
    page = ProfilesOptionsPage()
    page.current_profile_id = 'p1'
    page.profile_settings = {'p1': {KEY: SCRIPTS}}
    page._get_global_setting = lambda key: []
    group = QtWidgets.QTreeWidgetItem(['Scripting'])
    item = QtWidgets.QTreeWidgetItem(['Tagger scripts'])
    item.setData(page.TREEWIDGETITEM_COLUMN, QtCore.Qt.ItemDataRole.UserRole, KEY)
    item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
    item.setCheckState(page.TREEWIDGETITEM_COLUMN, QtCore.Qt.CheckState.Unchecked)
    group.addChild(item)
    page.ui.settings_tree.addTopLevelItem(group)
    page.tagger_scripts_item = item
    return page


def test_declined_prompt_rechecks_item_without_signal(page):
    """PICARD-3469: declining restores the check mark without emitting itemChanged."""
    changed = []
    page.ui.settings_tree.itemChanged.connect(lambda *args: changed.append(args))
    no = QtWidgets.QMessageBox.StandardButton.No
    with patch.object(QtWidgets.QMessageBox, 'question', return_value=no):
        page.update_values_in_profile_options()
    state = page.tagger_scripts_item.checkState(page.TREEWIDGETITEM_COLUMN)
    assert state == QtCore.Qt.CheckState.Checked
    assert changed == []
    assert page.profile_settings['p1'][KEY] == SCRIPTS


def test_confirmed_prompt_removes_scripts_and_keeps_item_unchecked(page):
    yes = QtWidgets.QMessageBox.StandardButton.Yes
    with patch.object(QtWidgets.QMessageBox, 'question', return_value=yes):
        page.update_values_in_profile_options()
    state = page.tagger_scripts_item.checkState(page.TREEWIDGETITEM_COLUMN)
    assert state == QtCore.Qt.CheckState.Unchecked
    assert KEY not in page.profile_settings['p1']

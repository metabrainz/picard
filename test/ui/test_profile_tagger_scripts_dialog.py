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


from PyQt6 import QtCore

from test.picardtestcase import PicardTestCase

from picard.ui.profile_tagger_scripts_dialog import ProfileTaggerScriptsDialog


class TestProfileTaggerScriptsDialog(PicardTestCase):
    def _make_dialog(self):
        # (position, title, enabled, content)
        scripts = [
            (0, "Enabled A", True, "$set(a,b)"),
            (1, "Disabled B", False, "$noop()"),
            (2, "Enabled C", True, "$set(c,d)"),
        ]
        return ProfileTaggerScriptsDialog("Shared", scripts)

    def test_precheck_follows_enabled_flag(self):
        dialog = self._make_dialog()
        # Scripts authored as enabled are pre-checked and thus selected.
        self.assertEqual(dialog.selected_positions(), {0, 2})

    def test_uncheck_updates_selection(self):
        dialog = self._make_dialog()
        # Uncheck the first item (position 0).
        item = dialog._list.item(0)
        item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.assertEqual(dialog.selected_positions(), {2})

    def test_check_disabled_updates_selection(self):
        dialog = self._make_dialog()
        # Enable the disabled item (position 1).
        item = dialog._list.item(1)
        item.setCheckState(QtCore.Qt.CheckState.Checked)
        self.assertEqual(dialog.selected_positions(), {0, 1, 2})

    def test_position_stored_in_item_data(self):
        dialog = self._make_dialog()
        positions = [dialog._list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(dialog._list.count())]
        self.assertEqual(positions, [0, 1, 2])

    def test_ok_button_enabled_when_any_checked(self):
        dialog = self._make_dialog()
        # Two scripts start checked, so OK is enabled.
        self.assertTrue(dialog._ok_button.isEnabled())

    def test_ok_button_disabled_when_none_checked(self):
        dialog = self._make_dialog()
        for i in range(dialog._list.count()):
            dialog._list.item(i).setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.assertFalse(dialog._ok_button.isEnabled())

    def test_ok_button_reenabled_after_recheck(self):
        dialog = self._make_dialog()
        for i in range(dialog._list.count()):
            dialog._list.item(i).setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.assertFalse(dialog._ok_button.isEnabled())
        dialog._list.item(0).setCheckState(QtCore.Qt.CheckState.Checked)
        self.assertTrue(dialog._ok_button.isEnabled())

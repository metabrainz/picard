# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from pathlib import Path
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.plugin3.plugin import Plugin


class TestPluginRefItem(PicardTestCase):
    def test_plugin_ref_item_initialization(self):
        """Test that Plugin.ref_item is initialized to None."""
        plugin = Plugin(Path("/tmp"), "test-plugin")
        self.assertIsNone(plugin.ref_item)

    def test_sync_ref_item_from_git_no_git_dir(self):
        """Test sync_ref_item_from_git when no git directory exists."""
        plugin = Plugin(Path("/tmp"), "test-plugin")
        plugin.local_path = Path("/nonexistent")

        mock_manager = Mock()
        plugin.sync_ref_item_from_git(mock_manager)

        self.assertIsNone(plugin.ref_item)

    def test_sync_ref_item_from_git_exception(self):
        """Test sync_ref_item_from_git handles exceptions gracefully."""
        plugin = Plugin(Path("/tmp"), "test-plugin")
        plugin.local_path = Path("/tmp")
        plugin.uuid = "test-uuid"

        # Create a fake .git directory
        git_dir = plugin.local_path / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)

        try:
            mock_manager = Mock()
            mock_manager._get_ref_item_from_git_state.side_effect = Exception("Git error")

            plugin.sync_ref_item_from_git(mock_manager)

            self.assertIsNone(plugin.ref_item)
        finally:
            # Clean up
            if git_dir.exists():
                git_dir.rmdir()

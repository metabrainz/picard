# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.plugin3.asyncops.manager import AsyncPluginManager


class TestAsyncopsManager(PicardTestCase):
    def test_async_manager_wraps_sync_manager(self):
        """Test AsyncPluginManager wraps PluginManager."""
        mock_manager = Mock()
        mock_manager.plugins = []

        async_manager = AsyncPluginManager(mock_manager)
        self.assertEqual(async_manager.plugins, [])

    def test_enable_plugin_synchronous(self):
        """Test enable_plugin is synchronous."""
        mock_manager = Mock()
        mock_plugin = Mock()

        async_manager = AsyncPluginManager(mock_manager)
        async_manager.enable_plugin(mock_plugin)

        mock_manager.enable_plugin.assert_called_once_with(mock_plugin)

    def test_disable_plugin_synchronous(self):
        """Test disable_plugin is synchronous."""
        mock_manager = Mock()
        mock_plugin = Mock()

        async_manager = AsyncPluginManager(mock_manager)
        async_manager.disable_plugin(mock_plugin)

        mock_manager.disable_plugin.assert_called_once_with(mock_plugin)

    def test_find_plugin_synchronous(self):
        """Test find_plugin is synchronous."""
        mock_manager = Mock()
        mock_manager.find_plugin.return_value = 'found_plugin'

        async_manager = AsyncPluginManager(mock_manager)
        result = async_manager.find_plugin('test-id')

        self.assertEqual(result, 'found_plugin')
        mock_manager.find_plugin.assert_called_once_with('test-id')

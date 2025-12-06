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

from picard.plugin3.asyncops.registry import AsyncPluginRegistry


class TestAsyncopsRegistry(PicardTestCase):
    def test_async_registry_wraps_registry(self):
        """Test AsyncPluginRegistry wraps PluginRegistry."""
        mock_registry = Mock()
        mock_registry._registry_data = {'test': 'data'}

        async_registry = AsyncPluginRegistry(mock_registry)
        self.assertEqual(async_registry._registry, mock_registry)

    def test_search_plugins_synchronous(self):
        """Test search_plugins is synchronous."""
        mock_registry = Mock()
        mock_registry.list_plugins.return_value = [{'id': 'test'}]

        async_registry = AsyncPluginRegistry(mock_registry)
        result = async_registry.search_plugins(query='test')

        self.assertEqual(result, [{'id': 'test'}])
        mock_registry.list_plugins.assert_called_once_with(query='test', category=None, trust_level=None)

    def test_fetch_registry_uses_cache(self):
        """Test fetch_registry returns cached data immediately."""
        mock_registry = Mock()
        mock_registry._registry_data = {'cached': 'data'}

        async_registry = AsyncPluginRegistry(mock_registry)

        result_holder = {}

        def callback(result):
            result_holder['result'] = result

        async_registry.fetch_registry(callback, use_cache=True)

        # Should be immediate (no async operation)
        self.assertIn('result', result_holder)
        self.assertTrue(result_holder['result'].success)
        self.assertEqual(result_holder['result'].result, {'cached': 'data'})

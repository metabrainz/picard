# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from functools import partial
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import load_plugin_manifest

from picard.plugin3.api import PluginApi


class TestPluginApiMethods(PicardTestCase):
    def test_register_file_processors(self):
        """Test file processor registration methods."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        def dummy_processor():
            pass

        with patch('picard.plugin3.api.register_file_post_addition_to_track_processor') as mock:
            api.register_file_post_addition_to_track_processor(dummy_processor, priority=5)
            # Should be called with partial(dummy_processor, api)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 5)

        with patch('picard.plugin3.api.register_file_post_removal_from_track_processor') as mock:
            api.register_file_post_removal_from_track_processor(dummy_processor, priority=3)
            # Should be called with partial(dummy_processor, api)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 3)

    def test_register_cover_art_provider(self):
        """Test cover art provider registration."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_provider = Mock()

        with patch('picard.plugin3.api.register_cover_art_provider') as mock:
            api.register_cover_art_provider(mock_provider)
            mock.assert_called_once_with(mock_provider)

    def test_register_format(self):
        """Test file format registration."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_format = Mock()

        with patch('picard.plugin3.api.register_format') as mock:
            api.register_format(mock_format)
            mock.assert_called_once_with(mock_format)

    def test_register_context_menu_actions(self):
        """Test context menu action registration methods."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_action = Mock()

        with patch('picard.plugin3.api.register_cluster_action') as mock:
            api.register_cluster_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

        with patch('picard.plugin3.api.register_clusterlist_action') as mock:
            api.register_clusterlist_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

        with patch('picard.plugin3.api.register_track_action') as mock:
            api.register_track_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

        with patch('picard.plugin3.api.register_file_action') as mock:
            api.register_file_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

    def test_register_options_page(self):
        """Test options page registration."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_page = Mock()

        with patch('picard.plugin3.api.register_options_page') as mock:
            api.register_options_page(mock_page)
            mock.assert_called_once_with(mock_page, api)

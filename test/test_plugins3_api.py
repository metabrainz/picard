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

        with patch('picard.plugin3.api_impl.register_file_post_addition_to_track_processor') as mock:
            api.register_file_post_addition_to_track_processor(dummy_processor, priority=5)
            # Should be called with partial(dummy_processor, api)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 5)

        with patch('picard.plugin3.api_impl.register_file_post_removal_from_track_processor') as mock:
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

        with patch('picard.plugin3.api_impl.register_cover_art_provider') as mock:
            api.register_cover_art_provider(mock_provider)
            self.assertEqual(mock_provider.api, api)
            mock.assert_called_once_with(mock_provider)

    def test_register_format(self):
        """Test file format registration."""
        manifest = load_plugin_manifest('example')
        mock_tagger = Mock()
        api = PluginApi(manifest, mock_tagger)

        mock_format = Mock()

        api.register_format(mock_format)
        mock_tagger.format_registry.register.assert_called_once_with(mock_format)

    def test_manifest(self):
        manifest = load_plugin_manifest('example')
        mock_tagger = Mock()
        api = PluginApi(manifest, mock_tagger)

        self.assertEqual(api.manifest, manifest)
        with self.assertRaises(AttributeError):
            api.manifest = Mock()

    def test_register_context_menu_actions(self):
        """Test context menu action registration methods."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_action = Mock()

        with patch('picard.plugin3.api_impl.register_cluster_action') as mock:
            api.register_cluster_action(mock_action)
            self.assertEqual(mock_action.api, api)
            mock.assert_called_once_with(mock_action)

        with patch('picard.plugin3.api_impl.register_clusterlist_action') as mock:
            api.register_clusterlist_action(mock_action)
            self.assertEqual(mock_action.api, api)
            mock.assert_called_once_with(mock_action)

        with patch('picard.plugin3.api_impl.register_track_action') as mock:
            api.register_track_action(mock_action)
            self.assertEqual(mock_action.api, api)
            mock.assert_called_once_with(mock_action)

        with patch('picard.plugin3.api_impl.register_file_action') as mock:
            api.register_file_action(mock_action)
            self.assertEqual(mock_action.api, api)
            mock.assert_called_once_with(mock_action)

    def test_register_options_page(self):
        """Test options page registration."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_page = Mock()

        with patch('picard.plugin3.api_impl.register_options_page') as mock:
            api.register_options_page(mock_page)
            self.assertEqual(mock_page.api, api)
            mock.assert_called_once_with(mock_page)

    def test_processor_metadata_preserved(self):
        """Test that processor function metadata is preserved after wrapping."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        def my_processor(api, track, metadata):
            """Process track metadata."""
            pass

        with patch('picard.plugin3.api_impl.register_track_metadata_processor') as mock:
            api.register_track_metadata_processor(my_processor)
            # Get the wrapped function that was passed
            wrapped = mock.call_args[0][0]
            # Verify metadata is preserved
            self.assertEqual(wrapped.__name__, 'my_processor')
            self.assertEqual(wrapped.__doc__, 'Process track metadata.')
            self.assertEqual(wrapped.func, my_processor)

    def test_register_cover_art_processor(self):
        """Test options page registration."""
        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_processor = Mock()

        with patch('picard.plugin3.api_impl.register_cover_art_processor') as mock:
            api.register_cover_art_processor(mock_processor)
            self.assertEqual(mock_processor.api, api)
            mock.assert_called_once_with(mock_processor)

    def test_get_plugin_version(self):
        """Test get_plugin_version method."""
        manifest = load_plugin_manifest('example')
        mock_tagger = Mock()
        mock_plugin_manager = Mock()
        mock_tagger.get_plugin_manager.return_value = mock_plugin_manager

        api = PluginApi(manifest, mock_tagger)

        # Test with git metadata
        mock_metadata = Mock()
        mock_plugin_manager._get_plugin_metadata.return_value = mock_metadata
        mock_plugin_manager.get_plugin_git_info.return_value = "v1.0.0 @abc1234"

        result = api.get_plugin_version()
        self.assertEqual(result, "v1.0.0 @abc1234")
        mock_plugin_manager._get_plugin_metadata.assert_called_once_with(manifest.uuid)

        # Test fallback to manifest version
        mock_plugin_manager._get_plugin_metadata.return_value = None
        result = api.get_plugin_version()
        self.assertEqual(result, manifest.version)

        # Test no plugin manager
        mock_tagger.get_plugin_manager.return_value = None
        result = api.get_plugin_version()
        self.assertEqual(result, "Unknown")

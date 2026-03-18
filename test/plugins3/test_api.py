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
import logging
from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from PyQt6.QtCore import QSettings

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    MockTagger,
    load_plugin_manifest,
)

from picard import log
from picard.config import (
    BoolOption,
    ConfigSection,
    IntOption,
    Option,
    TextOption,
    get_config,
)
from picard.plugin3.api import PluginApi


class TestPluginApiMethods(PicardTestCase):
    def _create_api(self):
        return PluginApi(load_plugin_manifest('example'), Mock())

    def test_register_file_processors(self):
        """Test file processor registration methods."""
        api = self._create_api()

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
        api = self._create_api()

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
        api = self._create_api()

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
        api = self._create_api()

        mock_page = Mock()

        with patch('picard.plugin3.api_impl.register_options_page') as mock:
            api.register_options_page(mock_page)
            self.assertEqual(mock_page.api, api)
            mock.assert_called_once_with(mock_page)

    def test_processor_metadata_preserved(self):
        """Test that processor function metadata is preserved after wrapping."""
        api = self._create_api()

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
        api = self._create_api()

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
        self.assertEqual(result, str(manifest.version))

        # Test no plugin manager
        mock_tagger.get_plugin_manager.return_value = None
        result = api.get_plugin_version()
        self.assertEqual(result, "Unknown")


class TestPluginApi(PicardTestCase):
    def _create_api(self):
        return PluginApi(load_plugin_manifest('example'), Mock())

    def tearDown(self):
        # Clear plugin options created during tests from registry
        for key, _v in list(Option.registry.items()):
            if key[0].startswith('plugin.'):
                del Option.registry[key]

    def test_init(self):
        manifest = load_plugin_manifest('example')

        mock_tagger = MockTagger()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)
        self.assertEqual(api.web_service, mock_ws)
        self.assertEqual(api.logger.name, 'main.plugin.example')
        self.assertEqual(api.global_config, get_config())
        self.assertIsInstance(api.plugin_config, ConfigSection)

    def test_api_properties(self):
        """Test PluginApi property accessors."""
        manifest = load_plugin_manifest('example')

        mock_tagger = MockTagger()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)

        # Test property accessors
        self.assertEqual(api.web_service, mock_ws)
        self.assertIsNotNone(api.mb_api)
        self.assertIsNotNone(api.logger)
        self.assertEqual(api.plugin_id, 'example')
        self.assertIsNotNone(api.global_config)
        self.assertIsNotNone(api.plugin_config)

    def test_logger_propagates_to_main(self):
        """Test that plugin logger messages propagate to main logger."""
        # Save and restore logging.disable state (other tests may have disabled logging)
        original_disable_level = logging.root.manager.disable
        logging.disable(logging.NOTSET)

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, MockTagger())

        # Verify logger name is correct
        self.assertEqual(api.logger.name, 'main.plugin.example')

        # Create a real handler that captures messages
        captured_messages = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                captured_messages.append(record)

        handler = CaptureHandler()
        handler.setLevel(logging.DEBUG)

        # Add handler to main logger
        log.main_logger.addHandler(handler)

        try:
            # Set logger levels to ensure messages are processed
            original_main_level = log.main_logger.level
            log.main_logger.setLevel(logging.DEBUG)
            api.logger.setLevel(logging.DEBUG)

            # Log messages at different levels
            api.logger.info("Test info message")
            api.logger.debug("Test debug message")

            # Verify messages were captured
            self.assertGreater(len(captured_messages), 0, "Plugin logger messages should propagate to main logger")
            # Verify the messages are from our plugin logger
            for record in captured_messages:
                self.assertTrue(record.name.startswith('main.plugin.'))
        finally:
            log.main_logger.removeHandler(handler)
            log.main_logger.setLevel(original_main_level)
            logging.disable(original_disable_level)

    def test_plugin_config_persistence(self):
        """Test that plugin config values are saved and can be retrieved."""
        manifest = load_plugin_manifest('example')
        test_uuid = manifest.uuid

        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config_file = Path(f.name)

        try:
            # Create a real QSettings instance
            settings = QSettings(str(config_file), QSettings.Format.IniFormat)

            # Create mock tagger with real config
            mock_tagger = MockTagger()

            # Create API with the test config
            api = PluginApi(manifest, mock_tagger)
            api._api_config._ConfigSection__qt_config = settings

            # Set some config values
            api.plugin_config['test_string'] = 'hello'
            api.plugin_config['test_int'] = 42
            api.plugin_config['test_bool'] = True

            # Force sync to disk
            settings.sync()

            # Verify values were written to QSettings
            self.assertEqual(settings.value(f'plugin.{test_uuid}/test_string'), 'hello')
            self.assertEqual(settings.value(f'plugin.{test_uuid}/test_int'), 42)
            self.assertEqual(settings.value(f'plugin.{test_uuid}/test_bool'), True)

            # Create a new settings instance to verify persistence
            settings2 = QSettings(str(config_file), QSettings.Format.IniFormat)

            # Verify values persisted across settings instances
            self.assertEqual(settings2.value(f'plugin.{test_uuid}/test_string'), 'hello')
            self.assertEqual(settings2.value(f'plugin.{test_uuid}/test_int'), 42)
            self.assertEqual(settings2.value(f'plugin.{test_uuid}/test_bool'), True)

            # Verify raw_value can read them back
            api2 = PluginApi(manifest, mock_tagger)
            api2._api_config._ConfigSection__qt_config = settings2
            self.assertEqual(api2.plugin_config.raw_value('test_string'), 'hello')
            self.assertEqual(api2.plugin_config.raw_value('test_int'), 42)
            self.assertEqual(api2.plugin_config.raw_value('test_bool'), True)

        finally:
            config_file.unlink(missing_ok=True)

    def test_plugin_config_operations(self):
        """Test all plugin_config operations."""
        manifest = load_plugin_manifest('example')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config_file = Path(f.name)

        try:
            settings = QSettings(str(config_file), QSettings.Format.IniFormat)
            mock_tagger = MockTagger()
            api = PluginApi(manifest, mock_tagger)
            api._api_config._ConfigSection__qt_config = settings

            # Test registering options
            api.plugin_config.register_option('string', 'default')
            api.plugin_config.register_option('int', 1)
            api.plugin_config.register_option('float', 1.0)
            api.plugin_config.register_option('bool', False)
            api.plugin_config.register_option('list', [])
            api.plugin_config.register_option('dict', {})

            # Test reading default values
            self.assertEqual(api.plugin_config['string'], 'default')
            self.assertEqual(api.plugin_config['int'], 1)
            self.assertEqual(api.plugin_config['float'], 1.0)
            self.assertEqual(api.plugin_config['bool'], False)
            self.assertEqual(api.plugin_config['list'], [])
            self.assertEqual(api.plugin_config['dict'], {})

            # Test setting various types
            api.plugin_config['string'] = 'value'
            api.plugin_config['int'] = 42
            api.plugin_config['float'] = 3.14
            api.plugin_config['bool'] = True
            api.plugin_config['list'] = [1, 2, 3]
            api.plugin_config['dict'] = {'key': 'value'}

            # Test __contains__
            self.assertIn('string', api.plugin_config)
            self.assertIn('int', api.plugin_config)
            self.assertNotIn('missing', api.plugin_config)

            # Test reading set values with various types
            self.assertEqual(api.plugin_config['string'], 'value')
            self.assertEqual(api.plugin_config['int'], 42)
            self.assertEqual(api.plugin_config['float'], 3.14)
            self.assertEqual(api.plugin_config['bool'], True)
            self.assertEqual(api.plugin_config['list'], [1, 2, 3])
            self.assertEqual(api.plugin_config['dict'], {'key': 'value'})

            # Test .remove()
            api.plugin_config.remove('string')
            self.assertNotIn('string', api.plugin_config)
            self.assertEqual(api.plugin_config['string'], 'default')

            # Verify persistence of complex types
            settings.sync()
            settings2 = QSettings(str(config_file), QSettings.Format.IniFormat)
            api2 = PluginApi(manifest, mock_tagger)
            api2._api_config._ConfigSection__qt_config = settings2

            self.assertEqual(api2.plugin_config['list'], [1, 2, 3])
            self.assertEqual(api2.plugin_config['dict'], {'key': 'value'})

        finally:
            config_file.unlink(missing_ok=True)

    def test_plugin_config_type_roundtrip(self):
        """Test that common types survive save/load roundtrip in same process."""
        manifest = load_plugin_manifest('example')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config_file = Path(f.name)

        try:
            settings = QSettings(str(config_file), QSettings.Format.IniFormat)
            mock_tagger = MockTagger()
            api = PluginApi(manifest, mock_tagger)
            api._api_config._ConfigSection__qt_config = settings

            # Register options
            api.plugin_config.register_option('bool_true', False)
            api.plugin_config.register_option('bool_false', False)
            api.plugin_config.register_option('int', 0)
            api.plugin_config.register_option('float', 0.0)
            api.plugin_config.register_option('string', "")
            api.plugin_config.register_option('list', [])
            api.plugin_config.register_option('dict', {})

            # Actually write specific values
            api.plugin_config['bool_true'] = True
            api.plugin_config['bool_false'] = False
            api.plugin_config['int'] = 42
            api.plugin_config['float'] = 3.14
            api.plugin_config['string'] = 'hello'
            api.plugin_config['list'] = [1, 2, 3]
            api.plugin_config['dict'] = {'key': 'value'}
            settings.sync()

            # Load in new QSettings instance (same process)
            settings2 = QSettings(str(config_file), QSettings.Format.IniFormat)
            api2 = PluginApi(manifest, mock_tagger)
            api2._api_config._ConfigSection__qt_config = settings2

            # Types are preserved due to QSettings in-memory cache
            self.assertIs(api2.plugin_config['bool_true'], True)
            self.assertIs(api2.plugin_config['bool_false'], False)
            self.assertEqual(api2.plugin_config['int'], 42)
            self.assertIsInstance(api2.plugin_config['int'], int)
            self.assertEqual(api2.plugin_config['float'], 3.14)
            self.assertIsInstance(api2.plugin_config['float'], float)
            self.assertEqual(api2.plugin_config['string'], 'hello')
            self.assertIsInstance(api2.plugin_config['string'], str)
            self.assertEqual(api2.plugin_config['list'], [1, 2, 3])
            self.assertIsInstance(api2.plugin_config['list'], list)
            self.assertEqual(api2.plugin_config['dict'], {'key': 'value'})
            self.assertIsInstance(api2.plugin_config['dict'], dict)

        finally:
            config_file.unlink(missing_ok=True)

    def test_plugin_config_with_options(self):
        """Test that plugin config works with registered Options."""
        manifest = load_plugin_manifest('example')
        test_uuid = manifest.uuid

        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config_file = Path(f.name)

        try:
            # Create a real QSettings instance
            settings = QSettings(str(config_file), QSettings.Format.IniFormat)

            # Create mock tagger
            mock_tagger = MockTagger()

            # Create API
            api = PluginApi(manifest, mock_tagger)
            api._api_config._ConfigSection__qt_config = settings

            # Register options for the plugin
            TextOption(f'plugin.{test_uuid}', 'text_setting', 'default_text')
            IntOption(f'plugin.{test_uuid}', 'int_setting', 42)
            BoolOption(f'plugin.{test_uuid}', 'bool_setting', False)

            # Set values
            api.plugin_config['text_setting'] = 'hello'
            api.plugin_config['int_setting'] = 100
            api.plugin_config['bool_setting'] = True

            # Read back using [] operator (works with registered Options)
            self.assertEqual(api.plugin_config['text_setting'], 'hello')
            self.assertEqual(api.plugin_config['int_setting'], 100)
            self.assertEqual(api.plugin_config['bool_setting'], True)

            # Verify persistence
            settings.sync()
            settings2 = QSettings(str(config_file), QSettings.Format.IniFormat)
            api2 = PluginApi(manifest, mock_tagger)
            api2._api_config._ConfigSection__qt_config = settings2

            # Values should persist and be properly typed
            self.assertEqual(api2.plugin_config['text_setting'], 'hello')
            self.assertEqual(api2.plugin_config['int_setting'], 100)
            self.assertEqual(api2.plugin_config['bool_setting'], True)

        finally:
            # Clean up registered options
            Option.registry.pop((f'plugin.{test_uuid}', 'text_setting'), None)
            Option.registry.pop((f'plugin.{test_uuid}', 'int_setting'), None)
            Option.registry.pop((f'plugin.{test_uuid}', 'bool_setting'), None)
            config_file.unlink(missing_ok=True)

    def test_register_metadata_processors(self):
        """Test metadata processor registration methods."""
        api = self._create_api()

        def dummy_processor():
            pass

        with patch('picard.plugin3.api_impl.register_album_metadata_processor') as mock_album:
            api.register_album_metadata_processor(dummy_processor, priority=5)
            args, kwargs = mock_album.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 5)

        with patch('picard.plugin3.api_impl.register_track_metadata_processor') as mock_track:
            api.register_track_metadata_processor(dummy_processor, priority=10)
            args, kwargs = mock_track.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 10)

    def test_register_event_hooks(self):
        """Test event hook registration methods."""
        api = self._create_api()

        def dummy_hook():
            pass

        with patch('picard.plugin3.api_impl.register_album_post_removal_processor') as mock:
            api.register_album_post_removal_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

        with patch('picard.plugin3.api_impl.register_file_post_load_processor') as mock:
            api.register_file_post_load_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

        with patch('picard.plugin3.api_impl.register_file_post_save_processor') as mock:
            api.register_file_post_save_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

        with patch('picard.plugin3.api_impl.register_file_pre_save_processor') as mock:
            api.register_file_pre_save_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

    def test_register_script_function(self):
        """Test script function registration."""
        api = self._create_api()

        def dummy_func():
            pass

        with patch('picard.plugin3.api_impl.register_script_function') as mock:
            api.register_script_function(
                dummy_func, name='test', eval_args=False, documentation="doc", signature="$test"
            )
            mock.assert_called_once_with(dummy_func, 'test', False, True, "doc", "$test")

    def test_register_actions(self):
        """Test action registration methods."""
        api = self._create_api()

        mock_action = Mock()

        with patch('picard.plugin3.api_impl.register_album_action') as mock:
            api.register_album_action(mock_action)
            mock.assert_called_once_with(mock_action)

        with patch('picard.plugin3.api_impl.register_track_action') as mock:
            api.register_track_action(mock_action)
            mock.assert_called_once_with(mock_action)

        with patch('picard.plugin3.api_impl.register_file_action') as mock:
            api.register_file_action(mock_action)
            mock.assert_called_once_with(mock_action)

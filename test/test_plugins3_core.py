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

from unittest.mock import Mock

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)
from test.test_plugins3_helpers import (
    MockPlugin,
    MockTagger,
    load_plugin_manifest,
)

from picard.config import (
    ConfigSection,
    Option,
    get_config,
)
from picard.plugin3.api import PluginApi
from picard.version import Version


class TestPluginManifest(PicardTestCase):
    def test_load_from_toml(self):
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.module_name, 'example')
        self.assertEqual(manifest.name(), 'Example plugin')
        self.assertEqual(manifest.authors, ('Philipp Wolfer',))
        self.assertEqual(manifest.description(), "This is an example plugin")
        self.assertEqual(manifest.description('en'), "This is an example plugin")
        self.assertEqual(manifest.description('fr'), "Ceci est un exemple de plugin")
        self.assertEqual(manifest.description('it'), "This is an example plugin")
        self.assertEqual(manifest.version, Version(1, 0, 0))
        self.assertEqual(manifest.api_versions, (Version(3, 0, 0), Version(3, 1, 0)))
        self.assertEqual(manifest.license, 'CC0-1.0')
        self.assertEqual(manifest.license_url, 'https://creativecommons.org/publicdomain/zero/1.0/')

    def test_manifest_missing_translation(self):
        """Test manifest description with missing translation."""
        manifest = load_plugin_manifest('example')

        # Request German translation (exists)
        desc_de = manifest.description('de')
        self.assertEqual(desc_de, "Dies ist ein Beispiel-Plugin")

        # Request non-existent language, should fallback to English
        desc_it = manifest.description('it')
        self.assertEqual(desc_it, "This is an example plugin")

    def test_manifest_name_translation(self):
        """Test manifest name translation."""
        manifest = load_plugin_manifest('example')

        # English (default)
        self.assertEqual(manifest.name('en'), 'Example plugin')

        # German translation
        self.assertEqual(manifest.name('de'), 'Beispiel-Plugin')

        # French translation
        self.assertEqual(manifest.name('fr'), 'Plugin d\'exemple')

        # Non-existent translation falls back to base
        self.assertEqual(manifest.name('it'), 'Example plugin')

    def test_manifest_locale_with_region(self):
        """Test locale with region code (e.g., de_DE) falls back to language (de)."""
        manifest = load_plugin_manifest('example')

        # de_DE should fall back to de
        self.assertEqual(manifest.name('de_DE'), 'Beispiel-Plugin')
        self.assertEqual(manifest.description('de_AT'), "Dies ist ein Beispiel-Plugin")

    def test_manifest_long_description(self):
        """Test long_description field and translation."""
        manifest = load_plugin_manifest('example')

        # English long description
        long_desc = manifest.long_description('en')
        self.assertIn('detailed', long_desc.lower())

        # German long description
        long_desc_de = manifest.long_description('de')
        self.assertIn('ausführlich', long_desc_de.lower())

        # Non-existent translation falls back to English
        long_desc_it = manifest.long_description('it')
        self.assertEqual(long_desc_it, long_desc)

    def test_manifest_validate_valid(self):
        """Test validation of valid manifest."""
        manifest = load_plugin_manifest('example')
        errors = manifest.validate()
        self.assertEqual(errors, [])

    def test_manifest_validate_missing_fields(self):
        """Test validation catches missing required fields."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        # Create minimal invalid manifest
        manifest_content = """
name = "Test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            errors = manifest.validate()
            self.assertGreater(len(errors), 0)
            # Should have errors for missing required fields
            error_text = ' '.join(errors)
            self.assertIn('uuid', error_text)
            self.assertIn('description', error_text)
            self.assertIn('api', error_text)
        finally:
            temp_path.unlink()

    def test_manifest_validate_invalid_types(self):
        """Test validation catches invalid field types."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        manifest_content = """
name = 123
authors = "not an array"
api = "not an array"
version = "1.0.0"
description = "Test"
license = "MIT"
license_url = "https://example.com"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            errors = manifest.validate()
            self.assertGreater(len(errors), 0)
            error_text = ' '.join(errors)
            self.assertIn('name', error_text)
            self.assertIn('authors', error_text)
            self.assertIn('api', error_text)
        finally:
            temp_path.unlink()

    def test_manifest_validate_empty_i18n_sections(self):
        """Test validation warns about empty i18n sections."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        manifest_content = """
name = "Test"
authors = ["Author"]
version = "1.0.0"
description = "Test"
api = ["3.0"]
license = "MIT"
license_url = "https://example.com"

[name_i18n]

[description_i18n]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            errors = manifest.validate()
            self.assertGreater(len(errors), 0)
            error_text = ' '.join(errors)
            self.assertIn('name_i18n', error_text)
            self.assertIn('description_i18n', error_text)
            self.assertIn('empty', error_text.lower())
        finally:
            temp_path.unlink()

    def test_manifest_properties(self):
        """Test manifest property accessors."""
        manifest = load_plugin_manifest('example')

        # Test all properties are accessible
        self.assertIsNotNone(manifest.module_name)
        self.assertIsNotNone(manifest.name())
        self.assertIsNotNone(manifest.authors)
        self.assertIsNotNone(manifest.version)
        self.assertIsNotNone(manifest.api_versions)
        self.assertIsNotNone(manifest.license)
        self.assertIsNotNone(manifest.license_url)

    def test_manifest_invalid_version(self):
        """Test manifest with invalid version string."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "invalid"
description = "Test"
api = ["3.0"]
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            # Should return None for invalid version
            self.assertIsNone(manifest.version)
        finally:
            temp_path.unlink()

    def test_manifest_invalid_api_versions(self):
        """Test manifest with invalid API version strings."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "1.0.0"
description = "Test"
api = ["invalid", "bad"]
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            # Should return empty tuple for invalid versions
            self.assertEqual(manifest.api_versions, tuple())
        finally:
            temp_path.unlink()

    def test_manifest_missing_api_versions(self):
        """Test manifest with missing API versions."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manifest import PluginManifest

        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "1.0.0"
description = "Test"
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(manifest_content)
            temp_path = Path(f.name)

        try:
            with open(temp_path, 'rb') as f:
                manifest = PluginManifest('test', f)

            # Should return empty tuple when api field is missing
            self.assertEqual(manifest.api_versions, tuple())
        finally:
            temp_path.unlink()


class TestPluginApi(PicardTestCase):
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
        import logging

        from picard import log

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
        from pathlib import Path
        import tempfile

        from PyQt6.QtCore import QSettings

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
        from pathlib import Path
        import tempfile

        from PyQt6.QtCore import QSettings

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
        from pathlib import Path
        import tempfile

        from PyQt6.QtCore import QSettings

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
        from pathlib import Path
        import tempfile

        from PyQt6.QtCore import QSettings

        from picard.config import (
            BoolOption,
            IntOption,
            TextOption,
        )

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
            from picard.config import Option

            Option.registry.pop((f'plugin.{test_uuid}', 'text_setting'), None)
            Option.registry.pop((f'plugin.{test_uuid}', 'int_setting'), None)
            Option.registry.pop((f'plugin.{test_uuid}', 'bool_setting'), None)
            config_file.unlink(missing_ok=True)

    def test_register_metadata_processors(self):
        """Test metadata processor registration methods."""
        from functools import partial
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

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
        from functools import partial
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

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
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        def dummy_func():
            pass

        with patch('picard.plugin3.api_impl.register_script_function') as mock:
            api.register_script_function(dummy_func, name='test', eval_args=False)
            mock.assert_called_once_with(dummy_func, 'test', False, True, None)

    def test_register_actions(self):
        """Test action registration methods."""
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

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


class TestPluginManager(PicardTestCase):
    def test_config_persistence(self):
        """Test that enabled plugins are saved to and loaded from config."""
        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Initially no plugins enabled
        self.assertEqual(manager._enabled_plugins, set())

        # Create a mock plugin with UUID
        from test.test_plugins3_helpers import generate_unique_uuid

        test_uuid = generate_unique_uuid()
        mock_plugin = MockPlugin(uuid=test_uuid)

        # Enable plugin - should save to config
        manager.enable_plugin(mock_plugin)
        self.assertIn(test_uuid, manager._enabled_plugins)

        # Verify it was saved to config
        config = get_config()
        self.assertIn('plugins3_enabled_plugins', config.setting)
        self.assertIn(test_uuid, config.setting['plugins3_enabled_plugins'])

        # Create new manager instance - should load from config
        manager2 = PluginManager(mock_tagger)
        self.assertIn(test_uuid, manager2._enabled_plugins)

        # Disable plugin - should remove from config
        manager2.disable_plugin(mock_plugin)
        self.assertNotIn(test_uuid, manager2._enabled_plugins)
        self.assertNotIn(test_uuid, config.setting['plugins3_enabled_plugins'])

    def test_init_plugins_only_loads_enabled(self):
        """Test that init_plugins only loads plugins that are enabled in config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create mock plugins with UUIDs
        enabled_uuid = 'enabled-uuid-1234'
        enabled_plugin = Mock(spec=Plugin)
        enabled_plugin.plugin_id = 'enabled-plugin'
        enabled_plugin.manifest = Mock()
        enabled_plugin.manifest.uuid = enabled_uuid
        enabled_plugin.uuid = enabled_uuid
        enabled_plugin.load_module = Mock()
        enabled_plugin.enable = Mock()

        disabled_uuid = 'disabled-uuid-5678'
        disabled_plugin = Mock(spec=Plugin)
        disabled_plugin.plugin_id = 'disabled-plugin'
        disabled_plugin.manifest = Mock()
        disabled_plugin.manifest.uuid = disabled_uuid
        disabled_plugin.uuid = disabled_uuid
        disabled_plugin.load_module = Mock()
        disabled_plugin.enable = Mock()

        manager._plugins = [enabled_plugin, disabled_plugin]
        manager._enabled_plugins = {enabled_uuid}

        # Initialize plugins
        manager.init_plugins()

        # Only enabled plugin should be loaded
        enabled_plugin.load_module.assert_called_once()
        enabled_plugin.enable.assert_called_once_with(mock_tagger)
        disabled_plugin.load_module.assert_not_called()
        disabled_plugin.enable.assert_not_called()

    def test_api_version_compatibility_compatible(self):
        """Test that plugins with compatible API versions are loaded."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Load compatible plugin (API 3.0, 3.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'example')

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.plugin_id, 'example')
        self.assertEqual(plugin.manifest.name(), 'Example plugin')

    def test_api_version_compatibility_incompatible_old(self):
        """Test that plugins with old incompatible API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Load incompatible plugin (API 2.0, 2.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'incompatible')

        self.assertIsNone(plugin)

    def test_api_version_compatibility_incompatible_new(self):
        """Test that plugins requiring newer API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Load plugin requiring future API (3.5, 3.6)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'newer-api')

        self.assertIsNone(plugin)


class TestPluginErrors(PicardTestCase):
    """Test error handling in plugin system."""

    def test_load_plugin_with_invalid_manifest(self):
        """Test loading plugin with invalid MANIFEST.toml."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Try to load plugin with missing manifest
        plugin = manager._load_plugin(Path('/nonexistent'), 'fake-plugin')
        self.assertIsNone(plugin)

    def test_init_plugins_handles_errors(self):
        """Test that init_plugins handles plugin errors gracefully."""

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Create a plugin that will fail to load
        bad_uuid = 'bad-uuid-1234'
        bad_plugin = Mock(spec=Plugin)
        bad_plugin.plugin_id = 'bad-plugin'
        bad_plugin.manifest = Mock()
        bad_plugin.manifest.uuid = bad_uuid
        bad_plugin.uuid = bad_uuid
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        manager._plugins = [bad_plugin]
        manager._enabled_plugins = {bad_uuid}

        # Should not raise, just log error
        manager.init_plugins()

        # Plugin should have been attempted to load
        bad_plugin.load_module.assert_called_once()

    def test_enable_plugin_with_load_error(self):
        """Test enabling plugin that fails to load."""

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        bad_plugin = Mock(spec=Plugin)
        bad_plugin.plugin_id = 'bad-plugin'
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        with self.assertRaises(Exception):  # noqa: B017
            manager.enable_plugin(bad_plugin)

    def test_manager_add_directory(self):
        """Test adding plugin directory."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Add directory
            manager.add_directory(str(plugin_dir), primary=True)

            # Should be registered
            self.assertIn(plugin_dir, manager._plugin_dirs)
            self.assertEqual(manager._primary_plugin_dir, plugin_dir)

    def test_manager_add_directory_twice(self):
        """Test adding same directory twice is ignored."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Add directory twice
            manager.add_directory(str(plugin_dir))
            initial_count = len(manager._plugin_dirs)

            manager.add_directory(str(plugin_dir))

            # Should not be added twice
            self.assertEqual(len(manager._plugin_dirs), initial_count)

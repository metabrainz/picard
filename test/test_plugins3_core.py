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
    MockTagger,
    load_plugin_manifest,
)

from picard.config import (
    ConfigSection,
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
    def test_init(self):
        manifest = load_plugin_manifest('example')

        mock_tagger = MockTagger()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)
        self.assertEqual(api.web_service, mock_ws)
        self.assertEqual(api.logger.name, 'plugin.example')
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
        self.assertIsNotNone(api.global_config)
        self.assertIsNotNone(api.plugin_config)

    def test_register_metadata_processors(self):
        """Test metadata processor registration methods."""
        from functools import partial
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        def dummy_processor():
            pass

        with patch('picard.plugin3.api.register_album_metadata_processor') as mock_album:
            api.register_album_metadata_processor(dummy_processor, priority=5)
            args, kwargs = mock_album.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_processor)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 5)

        with patch('picard.plugin3.api.register_track_metadata_processor') as mock_track:
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

        with patch('picard.plugin3.api.register_album_post_removal_processor') as mock:
            api.register_album_post_removal_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

        with patch('picard.plugin3.api.register_file_post_load_processor') as mock:
            api.register_file_post_load_processor(dummy_hook)
            args, kwargs = mock.call_args
            self.assertIsInstance(args[0], partial)
            self.assertEqual(args[0].func, dummy_hook)
            self.assertEqual(args[0].args, (api,))
            self.assertEqual(args[1], 0)

        with patch('picard.plugin3.api.register_file_post_save_processor') as mock:
            api.register_file_post_save_processor(dummy_hook)
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

        with patch('picard.plugin3.api.register_script_function') as mock:
            api.register_script_function(dummy_func, name='test', eval_args=False)
            mock.assert_called_once_with(dummy_func, 'test', False, True, None)

    def test_register_actions(self):
        """Test action registration methods."""
        from unittest.mock import patch

        manifest = load_plugin_manifest('example')
        api = PluginApi(manifest, Mock())

        mock_action = Mock()

        with patch('picard.plugin3.api.register_album_action') as mock:
            api.register_album_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

        with patch('picard.plugin3.api.register_track_action') as mock:
            api.register_track_action(mock_action)
            mock.assert_called_once_with(mock_action, api)

        with patch('picard.plugin3.api.register_file_action') as mock:
            api.register_file_action(mock_action)
            mock.assert_called_once_with(mock_action, api)


class TestPluginManager(PicardTestCase):
    def test_config_persistence(self):
        """Test that enabled plugins are saved to and loaded from config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)

        # Initially no plugins enabled
        self.assertEqual(manager._enabled_plugins, set())

        # Create a mock plugin with UUID
        test_uuid = 'test-uuid-1234'
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid

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
        enabled_plugin.load_module = Mock()
        enabled_plugin.enable = Mock()

        disabled_uuid = 'disabled-uuid-5678'
        disabled_plugin = Mock(spec=Plugin)
        disabled_plugin.plugin_id = 'disabled-plugin'
        disabled_plugin.manifest = Mock()
        disabled_plugin.manifest.uuid = disabled_uuid
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

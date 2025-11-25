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

from picard.config import (
    ConfigSection,
    get_config,
)
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.version import Version


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginManifest(PicardTestCase):
    def test_load_from_toml(self):
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.module_name, 'example')
        self.assertEqual(manifest.name, 'Example plugin')
        self.assertEqual(manifest.author, 'Philipp Wolfer')
        self.assertEqual(manifest.description(), "This is an example plugin")
        self.assertEqual(manifest.description('en'), "This is an example plugin")
        self.assertEqual(manifest.description('fr'), "Ceci est un exemple de plugin")
        self.assertEqual(manifest.description('it'), "This is an example plugin")
        self.assertEqual(manifest.version, Version(1, 0, 0))
        self.assertEqual(manifest.api_versions, (Version(3, 0, 0), Version(3, 1, 0)))
        self.assertEqual(manifest.license, 'CC0-1.0')
        self.assertEqual(manifest.license_url, 'https://creativecommons.org/publicdomain/zero/1.0/')
        self.assertEqual(manifest.user_guide_url, 'https://example.com/')

    def test_manifest_missing_translation(self):
        """Test manifest description with missing translation."""
        manifest = load_plugin_manifest('example')

        # Request non-existent language, should fallback to default (English)
        desc = manifest.description('de')
        # Should return English as fallback
        self.assertIsNotNone(desc)
        self.assertIsInstance(desc, str)

    def test_manifest_properties(self):
        """Test manifest property accessors."""
        manifest = load_plugin_manifest('example')

        # Test all properties are accessible
        self.assertIsNotNone(manifest.module_name)
        self.assertIsNotNone(manifest.name)
        self.assertIsNotNone(manifest.author)
        self.assertIsNotNone(manifest.version)
        self.assertIsNotNone(manifest.api_versions)
        self.assertIsNotNone(manifest.license)
        self.assertIsNotNone(manifest.license_url)


class TestPluginApi(PicardTestCase):
    def test_init(self):
        manifest = load_plugin_manifest('example')

        mock_tagger = Mock()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)
        self.assertEqual(api.web_service, mock_ws)
        self.assertEqual(api.logger.name, 'plugin.example')
        self.assertEqual(api.global_config, get_config())
        self.assertIsInstance(api.plugin_config, ConfigSection)

    def test_api_properties(self):
        """Test PluginApi property accessors."""
        manifest = load_plugin_manifest('example')

        mock_tagger = Mock()
        mock_ws = mock_tagger.webservice = Mock()

        api = PluginApi(manifest, mock_tagger)

        # Test property accessors
        self.assertEqual(api.web_service, mock_ws)
        self.assertIsNotNone(api.mb_api)
        self.assertIsNotNone(api.logger)
        self.assertIsNotNone(api.global_config)
        self.assertIsNotNone(api.plugin_config)


class TestPluginManager(PicardTestCase):
    def test_config_persistence(self):
        """Test that enabled plugins are saved to and loaded from config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Initially no plugins enabled
        self.assertEqual(manager._enabled_plugins, set())

        # Create a mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'

        # Enable plugin - should save to config
        manager.enable_plugin(mock_plugin)
        self.assertIn('test-plugin', manager._enabled_plugins)

        # Verify it was saved to config
        config = get_config()
        self.assertIn('plugins3', config.setting)
        self.assertIn('test-plugin', config.setting['plugins3']['enabled_plugins'])

        # Create new manager instance - should load from config
        manager2 = PluginManager(mock_tagger)
        self.assertIn('test-plugin', manager2._enabled_plugins)

        # Disable plugin - should remove from config
        manager2.disable_plugin(mock_plugin)
        self.assertNotIn('test-plugin', manager2._enabled_plugins)
        self.assertNotIn('test-plugin', config.setting['plugins3']['enabled_plugins'])

    def test_init_plugins_only_loads_enabled(self):
        """Test that init_plugins only loads plugins that are enabled in config."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Create mock plugins
        enabled_plugin = Mock(spec=Plugin)
        enabled_plugin.name = 'enabled-plugin'
        enabled_plugin.load_module = Mock()
        enabled_plugin.enable = Mock()

        disabled_plugin = Mock(spec=Plugin)
        disabled_plugin.name = 'disabled-plugin'
        disabled_plugin.load_module = Mock()
        disabled_plugin.enable = Mock()

        manager._plugins = [enabled_plugin, disabled_plugin]
        manager._enabled_plugins = {'enabled-plugin'}

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

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Load compatible plugin (API 3.0, 3.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'example')

        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'example')
        self.assertEqual(plugin.manifest.name, 'Example plugin')

    def test_api_version_compatibility_incompatible_old(self):
        """Test that plugins with old incompatible API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Load incompatible plugin (API 2.0, 2.1)
        plugin = manager._load_plugin(Path(get_test_data_path('testplugins3')), 'incompatible')

        self.assertIsNone(plugin)

    def test_api_version_compatibility_incompatible_new(self):
        """Test that plugins requiring newer API versions are rejected."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
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

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Try to load plugin with missing manifest
        plugin = manager._load_plugin(Path('/nonexistent'), 'fake-plugin')
        self.assertIsNone(plugin)

    def test_init_plugins_handles_errors(self):
        """Test that init_plugins handles plugin errors gracefully."""

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Create a plugin that will fail to load
        bad_plugin = Mock(spec=Plugin)
        bad_plugin.name = 'bad-plugin'
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        manager._plugins = [bad_plugin]
        manager._enabled_plugins = {'bad-plugin'}

        # Should not raise, just log error
        manager.init_plugins()

        # Plugin should have been attempted to load
        bad_plugin.load_module.assert_called_once()

    def test_enable_plugin_with_load_error(self):
        """Test enabling plugin that fails to load."""

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        bad_plugin = Mock(spec=Plugin)
        bad_plugin.name = 'bad-plugin'
        bad_plugin.load_module = Mock(side_effect=Exception('Load failed'))

        with self.assertRaises(Exception):  # noqa: B017
            manager.enable_plugin(bad_plugin)

    def test_manager_add_directory(self):
        """Test adding plugin directory."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
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

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            # Add directory twice
            manager.add_directory(str(plugin_dir))
            initial_count = len(manager._plugin_dirs)

            manager.add_directory(str(plugin_dir))

            # Should not be added twice
            self.assertEqual(len(manager._plugin_dirs), initial_count)

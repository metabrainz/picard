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

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    create_test_registry,
)


class TestPluginRegistry(PicardTestCase):
    def test_registry_blacklist_url(self):
        """Test that blacklisted URLs are detected."""
        registry = create_test_registry()

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/malicious.git')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malware', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/safe.git')
        self.assertFalse(is_blacklisted)

    def test_registry_url_from_parameter(self):
        """Test that registry URL can be set via parameter."""
        from picard.plugin3.registry import PluginRegistry

        custom_url = 'https://custom.example.com/registry.json'
        registry = PluginRegistry(registry_url=custom_url)
        self.assertEqual(registry.registry_url, custom_url)

    def test_registry_url_from_env(self):
        """Test that registry URL can be set via environment variable."""
        import os
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        custom_url = 'https://env.example.com/registry.json'
        with patch.dict(os.environ, {'PICARD_PLUGIN_REGISTRY_URL': custom_url}):
            registry = PluginRegistry()
            self.assertEqual(registry.registry_url, custom_url)

    def test_registry_url_priority(self):
        """Test that parameter takes priority over environment variable."""
        import os
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        param_url = 'https://param.example.com/registry.json'
        env_url = 'https://env.example.com/registry.json'

        with patch.dict(os.environ, {'PICARD_PLUGIN_REGISTRY_URL': env_url}):
            registry = PluginRegistry(registry_url=param_url)
            self.assertEqual(registry.registry_url, param_url)

    def test_registry_url_default(self):
        """Test that default URL is used when no parameter or env var is set."""
        import os
        from unittest.mock import patch

        from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URL
        from picard.plugin3.registry import PluginRegistry

        with patch.dict(os.environ, {}, clear=True):
            registry = PluginRegistry()
            self.assertEqual(registry.registry_url, DEFAULT_PLUGIN_REGISTRY_URL)

    def test_registry_blacklist_pattern(self):
        """Test that blacklisted URL regex patterns are detected."""
        registry = create_test_registry()

        is_blacklisted, reason = registry.is_blacklisted('https://badsite.com/plugin.git')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malicious site', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://goodsite.com/plugin.git')
        self.assertFalse(is_blacklisted)

    def test_registry_blacklist_plugin_id(self):
        """Test that blacklisted plugin UUIDs are detected."""
        registry = create_test_registry()

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'blacklisted-uuid-1234')
        self.assertTrue(is_blacklisted)
        self.assertIn('Security vulnerability', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'different-uuid')
        self.assertFalse(is_blacklisted)

    def test_registry_url_redirect(self):
        """Test that URL redirects work."""
        registry = create_test_registry()

        # Find by current URL
        plugin = registry.find_plugin(url='https://github.com/test/example')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['uuid'], 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

        # Find by old URL (redirect)
        plugin = registry.find_plugin(url='https://github.com/olduser/example')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['uuid'], 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertEqual(plugin['git_url'], 'https://github.com/test/example')

        # Find by another old URL
        plugin = registry.find_plugin(url='https://github.com/olduser/old-name')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['uuid'], 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

    def test_registry_uuid_redirect(self):
        """Test that UUID redirects work."""
        registry = create_test_registry()

        # Find by current UUID
        plugin = registry.find_plugin(uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['uuid'], 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

        # Find by old UUID (redirect)
        plugin = registry.find_plugin(uuid='old-uuid-1234')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['uuid'], 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertEqual(plugin['git_url'], 'https://github.com/test/example')

    def test_update_plugin_follows_redirect(self):
        """Test that update_plugin follows redirects and updates metadata."""
        from pathlib import Path
        import tempfile
        from unittest.mock import Mock, patch

        from picard.plugin3.manager import PluginManager

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir)

            manager = PluginManager()
            manager._primary_plugin_dir = plugin_dir
            manager._registry = create_test_registry()

            # Setup: plugin installed from old URL
            old_url = 'https://github.com/olduser/example'
            new_url = 'https://github.com/test/example'
            old_uuid = 'old-uuid-1234'
            new_uuid = 'ae5ef1ed-0195-4014-a113-6090de7cf8b7'

            # Create mock plugin
            mock_plugin = Mock()
            mock_plugin.name = 'example'
            mock_plugin.local_path = plugin_dir / 'example'
            mock_plugin.manifest = Mock()
            mock_plugin.manifest.version = '1.0.0'
            mock_plugin.manifest.uuid = old_uuid
            mock_plugin.read_manifest = Mock()

            # Mock metadata with old URL and UUID
            with patch.object(manager, '_get_plugin_metadata') as mock_get_meta:
                mock_get_meta.return_value = {'url': old_url, 'uuid': old_uuid, 'ref': 'main', 'commit': 'abc123'}

                with patch.object(manager, '_save_plugin_metadata') as mock_save_meta:
                    with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
                        mock_source = Mock()
                        mock_source.update.return_value = ('abc123', 'def456')
                        mock_source_class.return_value = mock_source

                        # Update plugin
                        manager.update_plugin(mock_plugin)

                        # Verify metadata was saved with NEW URL and UUID
                        mock_save_meta.assert_called_once()
                        call_args = mock_save_meta.call_args[0]
                        metadata = call_args[0]
                        self.assertEqual(metadata.url, new_url)
                        self.assertEqual(metadata.uuid, new_uuid)
                        self.assertEqual(metadata.original_url, old_url)
                        self.assertEqual(metadata.original_uuid, old_uuid)

    def test_install_blocks_blacklisted_url(self):
        """Test that install blocks blacklisted plugins."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            with self.assertRaises(ValueError) as context:
                manager.install_plugin('https://github.com/badactor/malicious-plugin')

            self.assertIn('blacklisted', str(context.exception).lower())
            self.assertIn('malicious code', str(context.exception).lower())

    def test_install_with_force_blacklisted(self):
        """Test that --force-blacklisted bypasses blacklist."""
        from pathlib import Path
        import tempfile
        from unittest.mock import (
            mock_open,
            patch,
        )

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            with patch('picard.plugin3.manager.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.name.return_value = 'Test Plugin'
                        mock_manifest.uuid = 'test-uuid-1234'
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with patch('shutil.move'):
                            # Should not raise with force_blacklisted=True
                            plugin_id = manager.install_plugin(
                                'https://github.com/badactor/malicious-plugin', force_blacklisted=True
                            )
                            self.assertEqual(plugin_id, 'test_plugin_test-uuid-1234')

    def test_check_blacklisted_plugins_on_startup(self):
        """Test that blacklisted plugins are disabled on startup."""
        from pathlib import Path
        from unittest.mock import patch

        from picard.plugin3.manager import PluginManager, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        test_uuid = 'blacklisted-uuid-1234'

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid

        manager._plugins = [mock_plugin]
        manager._enabled_plugins = {'test-plugin'}

        # Store metadata
        manager._save_plugin_metadata(
            PluginMetadata(
                name='test-plugin',
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc123',
                uuid=test_uuid,
            )
        )

        # Check blacklisted plugins (mock QMessageBox to avoid GUI)
        with patch('PyQt6.QtWidgets.QMessageBox'):
            manager._check_blacklisted_plugins()

        # Plugin should be disabled (check by UUID)
        self.assertNotIn(test_uuid, manager._enabled_plugins)

    def test_blacklist_warning_shown(self):
        """Test that user warning is shown for blacklisted plugins."""
        from pathlib import Path
        from unittest.mock import patch

        from picard.plugin3.manager import PluginManager, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        test_uuid = 'malicious-uuid-5678'

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'malicious-plugin'
        mock_plugin.local_path = Path('/tmp/malicious-plugin')
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid

        manager._plugins = [mock_plugin]
        manager._enabled_plugins = {'malicious-plugin'}

        # Store metadata
        manager._save_plugin_metadata(
            PluginMetadata(
                name='malicious-plugin',
                url='https://badsite.com/plugin.git',
                ref='main',
                commit='abc123',
                uuid=test_uuid,
            )
        )

        # Mock QMessageBox to capture warning
        with patch('PyQt6.QtWidgets.QMessageBox') as mock_msgbox:
            manager._check_blacklisted_plugins()

            # Warning should be shown
            mock_msgbox.warning.assert_called_once()
            call_args = mock_msgbox.warning.call_args
            message = call_args[0][2]
            self.assertIn('malicious-plugin', message)
            self.assertIn('blacklisted', message.lower())

        # Plugin should be disabled (check by UUID)
        self.assertNotIn(test_uuid, manager._enabled_plugins)

    def test_registry_fetch_from_url(self):
        """Test fetching registry from URL."""
        from unittest.mock import (
            patch,
        )

        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()

        mock_response_data = b'{"blacklist": []}'

        with patch('picard.plugin3.registry.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read = Mock(return_value=mock_response_data)
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            registry.fetch_registry(use_cache=False)

            self.assertIsNotNone(registry._registry_data)
            self.assertEqual(registry._registry_data['blacklist'], [])

    def test_registry_cache_save_and_load(self):
        """Test registry caching."""
        from pathlib import Path
        import tempfile
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / 'registry_cache.json'

            # Create registry with cache path
            registry = PluginRegistry(cache_path=cache_path)

            mock_response_data = b'{"blacklist": [{"url": "test"}]}'

            with patch('picard.plugin3.registry.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.read = Mock(return_value=mock_response_data)
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response

                # Fetch and save to cache
                registry.fetch_registry(use_cache=False)

                # Verify cache file was created
                self.assertTrue(cache_path.exists())

            # Create new registry instance and load from cache
            registry2 = PluginRegistry(cache_path=cache_path)
            registry2.fetch_registry(use_cache=True)

            # Should have loaded from cache
            self.assertEqual(registry2._registry_data['blacklist'], [{'url': 'test'}])

    def test_registry_fetch_error_fallback(self):
        """Test registry fetch error handling."""
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()

        with patch('picard.plugin3.registry.urlopen', side_effect=Exception('Network error')):
            # Should not raise, just use empty blacklist
            registry.fetch_registry(use_cache=False)

            self.assertIsNotNone(registry._registry_data)
            self.assertEqual(registry._registry_data['blacklist'], [])

    def test_registry_get_trust_level(self):
        """Test getting trust level for plugin by URL."""
        registry = create_test_registry()

        # Test official
        self.assertEqual(registry.get_trust_level('https://github.com/test/example'), 'official')

        # Test trusted
        self.assertEqual(registry.get_trust_level('https://github.com/user/picard-plugin-discogs'), 'trusted')

        # Test community
        self.assertEqual(registry.get_trust_level('https://github.com/community/custom-tagger'), 'community')

        # Test unregistered (not in registry)
        self.assertEqual(registry.get_trust_level('https://github.com/unknown/plugin'), 'unregistered')

    def test_registry_find_plugin(self):
        """Test finding plugin by ID or URL."""
        registry = create_test_registry()

        # Find by ID
        plugin = registry.find_plugin(plugin_id='example-plugin')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['name'], 'Example plugin')

        # Find by URL
        plugin = registry.find_plugin(url='https://github.com/user/picard-plugin-discogs')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin['name'], 'Discogs')

        # Not found
        plugin = registry.find_plugin(plugin_id='nonexistent')
        self.assertIsNone(plugin)

    def test_registry_list_plugins(self):
        """Test listing plugins with filters."""
        registry = create_test_registry()

        # List all
        plugins = registry.list_plugins()
        self.assertEqual(len(plugins), 6)

        # Filter by trust level
        official = registry.list_plugins(trust_level='official')
        self.assertEqual(len(official), 3)
        self.assertIn('example-plugin', [p['id'] for p in official])
        self.assertIn('listenbrainz', [p['id'] for p in official])

        # Filter by category
        metadata = registry.list_plugins(category='metadata')
        self.assertEqual(len(metadata), 4)

        # Filter by both
        official_metadata = registry.list_plugins(category='metadata', trust_level='official')
        self.assertEqual(len(official_metadata), 2)

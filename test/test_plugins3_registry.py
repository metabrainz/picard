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
    MockPlugin,
    MockTagger,
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

        custom_url = 'https://custom.example.com/registry.toml'
        registry = PluginRegistry(registry_url=custom_url)
        self.assertEqual(registry.registry_url, custom_url)

    def test_registry_url_from_env(self):
        """Test that registry URL can be set via environment variable."""
        import os
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        custom_url = 'https://env.example.com/registry.toml'
        with patch.dict(os.environ, {'PICARD_PLUGIN_REGISTRY_URL': custom_url}):
            registry = PluginRegistry()
            self.assertEqual(registry.registry_url, custom_url)

    def test_registry_url_priority(self):
        """Test that parameter takes priority over environment variable."""
        import os
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        param_url = 'https://param.example.com/registry.toml'
        env_url = 'https://env.example.com/registry.toml'

        with patch.dict(os.environ, {'PICARD_PLUGIN_REGISTRY_URL': env_url}):
            registry = PluginRegistry(registry_url=param_url)
            self.assertEqual(registry.registry_url, param_url)

    def test_registry_url_default(self):
        """Test that default URL is used when no parameter or env var is set."""
        import os
        from unittest.mock import patch

        from picard.const.defaults import DEFAULT_PLUGIN_REGISTRY_URLS
        from picard.plugin3.registry import PluginRegistry

        with patch.dict(os.environ, {}, clear=True):
            registry = PluginRegistry()
            self.assertEqual(registry.registry_url, DEFAULT_PLUGIN_REGISTRY_URLS[0])

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
        self.assertEqual(plugin.uuid, 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

        # Find by old URL (redirect)
        plugin = registry.find_plugin(url='https://github.com/olduser/example')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.uuid, 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertEqual(plugin.git_url, 'https://github.com/test/example')

        # Find by another old URL
        plugin = registry.find_plugin(url='https://github.com/olduser/old-name')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.uuid, 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

    def test_registry_uuid_redirect(self):
        """Test that UUID redirects work."""
        registry = create_test_registry()

        # Find by current UUID
        plugin = registry.find_plugin(uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.uuid, 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')

        # Find by old UUID (redirect)
        plugin = registry.find_plugin(uuid='old-uuid-1234')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.uuid, 'ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertEqual(plugin.git_url, 'https://github.com/test/example')

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
            mock_plugin = MockPlugin()
            mock_plugin.plugin_id = 'example'
            mock_plugin.local_path = plugin_dir / 'example'
            mock_plugin.manifest = Mock()
            mock_plugin.manifest.version = '1.0.0'
            mock_plugin.manifest.uuid = old_uuid
            mock_plugin.read_manifest = Mock()

            # Mock metadata with old URL and UUID
            with patch.object(manager._metadata, 'get_plugin_metadata') as mock_get_meta:
                from picard.plugin3.manager import PluginMetadata

                mock_get_meta.return_value = PluginMetadata(url=old_url, uuid=old_uuid, ref='main', commit='abc123')

                with patch.object(manager._metadata, 'check_redirects') as mock_check_redirects:
                    # Simulate redirect: old URL/UUID -> new URL/UUID
                    mock_check_redirects.return_value = (new_url, new_uuid, True)

                    with patch.object(manager._metadata, 'save_plugin_metadata') as mock_save_meta:
                        with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                            mock_source = Mock()
                            mock_source.update.return_value = ('abc123', 'def456')
                            mock_source.ref = 'main'  # Add ref attribute
                            mock_source.resolved_ref_type = 'branch'  # Add ref type
                            mock_source_class.return_value = mock_source

                            with patch('picard.git.ops.GitOperations.check_dirty_working_dir') as mock_check_dirty:
                                mock_check_dirty.return_value = []  # No uncommitted changes

                                with (
                                    patch('picard.plugin3.manager.update.git_backend') as mock_backend_func,
                                    patch('picard.plugin3.plugin.git_backend') as mock_plugin_backend_func,
                                    patch('picard.plugin3.manager.git_backend') as mock_manager_backend_func,
                                ):
                                    mock_backend = Mock()
                                    mock_repo = Mock()
                                    mock_repo.get_commit_date = Mock(return_value=1234567890)
                                    mock_repo.free = Mock()
                                    # Make mock_repo support context manager protocol
                                    mock_repo.__enter__ = Mock(return_value=mock_repo)
                                    mock_repo.__exit__ = Mock(return_value=False)
                                    mock_backend.create_repository = Mock(return_value=mock_repo)
                                    mock_backend_func.return_value = mock_backend
                                    mock_plugin_backend_func.return_value = mock_backend
                                    mock_manager_backend_func.return_value = mock_backend

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

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            from picard.plugin3.manager import PluginBlacklistedError

            with self.assertRaises(PluginBlacklistedError) as context:
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

        from test.test_plugins3_helpers import generate_unique_uuid

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        test_uuid = generate_unique_uuid()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path, **kwargs):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('builtins.open', mock_open(read_data=b'[plugin]\nmodule_name = "test"')):
                    with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                        mock_manifest = Mock()
                        mock_manifest.name.return_value = 'Test Plugin'
                        mock_manifest.uuid = test_uuid
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with patch('shutil.move'):
                            # Should not raise with force_blacklisted=True
                            plugin_id = manager.install_plugin(
                                'https://github.com/badactor/malicious-plugin', force_blacklisted=True
                            )
                            self.assertEqual(plugin_id, f'test_plugin_{test_uuid}')

    def test_check_blacklisted_plugins_on_startup(self):
        """Test that blacklisted plugins are disabled on startup."""
        from pathlib import Path
        from unittest.mock import patch

        from picard.plugin3.manager import PluginManager, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        test_uuid = 'blacklisted-uuid-1234'

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid
        mock_plugin.uuid = test_uuid

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
        """Test that blacklisted plugins are returned for warning display."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager, PluginMetadata
        from picard.plugin3.plugin import Plugin

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        test_uuid = 'malicious-uuid-5678'

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.plugin_id = 'malicious-plugin'
        mock_plugin.local_path = Path('/tmp/malicious-plugin')
        mock_plugin.manifest = Mock()
        mock_plugin.manifest.uuid = test_uuid
        mock_plugin.uuid = test_uuid

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

        # Check blacklisted plugins - should return list of blacklisted plugins
        blacklisted = manager._check_blacklisted_plugins()

        # Should return the blacklisted plugin
        self.assertEqual(len(blacklisted), 1)
        self.assertEqual(blacklisted[0][0], 'malicious-plugin')
        self.assertIn('Malicious site', blacklisted[0][1])

        # Plugin should be disabled (check by UUID)
        self.assertNotIn(test_uuid, manager._enabled_plugins)

    def test_registry_fetch_from_url(self):
        """Test fetching registry from URL."""
        from unittest.mock import (
            patch,
        )

        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry(registry_url='https://test.example.com/registry.toml')

        mock_response_data = b'blacklist = []'

        with patch('picard.plugin3.registry.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read = Mock(return_value=mock_response_data)
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            registry.fetch_registry(use_cache=False)

            self.assertTrue(registry.is_registry_loaded())
            self.assertEqual(registry.get_raw_registry_data()['blacklist'], [])

    def test_registry_cache_save_and_load(self):
        """Test registry caching."""
        import tempfile
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create registry with cache_dir and TOML URL
            registry = PluginRegistry(registry_url='https://test.example.com/registry.toml', cache_dir=tmpdir)

            mock_response_data = b'[[blacklist]]\nurl = "test"'

            with patch('picard.plugin3.registry.urlopen') as mock_urlopen:
                mock_response = Mock()
                mock_response.read = Mock(return_value=mock_response_data)
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                mock_urlopen.return_value = mock_response

                # Fetch and save to cache
                registry.fetch_registry(use_cache=False)

                # Verify cache file was created (with URL-specific hash)
                self.assertTrue(registry.cache_path.exists())

            # Create new registry instance and load from cache
            registry2 = PluginRegistry(registry_url='https://test.example.com/registry.toml', cache_dir=tmpdir)
            registry2.fetch_registry(use_cache=True)

            # Should have loaded from cache
            self.assertEqual(registry2.get_raw_registry_data()['blacklist'], [{'url': 'test'}])

    def test_registry_fetch_error_fallback(self):
        """Test registry fetch error handling."""
        from unittest.mock import patch

        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryFetchError,
        )

        registry = PluginRegistry()

        with patch('picard.plugin3.registry.urlopen', side_effect=Exception('Network error')):
            with patch('time.sleep'):  # Skip retry delays
                # Should raise RegistryFetchError
                with self.assertRaises(RegistryFetchError) as cm:
                    registry.fetch_registry(use_cache=False)

                self.assertIn('Network error', str(cm.exception))
                self.assertIn('https://picard.musicbrainz.org', str(cm.exception))

    def test_registry_parse_error(self):
        """Test registry parse error handling."""
        from unittest.mock import patch

        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryParseError,
        )

        registry = PluginRegistry()

        with patch('picard.plugin3.registry.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.read = Mock(return_value=b'invalid toml [')
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            # Should raise RegistryParseError
            with self.assertRaises(RegistryParseError) as cm:
                registry.fetch_registry(use_cache=False)

            self.assertIn('Failed to parse registry', str(cm.exception))

    def test_registry_graceful_fallback_on_blacklist_check(self):
        """Test that blacklist check doesn't fail if registry fetch fails."""
        from unittest.mock import patch

        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()

        with patch('picard.plugin3.registry.urlopen', side_effect=Exception('Network error')):
            with patch('time.sleep'):  # Skip retry delays
                # Should not raise, just return False (not blacklisted)
                is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin')

                self.assertFalse(is_blacklisted)
                self.assertIsNone(reason)

    def test_registry_get_registry_info(self):
        """Test getting registry metadata."""
        registry = create_test_registry()

        info = registry.get_registry_info()

        self.assertEqual(info['plugin_count'], 7)
        self.assertEqual(info['api_version'], '3.0')
        self.assertIn('registry_url', info)

    def test_registry_get_registry_info_not_loaded(self):
        """Test get_registry_info raises error when registry not loaded."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()

        with self.assertRaises(RuntimeError) as cm:
            registry.get_registry_info()

        self.assertIn('Registry not loaded', str(cm.exception))

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
        self.assertEqual(plugin.name, 'Example plugin')

        # Find by URL
        plugin = registry.find_plugin(url='https://github.com/user/picard-plugin-discogs')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'Discogs')

        # Not found
        plugin = registry.find_plugin(plugin_id='nonexistent')
        self.assertIsNone(plugin)

    def test_registry_list_plugins(self):
        """Test listing plugins with filters."""
        registry = create_test_registry()

        # List all
        plugins = registry.list_plugins()
        self.assertEqual(len(plugins), 7)

        # Filter by trust level
        official = registry.list_plugins(trust_level='official')
        self.assertEqual(len(official), 3)
        self.assertIn('example-plugin', [p.id for p in official])
        self.assertIn('listenbrainz', [p.id for p in official])

        # Filter by category
        metadata = registry.list_plugins(category='metadata')
        self.assertEqual(len(metadata), 5)

        # Filter by both
        official_metadata = registry.list_plugins(category='metadata', trust_level='official')
        self.assertEqual(len(official_metadata), 2)

    def test_get_registry_id_by_url(self):
        """Test getting registry ID by URL."""
        registry = create_test_registry()

        # Find by URL
        registry_id = registry.get_registry_id(url='https://github.com/test/example')
        self.assertEqual(registry_id, 'example-plugin')

        # Find by different URL
        registry_id = registry.get_registry_id(url='https://github.com/metabrainz/picard-plugin-listenbrainz')
        self.assertEqual(registry_id, 'listenbrainz')

        # Not found
        registry_id = registry.get_registry_id(url='https://github.com/nonexistent/plugin')
        self.assertIsNone(registry_id)

    def test_get_registry_id_by_uuid(self):
        """Test getting registry ID by UUID."""
        registry = create_test_registry()

        # Find by UUID
        registry_id = registry.get_registry_id(uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7')
        self.assertEqual(registry_id, 'example-plugin')

        # Find by different UUID
        registry_id = registry.get_registry_id(uuid='listenbrainz-uuid-5678')
        self.assertEqual(registry_id, 'listenbrainz')

        # Not found
        registry_id = registry.get_registry_id(uuid='nonexistent-uuid')
        self.assertIsNone(registry_id)

    def test_get_registry_id_by_url_and_uuid(self):
        """Test getting registry ID by both URL and UUID."""
        registry = create_test_registry()

        # Find by both (should match)
        registry_id = registry.get_registry_id(
            url='https://github.com/test/example', uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7'
        )
        self.assertEqual(registry_id, 'example-plugin')

        # UUID takes precedence if URL doesn't match
        registry_id = registry.get_registry_id(
            url='https://github.com/wrong/url', uuid='ae5ef1ed-0195-4014-a113-6090de7cf8b7'
        )
        self.assertEqual(registry_id, 'example-plugin')

    def test_ensure_registry_loaded_success(self):
        """Test _ensure_registry_loaded returns True when registry loads successfully."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()
        registry.set_raw_registry_data({'plugins': []})

        # Already loaded
        result = registry._ensure_registry_loaded('test')
        self.assertTrue(result)

    def test_ensure_registry_loaded_failure(self):
        """Test _ensure_registry_loaded returns False when registry fails to load."""
        from unittest.mock import patch

        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryFetchError,
        )

        registry = PluginRegistry()

        # Mock fetch_registry to raise error
        with patch.object(registry, 'fetch_registry', side_effect=RegistryFetchError('test', Exception('error'))):
            result = registry._ensure_registry_loaded('test operation')
            self.assertFalse(result)

    def test_registry_fetch_retry_on_network_error(self):
        """Test that registry fetch retries on network errors."""
        from unittest.mock import MagicMock, patch
        from urllib.error import URLError

        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry(registry_url='https://test.example.com/registry.toml')

        # Mock urlopen to fail twice then succeed
        mock_response = MagicMock()
        mock_response.read.return_value = b'plugins = []'
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        call_count = 0

        def urlopen_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise URLError('Network error')
            return mock_response

        with patch('picard.plugin3.registry.urlopen', side_effect=urlopen_side_effect):
            with patch('picard.plugin3.registry.time.sleep'):  # Skip actual sleep
                registry.fetch_registry()

        self.assertEqual(call_count, 3)
        self.assertEqual(registry.get_raw_registry_data(), {'plugins': []})

    def test_registry_fetch_no_retry_on_client_error(self):
        """Test that registry fetch does not retry on 4xx errors."""
        from unittest.mock import patch
        from urllib.error import HTTPError

        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryFetchError,
        )

        registry = PluginRegistry(registry_url='https://test.example.com/registry.toml')

        # Mock urlopen to return 404
        http_error = HTTPError('https://test.example.com/registry.toml', 404, 'Not Found', {}, None)

        with patch('picard.plugin3.registry.urlopen', side_effect=http_error):
            with patch('time.sleep'):  # Skip retry delays
                with self.assertRaises(RegistryFetchError):
                    registry.fetch_registry()

        # Should only try once (no retries for 4xx)

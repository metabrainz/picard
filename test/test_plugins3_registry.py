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

from picard.plugin3.manifest import PluginManifest


def load_plugin_manifest(plugin_name: str) -> PluginManifest:
    manifest_path = get_test_data_path('testplugins3', plugin_name, 'MANIFEST.toml')
    with open(manifest_path, 'rb') as manifest_file:
        return PluginManifest(plugin_name, manifest_file)


class TestPluginRegistry(PicardTestCase):
    def test_registry_blacklist_url(self):
        """Test that blacklisted URLs are detected."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()
        registry._registry_data = {
            'blacklist': [{'url': 'https://example.com/malicious.git', 'reason': 'Malware detected'}]
        }

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/malicious.git')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malware', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/safe.git')
        self.assertFalse(is_blacklisted)

    def test_registry_blacklist_pattern(self):
        """Test that blacklisted URL patterns are detected."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()
        registry._registry_data = {
            'blacklist': [{'url_pattern': r'https://badsite\.com/.*', 'reason': 'Malicious site'}]
        }

        is_blacklisted, reason = registry.is_blacklisted('https://badsite.com/plugin.git')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malicious site', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://goodsite.com/plugin.git')
        self.assertFalse(is_blacklisted)

    def test_registry_blacklist_plugin_id(self):
        """Test that blacklisted plugin IDs are detected."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()
        registry._registry_data = {'blacklist': [{'plugin_id': 'malicious_plugin', 'reason': 'Security vulnerability'}]}

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'malicious_plugin')
        self.assertTrue(is_blacklisted)
        self.assertIn('Security vulnerability', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'safe_plugin')
        self.assertFalse(is_blacklisted)

    def test_install_blocks_blacklisted_url(self):
        """Test that install blocks blacklisted plugins."""
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginManager

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Mock registry to blacklist URL
            manager._registry._registry_data = {
                'blacklist': [{'url': 'https://example.com/malicious.git', 'reason': 'Malware'}]
            }

            with self.assertRaises(ValueError) as context:
                manager.install_plugin('https://example.com/malicious.git')

            self.assertIn('blacklisted', str(context.exception).lower())
            self.assertIn('Malware', str(context.exception))

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

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Mock registry to blacklist URL
            manager._registry._registry_data = {
                'blacklist': [{'url': 'https://example.com/malicious.git', 'reason': 'Malware'}]
            }

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
                        mock_manifest.module_name = 'test-plugin'
                        mock_manifest.validate.return_value = []
                        mock_manifest_class.return_value = mock_manifest

                        with patch('shutil.move'):
                            # Should not raise with force_blacklisted=True
                            plugin_id = manager.install_plugin(
                                'https://example.com/malicious.git', force_blacklisted=True
                            )
                            self.assertEqual(plugin_id, 'test-plugin')

    def test_check_blacklisted_plugins_on_startup(self):
        """Test that blacklisted plugins are disabled on startup."""
        from pathlib import Path

        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        mock_tagger = Mock()
        manager = PluginManager(mock_tagger)

        # Create mock plugin
        mock_plugin = Mock(spec=Plugin)
        mock_plugin.name = 'test-plugin'
        mock_plugin.local_path = Path('/tmp/test-plugin')

        manager._plugins = [mock_plugin]
        manager._enabled_plugins = {'test-plugin'}

        # Store metadata
        manager._save_plugin_metadata('test-plugin', 'https://example.com/plugin.git', 'main', 'abc123')

        # Mock registry to blacklist the plugin
        manager._registry._registry_data = {
            'blacklist': [{'url': 'https://example.com/plugin.git', 'reason': 'Security issue'}]
        }

        # Check blacklisted plugins
        manager._check_blacklisted_plugins()

        # Plugin should be disabled
        self.assertNotIn('test-plugin', manager._enabled_plugins)

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

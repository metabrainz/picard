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

import json
from pathlib import Path
import tempfile
from unittest.mock import (
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.registry import (
    PluginRegistry,
    get_local_path,
)


class TestRegistryAdvanced(PicardTestCase):
    def test_get_local_path_remote_url(self):
        """Test get_local_path returns None for remote URLs."""
        self.assertIsNone(get_local_path('https://github.com/user/repo.git'))
        self.assertIsNone(get_local_path('git://example.com/repo.git'))

    def test_get_local_path_local_path(self):
        """Test get_local_path converts local paths."""
        result = get_local_path('/tmp/repo')
        self.assertIsInstance(result, Path)
        self.assertEqual(str(result), '/tmp/repo')

    def test_get_local_path_file_protocol(self):
        """Test get_local_path handles file:// protocol."""
        result = get_local_path('file:///tmp/repo')
        self.assertIsInstance(result, Path)
        self.assertIn('tmp', str(result))

    def test_registry_load_cache_error(self):
        """Test registry handles cache load errors gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json{')
            cache_path = f.name

        try:
            with patch('picard.plugin3.registry.urlopen'):
                registry = PluginRegistry(cache_path=cache_path)
                registry.fetch_registry()
                # Should have fetched and created data
                self.assertIsNotNone(registry._registry_data)
        finally:
            Path(cache_path).unlink(missing_ok=True)

    def test_registry_fetch_local_file(self):
        """Test registry can load from local file path."""
        registry_data = {'plugins': [{'id': 'test', 'git_url': 'https://example.com/test.git'}], 'blacklist': []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            registry_file = f.name

        try:
            registry = PluginRegistry(registry_url=registry_file)
            registry.fetch_registry()

            self.assertEqual(len(registry._registry_data['plugins']), 1)
            self.assertEqual(registry._registry_data['plugins'][0]['id'], 'test')
        finally:
            Path(registry_file).unlink(missing_ok=True)

    def test_registry_save_cache_error(self):
        """Test registry handles cache save errors gracefully."""
        registry_data = {'plugins': [], 'blacklist': []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            registry_file = f.name

        try:
            cache_path = tempfile.mktemp(suffix='.json')

            registry = PluginRegistry(registry_url=registry_file, cache_path=cache_path)

            # Patch json.dump after registry is loaded but before cache save
            original_dump = json.dump
            call_count = [0]

            def selective_dump(obj, fp, *args, **kwargs):
                call_count[0] += 1
                # First call is loading registry, second is saving cache
                if call_count[0] == 2:
                    raise IOError('Write failed')
                return original_dump(obj, fp, *args, **kwargs)

            with patch('picard.plugin3.registry.json.dump', side_effect=selective_dump):
                registry.fetch_registry()
                # Should not raise, just log warning
                self.assertIsNotNone(registry._registry_data)
        finally:
            Path(registry_file).unlink(missing_ok=True)
            Path(cache_path).unlink(missing_ok=True)

    def test_blacklist_uuid_and_url(self):
        """Test blacklist with both UUID and URL."""
        registry_data = {
            'plugins': [],
            'blacklist': [{'uuid': 'test-uuid-123', 'url': 'https://example.com/bad.git', 'reason': 'Malicious fork'}],
        }

        registry = PluginRegistry()
        registry._registry_data = registry_data

        # Same UUID and URL - should be blacklisted
        is_blacklisted, reason = registry.is_blacklisted('https://example.com/bad.git', plugin_uuid='test-uuid-123')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malicious fork', reason)

        # Same UUID, different URL - should NOT be blacklisted
        is_blacklisted, _ = registry.is_blacklisted('https://example.com/good.git', plugin_uuid='test-uuid-123')
        self.assertFalse(is_blacklisted)

    def test_blacklist_uuid_only(self):
        """Test blacklist with UUID only (blocks all sources)."""
        registry_data = {'plugins': [], 'blacklist': [{'uuid': 'bad-uuid-456', 'reason': 'Malware'}]}

        registry = PluginRegistry()
        registry._registry_data = registry_data

        # Any URL with this UUID should be blacklisted
        is_blacklisted, reason = registry.is_blacklisted('https://any-url.com/repo.git', plugin_uuid='bad-uuid-456')
        self.assertTrue(is_blacklisted)
        self.assertIn('Malware', reason)

    def test_blacklist_invalid_regex(self):
        """Test blacklist handles invalid regex gracefully."""
        registry_data = {'plugins': [], 'blacklist': [{'url_regex': '[invalid(regex', 'reason': 'Bad pattern'}]}

        registry = PluginRegistry()
        registry._registry_data = registry_data

        # Should not raise, just log warning
        is_blacklisted, _ = registry.is_blacklisted('https://example.com/repo.git')
        self.assertFalse(is_blacklisted)

    def test_registry_fetch_error_fallback(self):
        """Test registry creates empty data on fetch error."""
        with patch('picard.plugin3.registry.urlopen', side_effect=Exception('Network error')):
            registry = PluginRegistry(registry_url='https://invalid.example.com/registry.json')
            registry.fetch_registry()

            # Should have empty blacklist
            self.assertEqual(registry._registry_data, {'blacklist': []})

    def test_list_plugins_empty_registry(self):
        """Test list_plugins with empty registry."""
        registry = PluginRegistry()
        registry._registry_data = {'plugins': []}

        result = registry.list_plugins()
        self.assertEqual(result, [])

    def test_get_trust_level_lazy_load(self):
        """Test get_trust_level fetches registry if not loaded."""
        registry_data = {
            'plugins': [{'git_url': 'https://example.com/test.git', 'trust_level': 'trusted'}],
            'blacklist': [],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            registry_file = f.name

        try:
            registry = PluginRegistry(registry_url=registry_file)
            # Don't call fetch_registry() - let get_trust_level do it
            level = registry.get_trust_level('https://example.com/test.git')
            self.assertEqual(level, 'trusted')
        finally:
            Path(registry_file).unlink(missing_ok=True)

    def test_find_plugin_lazy_load(self):
        """Test find_plugin fetches registry if not loaded."""
        registry_data = {'plugins': [{'id': 'test-plugin', 'git_url': 'https://example.com/test.git'}], 'blacklist': []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            registry_file = f.name

        try:
            registry = PluginRegistry(registry_url=registry_file)
            # Don't call fetch_registry() - let find_plugin do it
            plugin = registry.find_plugin(plugin_id='test-plugin')
            self.assertIsNotNone(plugin)
            self.assertEqual(plugin['id'], 'test-plugin')
        finally:
            Path(registry_file).unlink(missing_ok=True)

    def test_list_plugins_lazy_load(self):
        """Test list_plugins fetches registry if not loaded."""
        registry_data = {'plugins': [{'id': 'test', 'trust_level': 'official'}], 'blacklist': []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(registry_data, f)
            registry_file = f.name

        try:
            registry = PluginRegistry(registry_url=registry_file)
            # Don't call fetch_registry() - let list_plugins do it
            plugins = registry.list_plugins()
            self.assertEqual(len(plugins), 1)
        finally:
            Path(registry_file).unlink(missing_ok=True)

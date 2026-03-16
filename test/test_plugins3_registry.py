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

from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import (
    MockPlugin,
    MockTagger,
    create_test_registry,
)

from picard.plugin3.validator import generate_uuid


def mock_webservice_fetch(response_data, error=None):
    """Helper to mock WebService.get_url for registry fetching.

    Args:
        response_data: TOML data as bytes to return
        error: Optional error to pass to handler
    """

    def get_url_mock(url, handler, **kwargs):
        if error:
            handler(b'', Mock(), error)
        else:
            handler(response_data, Mock(), None)

    return get_url_mock


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

    def test_registry_blacklist_pattern_end_anchor(self):
        """Test that url_regex supports end-of-string anchors via re.search.

        This would fail with re.match which only anchors at the start.
        """
        registry = create_test_registry()

        # Matches: any URL ending with malicious-repo.git
        is_blacklisted, reason = registry.is_blacklisted('https://github.com/user/malicious-repo.git')
        self.assertTrue(is_blacklisted)
        self.assertIn('Blocked repository name', reason)

        # Different host, same repo name — still blocked
        is_blacklisted, reason = registry.is_blacklisted('https://gitlab.com/other/malicious-repo.git')
        self.assertTrue(is_blacklisted)

        # Similar but different name — not blocked
        is_blacklisted, reason = registry.is_blacklisted('https://github.com/user/not-malicious-repo.git')
        self.assertFalse(is_blacklisted)

    def test_registry_blacklist_plugin_id(self):
        """Test that blacklisted plugin UUIDs are detected."""
        registry = create_test_registry()

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'blacklisted-uuid-1234')
        self.assertTrue(is_blacklisted)
        self.assertIn('Security vulnerability', reason)

        is_blacklisted, reason = registry.is_blacklisted('https://example.com/plugin.git', 'different-uuid')
        self.assertFalse(is_blacklisted)

    def test_registry_blacklist_uuid_url_combo(self):
        """Test that UUID+URL combo blacklist entries match only when both match.

        The test registry has a combo entry:
          url = "https://github.com/specific/malware-plugin"
          uuid = "malicious-uuid-5678"

        This should only match when BOTH UUID and URL match, not either alone.
        """
        registry = create_test_registry()

        combo_url = 'https://github.com/specific/malware-plugin'
        combo_uuid = 'malicious-uuid-5678'

        # Both UUID and URL match -> blacklisted
        is_blacklisted, reason = registry.is_blacklisted(combo_url, combo_uuid)
        self.assertTrue(is_blacklisted)
        self.assertIn('malware', reason.lower())

        # Same UUID, different URL -> not matched by combo entry
        is_blacklisted, reason = registry.is_blacklisted('https://goodsite.com/other.git', combo_uuid)
        self.assertFalse(is_blacklisted)

        # Same URL, different UUID -> not matched by combo entry
        is_blacklisted, reason = registry.is_blacklisted(combo_url, 'innocent-uuid')
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
        from unittest.mock import (
            Mock,
            patch,
        )

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

    def test_install_local_blocks_blacklisted_uuid(self):
        """Test that local install blocks plugins with blacklisted UUID.

        Regression test: _install_common() was skipping the UUID blacklist
        check for local installs (is_local=True), allowing locally cloned
        copies of UUID-blacklisted plugins to be installed.
        """
        from pathlib import Path
        import tempfile

        from picard.plugin3.manager import PluginBlacklistedError, PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()

        with tempfile.TemporaryDirectory() as tmpdir:
            manager._primary_plugin_dir = Path(tmpdir)

            # Create a fake local plugin directory with .git
            local_plugin = Path(tmpdir) / 'local-plugin'
            local_plugin.mkdir()
            (local_plugin / '.git').mkdir()

            with patch('picard.plugin3.manager.install.PluginSourceGit') as mock_source_class:
                mock_source = Mock()
                mock_source.ref = 'main'

                def fake_sync(path, **kwargs):
                    path.mkdir(parents=True, exist_ok=True)
                    (path / 'MANIFEST.toml').touch()
                    return 'abc123'

                mock_source.sync = fake_sync
                mock_source_class.return_value = mock_source

                with patch('picard.plugin3.manifest.PluginManifest') as mock_manifest_class:
                    mock_manifest = Mock()
                    mock_manifest.name.return_value = 'Malicious Plugin'
                    mock_manifest.uuid = 'blacklisted-uuid-1234'
                    mock_manifest.validate.return_value = []
                    mock_manifest_class.return_value = mock_manifest

                    with self.assertRaises(PluginBlacklistedError):
                        manager.install_plugin(str(local_plugin))

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

        from picard.plugin3.manager import PluginManager

        mock_tagger = MockTagger()
        manager = PluginManager(mock_tagger)
        manager._registry = create_test_registry()
        test_uuid = generate_uuid()

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
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry(registry_url='https://test.example.com/registry.toml')

        mock_response_data = b'blacklist = []'

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()
        mock_tagger.webservice.get_url = mock_webservice_fetch(mock_response_data)

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertTrue(result['success'])
            self.assertIsNone(result['error'])
            self.assertTrue(registry.is_registry_loaded())
            self.assertEqual(registry.get_raw_registry_data()['blacklist'], [])

    def test_registry_cache_save_and_load(self):
        """Test registry caching."""
        import tempfile

        from picard.plugin3.registry import PluginRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create registry with cache_dir and TOML URL
            registry = PluginRegistry(registry_url='https://test.example.com/registry.toml', cache_dir=tmpdir)

            mock_response_data = b'[[blacklist]]\nurl = "test"'

            mock_tagger = Mock()
            mock_tagger.webservice = Mock()
            mock_tagger.webservice.get_url = mock_webservice_fetch(mock_response_data)

            result = {}

            def callback(success, error):
                result['success'] = success

            with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
                # Fetch and save to cache
                registry.fetch_registry(use_cache=False, callback=callback)

                self.assertTrue(result['success'])
                # Verify cache file was created (with URL-specific hash)
                self.assertTrue(registry.cache_path.exists())

            # Create new registry instance and load from cache
            registry2 = PluginRegistry(registry_url='https://test.example.com/registry.toml', cache_dir=tmpdir)
            registry2.fetch_registry(use_cache=True)

            # Should have loaded from cache
            self.assertEqual(registry2.get_raw_registry_data()['blacklist'], [{'url': 'test'}])

    def test_registry_fetch_error_fallback(self):
        """Test registry fetch error handling."""
        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryFetchError,
        )

        registry = PluginRegistry()

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()
        mock_tagger.webservice.get_url = mock_webservice_fetch(b'', error=Exception('Network error'))

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertFalse(result['success'])
            self.assertIsInstance(result['error'], RegistryFetchError)
            self.assertIn('Network error', str(result['error']))

    def test_registry_parse_error(self):
        """Test registry parse error handling."""
        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryParseError,
        )

        registry = PluginRegistry()

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()
        mock_tagger.webservice.get_url = mock_webservice_fetch(b'invalid toml [')

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertFalse(result['success'])
            self.assertIsInstance(result['error'], RegistryParseError)
            self.assertIn('Failed to parse registry', str(result['error']))

    def test_registry_multiple_url_fallback(self):
        """Test registry tries second URL when first fails."""
        from picard.plugin3.registry import PluginRegistry

        url1 = 'https://first.example.com/registry.toml'
        url2 = 'https://second.example.com/registry.toml'
        registry = PluginRegistry(registry_url=[url1, url2])

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()

        calls = []

        def get_url_mock(url, handler, **kwargs):
            url_str = url.toString()
            calls.append(url_str)
            if url_str == url1:
                handler(b'', Mock(), Exception('First URL failed'))
            else:
                handler(b'plugins = []\nblacklist = []', Mock(), None)

        mock_tagger.webservice.get_url = get_url_mock

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertTrue(result['success'])
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0], url1)
            self.assertEqual(calls[1], url2)
            self.assertTrue(registry.is_registry_loaded())

    def test_registry_all_urls_fail(self):
        """Test registry returns error when all URLs fail."""
        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryFetchError,
        )

        url1 = 'https://first.example.com/registry.toml'
        url2 = 'https://second.example.com/registry.toml'
        registry = PluginRegistry(registry_url=[url1, url2])

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()

        calls = []

        def get_url_mock(url, handler, **kwargs):
            calls.append(url.toString())
            handler(b'', Mock(), Exception('Network error'))

        mock_tagger.webservice.get_url = get_url_mock

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertFalse(result['success'])
            self.assertIsInstance(result['error'], RegistryFetchError)
            self.assertEqual(len(calls), 2)  # Both URLs should be tried
            self.assertFalse(registry.is_registry_loaded())

    def test_registry_parse_error_stops_fallback(self):
        """Test that parse errors don't trigger fallback to next URL."""
        from picard.plugin3.registry import (
            PluginRegistry,
            RegistryParseError,
        )

        url1 = 'https://first.example.com/registry.toml'
        url2 = 'https://second.example.com/registry.toml'
        registry = PluginRegistry(registry_url=[url1, url2])

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()

        calls = []

        def get_url_mock(url, handler, **kwargs):
            calls.append(url.toString())
            # First URL returns invalid TOML
            handler(b'invalid toml [', Mock(), None)

        mock_tagger.webservice.get_url = get_url_mock

        result = {}

        def callback(success, error):
            result['success'] = success
            result['error'] = error

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
            registry.fetch_registry(use_cache=False, callback=callback)

            self.assertFalse(result['success'])
            self.assertIsInstance(result['error'], RegistryParseError)
            self.assertEqual(len(calls), 1)  # Only first URL should be tried
            self.assertFalse(registry.is_registry_loaded())

    def test_ui_dialog_blacklist_check_passes_uuid(self):
        """Test that blacklist check detects UUID-only blacklist entries.

        Regression test: InstallConfirmDialog.check_trust_and_blacklist()
        must pass plugin_uuid to is_blacklisted(), otherwise UUID-only
        blacklist entries are missed.
        """
        registry = create_test_registry()

        # UUID "blacklisted-uuid-1234" is blacklisted in test registry.
        # Using a non-blacklisted URL should still be caught via UUID.
        url = 'https://example.com/innocent-looking-url.git'
        plugin_uuid = 'blacklisted-uuid-1234'

        is_blacklisted, reason = registry.is_blacklisted(url, plugin_uuid)
        self.assertTrue(is_blacklisted, "UUID-only blacklist entry must be detected when UUID is provided")
        self.assertIn('Security vulnerability', reason)

        # Without UUID, this URL should NOT be blacklisted
        is_blacklisted, reason = registry.is_blacklisted(url)
        self.assertFalse(is_blacklisted)

    def test_registry_graceful_fallback_on_blacklist_check(self):
        """Test that blacklist check doesn't fail if registry fetch fails."""
        from picard.plugin3.registry import PluginRegistry

        registry = PluginRegistry()

        mock_tagger = Mock()
        mock_tagger.webservice = Mock()
        mock_tagger.webservice.get_url = mock_webservice_fetch(b'', error=Exception('Network error'))

        with patch('picard.plugin3.registry.QtCore.QCoreApplication.instance', return_value=mock_tagger):
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

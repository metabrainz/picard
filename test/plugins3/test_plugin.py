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

from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from PyQt6.QtCore import (
    QCollator,
    QLocale,
)

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    backend_add_and_commit,
    backend_create_tag,
    backend_init_and_commit,
    create_git_repo_with_backend,
    skip_if_no_git_backend,
)

from picard.git.factory import (
    git_backend,
    has_git_backend,
)
from picard.plugin3.manager import PluginManifestInvalidError
from picard.plugin3.plugin import (
    Plugin,
    PluginAlreadyDisabledError,
    PluginSource,
    PluginSourceGit,
    PluginSourceSyncError,
    PluginState,
)


class TestPluginSync(PicardTestCase):
    def test_plugin_sync_with_source(self):
        """Test Plugin.sync() with a plugin source."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        mock_source = Mock()

        plugin.sync(mock_source)

        mock_source.sync.assert_called_once_with(plugin.local_path)

    def test_plugin_sync_error(self):
        """Test Plugin.sync() raises PluginSourceSyncError on failure."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')
        mock_source = Mock()
        mock_source.sync.side_effect = Exception('Sync failed')

        with self.assertRaises(PluginSourceSyncError):
            plugin.sync(mock_source)

    def test_plugin_sync_without_source(self):
        """Test Plugin.sync() without source does nothing."""
        plugin = Plugin(Path('/tmp'), 'test-plugin')

        # Should not raise and return None
        self.assertIsNone(plugin.sync(None))


class TestPluginManifestReading(PicardTestCase):
    def test_read_manifest_invalid(self):
        """Test Plugin.read_manifest() with invalid manifest."""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('picard.plugin3.plugin.PluginManifest') as mock_manifest_class:
                mock_manifest = Mock()
                mock_manifest.validate.return_value = ['Error 1', 'Error 2']
                mock_manifest_class.return_value = mock_manifest

                plugin = Plugin(Path('/tmp'), 'test-plugin')

                with self.assertRaises(PluginManifestInvalidError) as context:
                    plugin.read_manifest()

                self.assertIn('Invalid MANIFEST.toml', str(context.exception))
                self.assertIn('Error 1', str(context.exception))


class TestPluginSource(PicardTestCase):
    def test_plugin_source_base_not_implemented(self):
        """Test PluginSource.sync() raises NotImplementedError."""
        source = PluginSource()

        with self.assertRaises(NotImplementedError):
            source.sync(Path('/tmp'))


class TestPluginSourceGitInit(PicardTestCase):
    def test_plugin_source_git_init_with_ref(self):
        """Test PluginSourceGit initialization with ref."""
        if not has_git_backend():
            self.skipTest('git backend not available')

        source = PluginSourceGit('https://example.com/repo.git', ref='v1.0')

        self.assertEqual(source.url, 'https://example.com/repo.git')
        self.assertEqual(source.ref, 'v1.0')
        self.assertIsNone(source.resolved_ref)

    def test_plugin_source_git_init_without_ref(self):
        """Test PluginSourceGit initialization without ref."""
        if not has_git_backend():
            self.skipTest('git backend not available')

        source = PluginSourceGit('https://example.com/repo.git')

        self.assertEqual(source.url, 'https://example.com/repo.git')
        self.assertIsNone(source.ref)
        self.assertIsNone(source.resolved_ref)


class TestGitRemoteCallbacks(PicardTestCase):
    def test_git_remote_callbacks_transfer_progress(self):
        """Test GitRemoteCallbacks._transfer_progress() prints progress."""
        if not has_git_backend():
            self.skipTest('git backend not available')

        backend = git_backend()
        callbacks = backend.create_remote_callbacks()
        mock_stats = Mock()
        mock_stats.indexed_objects = 50
        mock_stats.total_objects = 100

        # Progress output is suppressed for cleaner CLI
        with patch('builtins.print') as mock_print:
            callbacks._transfer_progress(mock_stats)
            mock_print.assert_not_called()


class TestPluginSourceGitUpdate(PicardTestCase):
    def test_update_without_ref_uses_head(self):
        """Test update without ref uses HEAD."""
        if not has_git_backend():
            self.skipTest('git backend not available')

        # Create a test git repo
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / 'source'
            backend_init_and_commit(repo_dir, {'file.txt': 'content'}, 'Initial')

            # Clone it
            target = Path(tmpdir) / 'target'
            source = PluginSourceGit(str(repo_dir))
            source.sync(target)

            # Update without specifying ref - should use HEAD
            source_no_ref = PluginSourceGit(str(repo_dir))
            old, new = source_no_ref.update(target)

            # Should return commit IDs (same since no new commits)
            self.assertIsNotNone(old)
            self.assertIsNotNone(new)

    def test_update_with_tag_ref(self):
        """Test update with tag ref falls back to original ref."""
        if not has_git_backend():
            self.skipTest('git backend not available')

        # Create a test git repo with a tag
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / 'source'
            commit = backend_init_and_commit(repo_dir, {'file.txt': 'content'}, 'Initial')

            # Create a tag
            backend_create_tag(repo_dir, 'v1.0', commit, 'Version 1.0')

            # Clone it
            target = Path(tmpdir) / 'target'
            source = PluginSourceGit(str(repo_dir))
            source.sync(target)

            # Update using tag (should fall back to original ref, not try origin/ prefix)
            source_with_tag = PluginSourceGit(str(repo_dir), ref='v1.0')
            old, new = source_with_tag.update(target)

            # Should return commit IDs
            self.assertIsNotNone(old)
            self.assertIsNotNone(new)


class TestPluginGetCurrentCommitId(PicardTestCase):
    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.tmpdir = tempfile.mkdtemp()

    def test_returns_full_commit_id(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        commit_id = create_git_repo_with_backend(repo_path, {'__init__.py': ''})
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        self.assertEqual(plugin.get_current_commit_id(), commit_id)

    def test_returns_short_commit_id(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        commit_id = create_git_repo_with_backend(repo_path, {'__init__.py': ''})
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        result = plugin.get_current_commit_id(short=True)
        self.assertTrue(commit_id.startswith(result))
        self.assertTrue(len(result) < len(commit_id))

    def test_returns_none_no_local_path(self):
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        plugin.local_path = None
        self.assertIsNone(plugin.get_current_commit_id())

    def test_returns_none_no_git_dir(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        repo_path.mkdir()
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        self.assertIsNone(plugin.get_current_commit_id())

    def test_returns_none_on_error(self):
        plugin = Plugin(Path(self.tmpdir), 'nonexistent')
        plugin.local_path = Path(self.tmpdir) / 'nonexistent'
        (plugin.local_path / '.git').mkdir(parents=True)
        self.assertIsNone(plugin.get_current_commit_id())


class TestPluginNameAndStr(PicardTestCase):
    def test_str_returns_plugin_id(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        self.assertEqual(str(plugin), 'my-plugin')

    def test_name_returns_i18n_name(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        plugin.manifest = Mock()
        plugin.manifest.name_i18n.return_value = 'My Plugin'
        self.assertEqual(plugin.name(), 'My Plugin')

    def test_name_falls_back_to_plugin_id(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        plugin.manifest = Mock()
        plugin.manifest.name_i18n.side_effect = Exception('no i18n')
        self.assertEqual(plugin.name(), 'my-plugin')

    def test_lt_compares_by_name(self):
        import picard.i18n

        QLocale.setDefault(QLocale('en'))
        picard.i18n._qcollator = QCollator()

        p1 = Plugin(Path('/tmp'), 'alpha')
        p1.manifest = Mock()
        p1.manifest.name_i18n.return_value = 'Alpha'
        p2 = Plugin(Path('/tmp'), 'beta')
        p2.manifest = Mock()
        p2.manifest.name_i18n.return_value = 'Beta'
        self.assertTrue(p1 < p2)
        self.assertFalse(p2 < p1)


class TestPluginDisable(PicardTestCase):
    def test_disable_already_disabled_raises(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        plugin.state = PluginState.DISABLED
        with self.assertRaises(PluginAlreadyDisabledError):
            plugin.disable()

    def test_disable_calls_module_disable(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        plugin.state = PluginState.ENABLED
        plugin._module = Mock()
        plugin._module.disable = Mock()

        with (
            patch('picard.plugin3.plugin.unregister_module_extensions'),
            patch('picard.plugin3.plugin.PluginApi') as mock_api_cls,
        ):
            mock_api_cls._instances = {}
            plugin.disable()

        plugin._module.disable.assert_called_once()
        self.assertEqual(plugin.state, PluginState.DISABLED)

    def test_disable_cleans_api_instances(self):
        plugin = Plugin(Path('/tmp'), 'my-plugin')
        plugin.state = PluginState.ENABLED
        module = Mock()
        plugin._module = module
        plugin.module_name = 'picard.plugins.my-plugin'

        mock_api = Mock()
        mock_api._plugin_module = module

        with (
            patch('picard.plugin3.plugin.unregister_module_extensions'),
            patch('picard.plugin3.plugin.PluginApi') as mock_api_cls,
        ):
            mock_api_cls._instances = {'picard.plugins.my-plugin': mock_api}
            mock_api_cls._module_cache = {
                'picard.plugins.my-plugin': mock_api,
                'picard.plugins.my-plugin.sub': mock_api,
            }
            plugin.disable()

        mock_api._remove_qt_translator.assert_called_once()
        self.assertNotIn('picard.plugins.my-plugin', mock_api_cls._instances)
        self.assertNotIn('picard.plugins.my-plugin', mock_api_cls._module_cache)
        self.assertNotIn('picard.plugins.my-plugin.sub', mock_api_cls._module_cache)


class TestPluginSourceGitSync(PicardTestCase):
    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.tmpdir = tempfile.mkdtemp()

    def test_sync_existing_repo_fetches(self):
        """Sync into existing repo directory triggers fetch path."""
        repo_path = Path(self.tmpdir) / 'plugin'
        create_git_repo_with_backend(repo_path, {'__init__.py': ''})

        source = PluginSourceGit(str(repo_path), ref='main')
        # Sync into existing repo — should take the fetch path, not clone
        commit_id = source.sync(repo_path)
        self.assertIsNotNone(commit_id)

    def test_sync_resolves_tag_ref(self):
        """Sync with a tag ref resolves to the tagged commit."""
        repo_path = Path(self.tmpdir) / 'source'
        commit_id = backend_init_and_commit(repo_path, {'__init__.py': ''})
        backend_create_tag(repo_path, 'v1.0', commit_id, 'Release')

        target = Path(self.tmpdir) / 'target'
        source = PluginSourceGit(str(repo_path), ref='v1.0')
        result = source.sync(target)
        self.assertEqual(result, commit_id)
        self.assertEqual(source.resolved_ref_type, 'tag')

    def test_sync_no_ref_uses_default_branch(self):
        """Sync without ref uses the default branch."""
        repo_path = Path(self.tmpdir) / 'source'
        commit_id = backend_init_and_commit(repo_path, {'__init__.py': ''})

        target = Path(self.tmpdir) / 'target'
        source = PluginSourceGit(str(repo_path))
        result = source.sync(target)
        self.assertEqual(result, commit_id)
        self.assertEqual(source.resolved_ref, 'main')

    def test_sync_ref_not_found_raises(self):
        """Sync with nonexistent ref raises KeyError."""
        repo_path = Path(self.tmpdir) / 'source'
        backend_init_and_commit(repo_path, {'__init__.py': ''})

        target = Path(self.tmpdir) / 'target'
        source = PluginSourceGit(str(repo_path), ref='nonexistent')
        with self.assertRaises(KeyError):
            source.sync(target)


class TestPluginSourceGitFindLatestTag(PicardTestCase):
    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.tmpdir = tempfile.mkdtemp()

    def _create_tagged_repo(self, tags):
        """Create a repo with multiple tagged commits."""
        repo_path = Path(self.tmpdir) / 'repo'
        commit_id = backend_init_and_commit(repo_path, {'__init__.py': ''})
        for tag in tags:
            (repo_path / '__init__.py').write_text(f'# {tag}')
            commit_id = backend_add_and_commit(repo_path, f'Tag {tag}')
            backend_create_tag(repo_path, tag, commit_id, f'Release {tag}')
        return repo_path

    def test_finds_newer_semver_tag(self):
        repo_path = self._create_tagged_repo(['v1.0.0', 'v2.0.0'])
        source = PluginSourceGit(str(repo_path))
        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            result = source._find_latest_tag(repo, 'v1.0.0')
        self.assertEqual(result, 'v2.0.0')

    def test_returns_none_when_current_is_latest(self):
        repo_path = self._create_tagged_repo(['v1.0.0', 'v2.0.0'])
        source = PluginSourceGit(str(repo_path))
        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            result = source._find_latest_tag(repo, 'v2.0.0')
        self.assertIsNone(result)

    def test_returns_none_for_unparseable_tag(self):
        repo_path = self._create_tagged_repo(['release-candidate'])
        source = PluginSourceGit(str(repo_path))
        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            result = source._find_latest_tag(repo, 'release-candidate')
        self.assertIsNone(result)

    def test_returns_none_for_no_tags(self):
        repo_path = Path(self.tmpdir) / 'repo'
        backend_init_and_commit(repo_path, {'__init__.py': ''})
        source = PluginSourceGit(str(repo_path))
        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            result = source._find_latest_tag(repo, 'v1.0.0')
        self.assertIsNone(result)

    def test_date_based_tags(self):
        repo_path = self._create_tagged_repo(['2024.1.1', '2024.12.30'])
        source = PluginSourceGit(str(repo_path))
        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            result = source._find_latest_tag(repo, '2024.1.1')
        self.assertEqual(result, '2024.12.30')

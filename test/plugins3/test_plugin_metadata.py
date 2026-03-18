# -*- coding: utf-8 -*-

from pathlib import Path
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    backend_create_tag,
    backend_set_detached_head,
    create_git_repo_with_backend,
    skip_if_no_git_backend,
)

from picard.git.backend import (
    GitRef,
    GitRefType,
)
from picard.plugin3.plugin import Plugin
from picard.plugin3.plugin_metadata import (
    PluginMetadata,
    PluginMetadataManager,
)


class TestPluginMetadataToDict(PicardTestCase):
    def test_excludes_none_values(self):
        m = PluginMetadata(url='u', ref='r', commit='c')
        d = m.to_dict()
        self.assertNotIn('uuid', d)
        self.assertNotIn('original_url', d)

    def test_serializes_git_ref(self):
        ref = GitRef(name='refs/tags/v1', target='abc', ref_type=GitRefType.TAG)
        m = PluginMetadata(url='u', ref='r', commit='c', git_ref=ref)
        d = m.to_dict()
        self.assertIn('git_ref_tuple', d)
        self.assertNotIn('git_ref', d)
        self.assertEqual(d['git_ref_tuple'][0], 'refs/tags/v1')


class TestPluginMetadataFromDict(PicardTestCase):
    def test_reconstructs_git_ref_from_tuple(self):
        data = {
            'url': 'u',
            'ref': 'r',
            'commit': 'c',
            'git_ref_tuple': ('refs/heads/main', 'abc', 'branch', False, False),
        }
        m = PluginMetadata.from_dict(data)
        self.assertIsNotNone(m.git_ref)
        self.assertEqual(m.git_ref.name, 'refs/heads/main')
        self.assertEqual(m.git_ref.ref_type, GitRefType.BRANCH)

    def test_ignores_unknown_fields(self):
        data = {'url': 'u', 'ref': 'r', 'commit': 'c', 'unknown_field': 'x'}
        m = PluginMetadata.from_dict(data)
        self.assertEqual(m.url, 'u')


class TestPluginMetadataGetGitRef(PicardTestCase):
    def test_returns_stored_git_ref(self):
        ref = GitRef(name='refs/tags/v1', target='abc')
        m = PluginMetadata(url='', ref='', commit='', git_ref=ref)
        self.assertIs(m.get_git_ref(), ref)

    def test_full_ref_name_passthrough(self):
        m = PluginMetadata(url='', ref='refs/tags/v1.0', commit='abc')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/tags/v1.0')

    def test_short_tag_ref_type(self):
        m = PluginMetadata(url='', ref='v1.0', commit='abc', ref_type='tag')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/tags/v1.0')
        self.assertEqual(result.ref_type, GitRefType.TAG)

    def test_short_branch_ref_type(self):
        m = PluginMetadata(url='', ref='main', commit='abc', ref_type='branch')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/heads/main')
        self.assertEqual(result.ref_type, GitRefType.BRANCH)

    def test_unknown_type_guesses_tag_for_version(self):
        m = PluginMetadata(url='', ref='v2.0', commit='abc')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/tags/v2.0')

    def test_unknown_type_guesses_tag_for_dotted(self):
        m = PluginMetadata(url='', ref='1.2.3', commit='abc')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/tags/1.2.3')

    def test_unknown_type_guesses_branch(self):
        m = PluginMetadata(url='', ref='develop', commit='abc')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'refs/heads/develop')

    def test_commit_only_no_ref(self):
        m = PluginMetadata(url='', ref='', commit='abc123')
        result = m.get_git_ref()
        self.assertEqual(result.name, 'abc123')
        self.assertIsNone(result.ref_type)

    def test_empty_ref_and_commit(self):
        m = PluginMetadata(url='', ref='', commit='')
        result = m.get_git_ref()
        self.assertEqual(result.name, '')
        self.assertEqual(result.target, '')

    def test_ref_type_inferred_from_full_name(self):
        """When ref_type is None but full name starts with refs/heads/."""
        m = PluginMetadata(url='', ref='refs/heads/main', commit='abc')
        result = m.get_git_ref()
        self.assertEqual(result.ref_type, GitRefType.BRANCH)


class TestFindPluginByUrl(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.registry = Mock()
        self.manager = PluginMetadataManager(self.registry)

    @patch('picard.plugin3.plugin_metadata.get_config')
    def test_finds_matching_url(self, mock_config):
        mock_config.return_value.setting = {
            'plugins3_metadata': {
                'uuid1': {'url': 'https://github.com/user/plugin.git', 'ref': 'main', 'commit': 'abc'},
            }
        }
        result = self.manager.find_plugin_by_url('https://github.com/user/plugin.git')
        self.assertIsNotNone(result)
        self.assertEqual(result.ref, 'main')

    @patch('picard.plugin3.plugin_metadata.get_config')
    def test_returns_none_for_empty_url(self, mock_config):
        mock_config.return_value.setting = {'plugins3_metadata': {}}
        result = self.manager.find_plugin_by_url('')
        self.assertIsNone(result)

    @patch('picard.plugin3.plugin_metadata.get_config')
    def test_returns_none_when_no_match(self, mock_config):
        mock_config.return_value.setting = {
            'plugins3_metadata': {
                'uuid1': {'url': 'https://github.com/other/plugin.git', 'ref': 'main', 'commit': 'abc'},
            }
        }
        result = self.manager.find_plugin_by_url('https://github.com/user/plugin.git')
        self.assertIsNone(result)


class TestGetCurrentRefInfo(PicardTestCase):
    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.tmpdir = tempfile.mkdtemp()
        self.registry = Mock()
        self.manager = PluginMetadataManager(self.registry)

    def test_returns_none_for_no_plugin(self):
        ref, commit = self.manager._get_current_ref_info(None)
        self.assertIsNone(ref)
        self.assertIsNone(commit)

    def test_branch_ref(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        create_git_repo_with_backend(repo_path, {'__init__.py': ''})
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        ref, commit = self.manager._get_current_ref_info(plugin)
        self.assertEqual(ref, 'main')
        self.assertIsNotNone(commit)

    def test_tag_ref(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        commit_id = create_git_repo_with_backend(repo_path, {'__init__.py': ''})
        backend_create_tag(repo_path, 'v1.0', commit_id, 'Release')
        backend_set_detached_head(repo_path, commit_id)
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        ref, commit = self.manager._get_current_ref_info(plugin)
        self.assertEqual(ref, 'v1.0')
        self.assertEqual(commit, commit_id)

    def test_detached_head(self):
        repo_path = Path(self.tmpdir) / 'test-plugin'
        commit_id = create_git_repo_with_backend(repo_path, {'__init__.py': ''})
        backend_set_detached_head(repo_path, commit_id)
        plugin = Plugin(Path(self.tmpdir), 'test-plugin')
        ref, commit = self.manager._get_current_ref_info(plugin)
        self.assertEqual(ref, commit_id)
        self.assertEqual(commit, commit_id)

    def test_error_returns_none(self):
        plugin = Plugin(Path(self.tmpdir), 'nonexistent')
        ref, commit = self.manager._get_current_ref_info(plugin)
        self.assertIsNone(ref)
        self.assertIsNone(commit)


class TestGetPluginRefsInfo(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.registry = Mock()
        self.registry.find_plugin.return_value = None
        self.registry.get_registry_id.return_value = None
        self.manager = PluginMetadataManager(self.registry)

    def test_not_found_returns_none(self):
        result = self.manager.get_plugin_refs_info('nonexistent', [])
        self.assertIsNone(result)

    def test_installed_plugin_by_id(self):
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = Mock()
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id') as mock_reg_id,
        ):
            mock_reg_id.return_value = 'reg-id'
            mock_meta.return_value = PluginMetadata(
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc',
                ref_type='branch',
            )
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])

        self.assertIsNotNone(result)
        self.assertEqual(result['url'], 'https://example.com/plugin.git')
        self.assertEqual(result['plugin'], plugin)

    def test_installed_plugin_no_manifest_returns_none(self):
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = None
        plugin.uuid = 'uuid-1'

        with patch.object(self.manager, 'get_plugin_registry_id', return_value=None):
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])
        self.assertIsNone(result)

    def test_installed_plugin_url_from_registry(self):
        """When metadata has no URL, falls back to registry."""
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = Mock()
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        reg_plugin = Mock()
        reg_plugin.git_url = 'https://registry.com/plugin.git'
        reg_plugin.id = 'reg-id'

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id') as mock_reg_id,
        ):
            mock_meta.return_value = PluginMetadata(url='', ref='main', commit='abc')
            mock_reg_id.return_value = 'reg-id'
            self.registry.find_plugin.return_value = reg_plugin
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])

        self.assertEqual(result['url'], 'https://registry.com/plugin.git')

    def test_installed_no_url_no_registry_returns_none(self):
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = Mock()
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id', return_value=None),
        ):
            mock_meta.return_value = PluginMetadata(url='', ref='', commit='')
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])
        self.assertIsNone(result)

    def test_not_installed_by_url(self):
        reg_plugin = Mock()
        reg_plugin.id = 'reg-id'
        self.registry.get_registry_id.return_value = 'reg-id'
        self.registry.find_plugin.return_value = reg_plugin

        result = self.manager.get_plugin_refs_info('https://github.com/user/plugin.git', [])
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], 'https://github.com/user/plugin.git')
        self.assertIsNone(result['plugin'])

    def test_not_installed_by_registry_id(self):
        reg_plugin = Mock()
        reg_plugin.git_url = 'https://example.com/plugin.git'
        reg_plugin.id = 'my-plugin'
        self.registry.find_plugin.return_value = reg_plugin

        result = self.manager.get_plugin_refs_info('my-plugin', [])
        self.assertEqual(result['url'], 'https://example.com/plugin.git')

    def test_not_installed_by_uuid(self):
        reg_plugin = Mock()
        reg_plugin.git_url = 'https://example.com/plugin.git'
        reg_plugin.id = 'my-plugin'
        # First find_plugin(plugin_id=) returns None, second find_plugin(uuid=) returns match
        self.registry.find_plugin.side_effect = [None, reg_plugin, reg_plugin]

        result = self.manager.get_plugin_refs_info('some-uuid', [])
        self.assertEqual(result['url'], 'https://example.com/plugin.git')

    def test_match_by_manifest_name(self):
        plugin = Mock()
        plugin.plugin_id = 'other-id'
        plugin.manifest = Mock()
        plugin.manifest.name.return_value = 'My Plugin'
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id') as mock_reg_id,
        ):
            mock_reg_id.return_value = None
            mock_meta.return_value = PluginMetadata(
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc',
            )
            result = self.manager.get_plugin_refs_info('My Plugin', [plugin])

        self.assertEqual(result['plugin'], plugin)

    def test_match_by_uuid(self):
        plugin = Mock()
        plugin.plugin_id = 'other-id'
        plugin.manifest = Mock()
        plugin.manifest.name.return_value = 'Other'
        plugin.uuid = 'target-uuid'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id') as mock_reg_id,
        ):
            mock_reg_id.return_value = None
            mock_meta.return_value = PluginMetadata(
                url='https://example.com/plugin.git',
                ref='main',
                commit='abc',
            )
            result = self.manager.get_plugin_refs_info('target-uuid', [plugin])

        self.assertEqual(result['plugin'], plugin)

    def test_installed_ref_from_metadata_fallback(self):
        """When _get_current_ref_info returns None, falls back to metadata."""
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = Mock()
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id', return_value=None),
            patch.object(self.manager, '_get_current_ref_info', return_value=(None, None)),
        ):
            mock_meta.return_value = PluginMetadata(
                url='https://example.com/plugin.git',
                ref='v1.0',
                commit='abc',
                ref_type='tag',
            )
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])

        self.assertEqual(result['current_ref'], 'v1.0')
        self.assertEqual(result['current_commit'], 'abc')
        self.assertEqual(result['current_ref_type'], 'tag')

    def test_installed_ref_prefers_metadata_over_detected(self):
        """When both detected and metadata refs exist, metadata ref wins."""
        plugin = Mock()
        plugin.plugin_id = 'my-plugin'
        plugin.manifest = Mock()
        plugin.uuid = 'uuid-1'
        plugin.local_path = None

        with (
            patch.object(self.manager, 'get_plugin_metadata') as mock_meta,
            patch.object(self.manager, 'get_plugin_registry_id', return_value=None),
            patch.object(self.manager, '_get_current_ref_info', return_value=('main', 'abc')),
        ):
            mock_meta.return_value = PluginMetadata(
                url='https://example.com/plugin.git',
                ref='v1.0',
                commit='abc',
                ref_type='tag',
            )
            result = self.manager.get_plugin_refs_info('my-plugin', [plugin])

        self.assertEqual(result['current_ref'], 'v1.0')

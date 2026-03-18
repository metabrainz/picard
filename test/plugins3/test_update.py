# -*- coding: utf-8 -*-

from pathlib import Path
import shutil
import tempfile
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase
from test.plugins3.helpers import (
    MockTagger,
    backend_add_and_commit,
    backend_create_tag,
    backend_set_detached_head,
    create_git_repo_with_backend,
    skip_if_no_git_backend,
)

from picard.git.factory import git_backend
from picard.plugin3.manager import PluginManager
from picard.plugin3.manager.errors import (
    PluginCommitPinnedError,
)
from picard.plugin3.manager.update import (
    PluginUpdater,
    UpdateCheck,
)
from picard.plugin3.plugin import (
    Plugin,
)
from picard.plugin3.plugin_metadata import PluginMetadata
from picard.plugin3.ref_item import RefItem


MANIFEST_TOML = """\
uuid = "test-uuid-1234"
name = "Test Plugin"
authors = ["Test"]
description = "Test"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
version = "{version}"
"""


def _create_plugin_repo(tmpdir, version="1.0.0", plugin_id="test-plugin"):
    """Create a git repo with a valid MANIFEST.toml and return (repo_path, commit_id).

    The repo is created at tmpdir/plugin_id so that Plugin(tmpdir, plugin_id)
    will have local_path pointing to the repo.
    """
    repo_path = Path(tmpdir) / plugin_id
    commit_id = create_git_repo_with_backend(
        repo_path,
        {
            "MANIFEST.toml": MANIFEST_TOML.format(version=version),
            "__init__.py": "",
        },
    )
    return repo_path, commit_id


def _create_updater():
    """Create a PluginUpdater with a real PluginManager."""
    manager = PluginManager(MockTagger())
    return PluginUpdater(manager)


class TestCreateRefItem(PicardTestCase):
    """Test PluginUpdater._create_ref_item()."""

    def setUp(self):
        super().setUp()
        self.updater = _create_updater()

    def test_empty_ref_and_commit(self):
        item = self.updater._create_ref_item(None, None, None)
        self.assertEqual(item.shortname, '')

    def test_tag_ref(self):
        item = self.updater._create_ref_item('v1.0', 'abc123', 'tag')
        self.assertEqual(item.shortname, 'v1.0')
        self.assertEqual(item.ref_type, RefItem.Type.TAG)
        self.assertEqual(item.commit, 'abc123')

    def test_branch_ref(self):
        item = self.updater._create_ref_item('main', 'abc123', 'branch')
        self.assertEqual(item.shortname, 'main')
        self.assertEqual(item.ref_type, RefItem.Type.BRANCH)

    def test_commit_ref(self):
        item = self.updater._create_ref_item(None, 'abc123', 'commit')
        self.assertEqual(item.shortname, 'abc123')
        self.assertEqual(item.ref_type, RefItem.Type.COMMIT)

    def test_none_type_defaults_to_commit(self):
        item = self.updater._create_ref_item('some-ref', 'abc123', None)
        self.assertEqual(item.ref_type, RefItem.Type.COMMIT)
        self.assertEqual(item.shortname, 'abc123')


class TestUpdateAllPlugins(PicardTestCase):
    """Test PluginUpdater.update_all_plugins()."""

    def setUp(self):
        super().setUp()
        self.updater = _create_updater()

    def test_empty_plugin_list(self):
        self.updater.manager._plugins = []
        results = self.updater.update_all_plugins()
        self.assertEqual(results, [])

    def test_commit_pinned_skipped_as_success(self):
        """Commit-pinned plugins should be reported as success with error message."""
        self.updater.update_plugin = Mock(side_effect=PluginCommitPinnedError('test', 'abc123'))
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'
        self.updater.manager._plugins = [plugin]

        results = self.updater.update_all_plugins()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertIsNone(results[0].result)
        self.assertIn('abc123', results[0].error)

    def test_other_error_reported_as_failure(self):
        self.updater.update_plugin = Mock(side_effect=RuntimeError('network error'))
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'
        self.updater.manager._plugins = [plugin]

        results = self.updater.update_all_plugins()

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn('network error', results[0].error)

    def test_successful_update(self):
        mock_result = Mock()
        self.updater.update_plugin = Mock(return_value=mock_result)
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'
        self.updater.manager._plugins = [plugin]

        results = self.updater.update_all_plugins()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].result, mock_result)
        self.assertIsNone(results[0].error)


class TestCheckCommitPinned(PicardTestCase):
    """Test PluginUpdater._check_commit_pinned()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_tag_ref_not_pinned(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(name='test-plugin', url='', ref='v1.0', commit=commit_id, uuid='test-uuid')

        # check_ref_type('v1.0') should find the tag and return 'tag'
        result = self.updater._check_commit_pinned(plugin, metadata)
        self.assertEqual(result, 'tag')

    def test_commit_ref_raises(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        # Metadata ref is a commit hash — check_ref_type resolves it as 'commit'
        metadata = PluginMetadata(name='test-plugin', url='', ref=commit_id, commit=commit_id, uuid='test-uuid')

        with self.assertRaises(PluginCommitPinnedError):
            self.updater._check_commit_pinned(plugin, metadata)

    def test_no_metadata_detached_head_raises(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_set_detached_head(repo_path, commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        # No metadata ref — falls through to check HEAD state
        metadata = PluginMetadata(name='test-plugin', url='', ref='', commit=commit_id, uuid='test-uuid')

        with self.assertRaises(PluginCommitPinnedError):
            self.updater._check_commit_pinned(plugin, metadata)


class TestDetectInstallationType(PicardTestCase):
    """Test PluginUpdater._detect_installation_type()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def _detect(self, plugin, metadata, repo_path, commit_id):
        """Run _detect_installation_type within a repo context."""

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            return self.updater._detect_installation_type(plugin, metadata, repo, commit_id)

    def test_explicit_tag_ref_type(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='v1.0',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='tag',
        )

        # Mock has_versioning to return True
        with patch.object(Plugin, 'has_versioning', return_value=True):
            is_tag, info = self._detect(plugin, metadata, repo_path, commit_id)

        self.assertTrue(is_tag)
        self.assertIn('tag', info)

    def test_explicit_branch_ref_type(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='main',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='branch',
        )

        is_tag, info = self._detect(plugin, metadata, repo_path, commit_id)

        self.assertFalse(is_tag)
        self.assertIn('branch', info)

    def test_unknown_ref_type_resolves_tag(self):
        """When ref_type is None but ref matches a tag, detect as tag."""
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='v1.0',
            commit=commit_id,
            uuid='test-uuid',
            ref_type=None,
        )

        with patch.object(Plugin, 'has_versioning', return_value=True):
            is_tag, info = self._detect(plugin, metadata, repo_path, commit_id)

        self.assertTrue(is_tag)
        self.assertIn('tag', info)

    def test_unknown_ref_type_commit_resolves_to_tag(self):
        """When ref_type is None and ref is a commit that matches a tag."""
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref=commit_id,
            commit=commit_id,
            uuid='test-uuid',
            ref_type=None,
        )

        with patch.object(Plugin, 'has_versioning', return_value=True):
            is_tag, info = self._detect(plugin, metadata, repo_path, commit_id)

        self.assertTrue(is_tag)
        self.assertIn('tag', info)

    def test_tag_without_versioning_falls_back(self):
        """Tag installation without versioning support should not be treated as tag."""
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='v1.0',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='tag',
        )

        with patch.object(Plugin, 'has_versioning', return_value=False):
            is_tag, info = self._detect(plugin, metadata, repo_path, commit_id)

        self.assertFalse(is_tag)


class TestCheckTagUpdates(PicardTestCase):
    """Test PluginUpdater._check_tag_updates()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_non_tag_installation_skips(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(name='test-plugin', url='', ref='main', commit=commit_id, uuid='test-uuid')

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            current_is_tag, current_tag, new_ref = self.updater._check_tag_updates(
                plugin,
                metadata,
                repo,
                commit_id,
                is_tag_installation=False,
                resolved_ref_info="branch main",
                ref='main',
            )

        self.assertFalse(current_is_tag)
        self.assertIsNone(current_tag)
        self.assertIsNone(new_ref)

    def test_tag_installation_finds_current_tag(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(name='test-plugin', url='', ref='v1.0', commit=commit_id, uuid='test-uuid')

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            current_is_tag, current_tag, new_ref = self.updater._check_tag_updates(
                plugin,
                metadata,
                repo,
                commit_id,
                is_tag_installation=True,
                resolved_ref_info="tag v1.0",
                ref='v1.0',
            )

        self.assertTrue(current_is_tag)
        self.assertEqual(current_tag, 'v1.0')
        # No newer tag, so new_ref should be None
        self.assertIsNone(new_ref)

    def test_tag_installation_finds_newer_tag(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir, version="1.0.0")
        backend_create_tag(repo_path, 'v1.0.0', commit_id)

        # Add a new commit with v2.0.0
        (repo_path / "MANIFEST.toml").write_text(MANIFEST_TOML.format(version="2.0.0"))
        commit2 = backend_add_and_commit(repo_path, "v2.0.0")
        backend_create_tag(repo_path, 'v2.0.0', commit2)

        # Go back to v1.0.0
        backend_set_detached_head(repo_path, commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        metadata = PluginMetadata(name='test-plugin', url='', ref='v1.0.0', commit=commit_id, uuid='test-uuid')

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            current_is_tag, current_tag, new_ref = self.updater._check_tag_updates(
                plugin,
                metadata,
                repo,
                commit_id,
                is_tag_installation=True,
                resolved_ref_info="tag v1.0.0",
                ref='v1.0.0',
            )

        self.assertTrue(current_is_tag)
        self.assertEqual(current_tag, 'v1.0.0')
        self.assertEqual(new_ref, 'v2.0.0')


class TestResolveRefToCommit(PicardTestCase):
    """Test PluginUpdater._resolve_ref_to_commit()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_resolve_branch(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            resolved_commit, commit_date = self.updater._resolve_ref_to_commit(repo, 'main')

        self.assertEqual(resolved_commit, commit_id)
        self.assertIsNotNone(commit_date)

    def test_resolve_tag(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)
        backend_create_tag(repo_path, 'v1.0', commit_id)

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            resolved_commit, commit_date = self.updater._resolve_ref_to_commit(repo, 'v1.0')

        self.assertEqual(resolved_commit, commit_id)

    def test_resolve_nonexistent_ref(self):
        repo_path, _ = _create_plugin_repo(self.tmpdir)

        backend = git_backend()
        with backend.create_repository(repo_path) as repo:
            resolved_commit, commit_date = self.updater._resolve_ref_to_commit(repo, 'nonexistent')

        self.assertIsNone(resolved_commit)
        self.assertIsNone(commit_date)


class TestCreateUpdateCheck(PicardTestCase):
    """Test PluginUpdater._create_update_check()."""

    def setUp(self):
        super().setUp()
        self.updater = _create_updater()

    def test_tag_based_update(self):
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'

        result = self.updater._create_update_check(
            plugin,
            current_commit='aaa',
            latest_commit='bbb',
            latest_commit_date=1234567890,
            current_is_tag=True,
            current_tag='v1.0',
            is_detached=False,
            old_ref='v1.0',
            new_ref='v2.0',
        )

        self.assertIsInstance(result, UpdateCheck)
        self.assertEqual(result.old_ref, 'v1.0')
        self.assertEqual(result.new_ref, 'v2.0')
        self.assertEqual(result.old_commit, 'aaa')
        self.assertEqual(result.new_commit, 'bbb')

    def test_detached_head_uses_short_commit(self):
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'

        result = self.updater._create_update_check(
            plugin,
            current_commit='aabbccdd11223344',
            latest_commit='eeff0011',
            latest_commit_date=1234567890,
            current_is_tag=False,
            current_tag=None,
            is_detached=True,
            old_ref='main',
            new_ref=None,
        )

        # Detached head should show short commit IDs
        self.assertEqual(result.old_ref, 'aabbccd')

    def test_branch_based_update(self):
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'

        result = self.updater._create_update_check(
            plugin,
            current_commit='aaa',
            latest_commit='bbb',
            latest_commit_date=1234567890,
            current_is_tag=False,
            current_tag=None,
            is_detached=False,
            old_ref='main',
            new_ref=None,
        )

        self.assertEqual(result.old_ref, 'main')
        self.assertIsNone(result.new_ref)


class TestCheckSinglePluginUpdate(PicardTestCase):
    """Test PluginUpdater._check_single_plugin_update()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_no_update_when_up_to_date(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        plugin._uuid = 'test-uuid'
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='main',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='branch',
        )

        result = self.updater._check_single_plugin_update(plugin, metadata, skip_fetch=True)
        self.assertIsNone(result)

    def test_update_available_on_branch(self):
        """Test that an update is detected when HEAD is behind the tracked ref."""
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        # Create a new commit on main
        (repo_path / "MANIFEST.toml").write_text(MANIFEST_TOML.format(version="2.0.0"))
        commit2 = backend_add_and_commit(repo_path, "Update")

        # Detach HEAD at the old commit to simulate "behind main"
        backend_set_detached_head(repo_path, commit_id)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        plugin._uuid = 'test-uuid'
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='main',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='branch',
        )

        result = self.updater._check_single_plugin_update(plugin, metadata, skip_fetch=True)
        self.assertIsNotNone(result)
        self.assertEqual(result.old_commit, commit_id)
        self.assertEqual(result.new_commit, commit2)

        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='main',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='branch',
        )

        result = self.updater._check_single_plugin_update(plugin, metadata, skip_fetch=True)
        self.assertIsNotNone(result)
        self.assertEqual(result.old_commit, commit_id)

    def test_commit_pinned_returns_none(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        plugin._uuid = 'test-uuid'
        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref=commit_id,
            commit=commit_id,
            uuid='test-uuid',
            ref_type='commit',
        )

        result = self.updater._check_single_plugin_update(plugin, metadata, skip_fetch=True)
        self.assertIsNone(result)

    def test_exception_returns_none(self):
        """Errors during update check should be caught and return None."""
        plugin = Mock()
        plugin.plugin_id = 'test-plugin'
        plugin.uuid = 'test-uuid'
        plugin.local_path = Path('/nonexistent/path')

        metadata = PluginMetadata(
            name='test-plugin',
            url='',
            ref='main',
            commit='abc',
            uuid='test-uuid',
            ref_type='branch',
        )

        result = self.updater._check_single_plugin_update(plugin, metadata, skip_fetch=True)
        self.assertIsNone(result)


class TestCheckUpdates(PicardTestCase):
    """Test PluginUpdater.check_updates()."""

    def setUp(self):
        super().setUp()
        skip_if_no_git_backend()
        self.updater = _create_updater()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_empty_plugin_list(self):
        self.updater.manager._plugins = []
        updates = self.updater.check_updates(skip_fetch=True)
        self.assertEqual(updates, {})

    def test_skips_plugins_without_uuid(self):
        plugin = Mock()
        plugin.uuid = None
        self.updater.manager._plugins = [plugin]

        updates = self.updater.check_updates(skip_fetch=True)
        self.assertEqual(updates, {})

    def test_skips_blacklisted_plugins(self):
        repo_path, commit_id = _create_plugin_repo(self.tmpdir)

        plugin = Plugin(repo_path.parent, 'test-plugin')
        plugin._uuid = 'test-uuid'
        self.updater.manager._plugins = [plugin]

        metadata = PluginMetadata(
            name='test-plugin',
            url='https://example.com/plugin.git',
            ref='main',
            commit=commit_id,
            uuid='test-uuid',
            ref_type='branch',
        )
        self.updater.manager._metadata.save_plugin_metadata(metadata)
        self.updater.manager._registry.is_blacklisted = Mock(return_value=(True, 'security'))

        updates = self.updater.check_updates(skip_fetch=True)
        self.assertEqual(updates, {})

    def test_include_plugins_filter(self):
        plugin1 = Mock()
        plugin1.uuid = 'uuid1'
        plugin1.plugin_id = 'plugin1'
        plugin2 = Mock()
        plugin2.uuid = 'uuid2'
        plugin2.plugin_id = 'plugin2'
        self.updater.manager._plugins = [plugin1, plugin2]

        # Only include plugin1
        self.updater._check_single_plugin_update = Mock(return_value=None)
        self.updater.check_updates(skip_fetch=True, include_plugins=[plugin1])

        # plugin2 should not have been checked
        calls = self.updater._check_single_plugin_update.call_args_list
        plugin_ids = [c[0][0].plugin_id for c in calls]
        self.assertNotIn('plugin2', plugin_ids)

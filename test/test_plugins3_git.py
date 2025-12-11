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

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import MockTagger

import pytest


try:
    from picard.git.factory import has_git_backend

    HAS_GIT_BACKEND = has_git_backend()
except ImportError:
    HAS_GIT_BACKEND = False


class TestCheckRefType(PicardTestCase):
    """Test check_ref_type() function that queries actual git repos."""

    def test_check_ref_type_with_invalid_repo(self):
        """Test check_ref_type with invalid repository path."""
        from picard.plugin3.git_ops import GitOperations

        # Should handle repository errors gracefully
        ref_type, ref_name = GitOperations.check_ref_type(Path('/nonexistent'), 'main')
        self.assertIsNone(ref_type)
        self.assertEqual(ref_name, 'main')


@pytest.mark.skipif(not HAS_GIT_BACKEND, reason="git backend not available")
class TestCheckRefTypeWithRepo(PicardTestCase):
    """Test check_ref_type() with actual git repository."""

    def setUp(self):
        """Create a temporary git repository."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.repo_dir = Path(self.tmpdir) / "test-repo"

        from picard.git.factory import git_backend

        backend = git_backend()
        self.repo = backend.init_repository(self.repo_dir)

        # Create initial commit
        (self.repo_dir / "file.txt").write_text("content")
        self.commit1 = backend.create_commit(self.repo, 'Initial commit')

    def tearDown(self):
        """Clean up temporary directory."""
        import gc
        import shutil

        gc.collect()
        if hasattr(self, 'tmpdir'):
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_check_current_branch(self):
        """Test checking current HEAD on a branch."""
        from picard.plugin3.git_ops import GitOperations

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir)
        self.assertEqual(ref_type, 'branch')
        self.assertEqual(ref_name, 'main')

    def test_check_detached_head_commit(self):
        """Test checking detached HEAD (commit)."""
        from test.test_plugins3_helpers import backend_set_detached_head

        from picard.plugin3.git_ops import GitOperations

        # Checkout specific commit (detached HEAD)
        backend_set_detached_head(self.repo_dir, self.commit1)

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir)
        self.assertEqual(ref_type, 'commit')
        self.assertEqual(ref_name, str(self.commit1)[:7])

    def test_check_tag_ref(self):
        """Test checking if a ref is a tag."""
        from test.test_plugins3_helpers import backend_create_tag

        from picard.plugin3.git_ops import GitOperations

        # Create a tag
        backend_create_tag(self.repo_dir, 'v1.0.0', self.commit1, 'Version 1.0.0')

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir, 'v1.0.0')
        self.assertEqual(ref_type, 'tag')
        self.assertEqual(ref_name, 'v1.0.0')

    def test_check_branch_ref(self):
        """Test checking if a ref is a branch."""
        from test.test_plugins3_helpers import backend_add_and_commit, backend_create_branch

        from picard.plugin3.git_ops import GitOperations

        # Create a dev branch with different content
        (self.repo_dir / "dev.txt").write_text("dev")
        dev_commit = backend_add_and_commit(self.repo_dir, 'Dev')
        backend_create_branch(self.repo_dir, 'dev', dev_commit)

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir, 'dev')
        self.assertEqual(ref_type, 'branch')
        self.assertEqual(ref_name, 'dev')

    def test_check_commit_hash_ref(self):
        """Test checking if a ref is a commit hash."""
        from picard.plugin3.git_ops import GitOperations

        commit_hash = str(self.commit1)
        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir, commit_hash)
        self.assertEqual(ref_type, 'commit')
        self.assertEqual(ref_name, commit_hash)

    def test_check_nonexistent_ref(self):
        """Test checking a ref that doesn't exist."""
        from picard.plugin3.git_ops import GitOperations

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir, 'nonexistent')
        self.assertIsNone(ref_type)
        self.assertEqual(ref_name, 'nonexistent')

    def test_check_lightweight_tag(self):
        """Test checking a lightweight tag (ref to commit, not tag object)."""
        from test.test_plugins3_helpers import backend_create_lightweight_tag

        from picard.plugin3.git_ops import GitOperations

        # Create a lightweight tag (just a reference, no tag object)
        backend_create_lightweight_tag(self.repo_dir, 'lightweight-v1.0', self.commit1)

        ref_type, ref_name = GitOperations.check_ref_type(self.repo_dir, 'lightweight-v1.0')
        self.assertEqual(ref_type, 'tag')
        self.assertEqual(ref_name, 'lightweight-v1.0')


@pytest.mark.skipif(not HAS_GIT_BACKEND, reason="git backend not available")
class TestPluginGitOperations(PicardTestCase):
    """Test git operations for plugin installation and updates."""

    def setUp(self):
        """Create a temporary git repository with a valid plugin."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.tmpdir) / "test-plugin"
        self.plugin_dir.mkdir()

        # Create MANIFEST.toml and __init__.py, then initialize git repo
        manifest_content = """name = "Test Plugin"
authors = ["Test Author"]
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
uuid = "3fa397ec-0f2a-47dd-9223-e47ce9f2d692"
"""

        from test.test_plugins3_helpers import create_git_repo_with_backend

        create_git_repo_with_backend(
            self.plugin_dir,
            {
                'MANIFEST.toml': manifest_content,
                '__init__.py': """
def enable(api):
    pass

def disable():
    pass
""",
            },
        )

    def tearDown(self):
        """Clean up temporary directory."""
        import gc
        import shutil

        # Force garbage collection to release file handles on Windows
        gc.collect()

        if hasattr(self, 'tmpdir'):
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_plugin_source_git_clone(self):
        """Test cloning a git repository."""
        from picard.plugin3.plugin import PluginSourceGit

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir))

            commit_id = source.sync(target)

            self.assertTrue(target.exists())
            self.assertTrue((target / "MANIFEST.toml").exists())
            self.assertTrue((target / "__init__.py").exists())
            self.assertIsNotNone(commit_id)
            self.assertEqual(len(commit_id), 40)  # SHA-1 hash

    def test_plugin_source_git_fetch_existing(self):
        """Test fetching updates to existing repository."""
        from picard.plugin3.plugin import PluginSourceGit

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir))

            # Clone first
            first_commit = source.sync(target)

            # Sync again (should fetch, not clone)
            second_commit = source.sync(target)

            self.assertEqual(first_commit, second_commit)
            self.assertTrue(target.exists())

    def test_plugin_source_git_update(self):
        """Test updating an existing git repository."""
        from picard.plugin3.plugin import PluginSourceGit

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir))

            # Clone first
            old_commit = source.sync(target)

            # Make a new commit in source
            (self.plugin_dir / "newfile.txt").write_text("new content")
            from test.test_plugins3_helpers import backend_add_and_commit

            backend_add_and_commit(self.plugin_dir, 'Add new file')

            # Update - need to use origin/main after clone
            source_with_remote = PluginSourceGit(str(self.plugin_dir), ref='origin/main')
            old, new = source_with_remote.update(target)

            self.assertNotEqual(old, new)
            self.assertEqual(old, old_commit)
            self.assertTrue((target / "newfile.txt").exists())
            self.assertEqual((target / "newfile.txt").read_text(), "new content")

    def test_plugin_source_git_with_branch(self):
        """Test cloning specific branch."""
        # Create a dev branch in source
        from picard.git.factory import git_backend
        from picard.plugin3.plugin import PluginSourceGit

        backend = git_backend()
        repo = backend.create_repository(self.plugin_dir)
        repo.free()

        # Create file on dev branch
        (self.plugin_dir / "dev-feature.txt").write_text("dev only")
        from test.test_plugins3_helpers import backend_add_and_commit, backend_create_branch

        dev_commit = backend_add_and_commit(self.plugin_dir, 'Dev feature')
        backend_create_branch(self.plugin_dir, 'dev', dev_commit)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Clone dev branch
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir), ref='origin/dev')

            commit_id = source.sync(target)

            self.assertEqual(commit_id, str(dev_commit))
            self.assertTrue((target / "dev-feature.txt").exists())

    def test_plugin_source_git_with_tag(self):
        """Test cloning specific tag."""
        # Create a tag in source
        from picard.git.factory import git_backend
        from picard.plugin3.plugin import PluginSourceGit

        backend = git_backend()
        repo = backend.create_repository(self.plugin_dir)
        commit = repo.get_head_target()
        backend.create_tag(repo, 'v1.0.0', commit, 'Version 1.0.0')
        repo.free()

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir), ref='v1.0.0')

            commit_id = source.sync(target)

            self.assertIsNotNone(commit_id)
            self.assertTrue(target.exists())

    def test_plugin_source_git_with_commit_hash(self):
        """Test cloning specific commit."""
        from picard.git.factory import git_backend
        from picard.plugin3.plugin import PluginSourceGit

        backend = git_backend()
        repo = backend.create_repository(self.plugin_dir)
        first_commit = repo.get_head_target()
        repo.free()

        # Make another commit
        (self.plugin_dir / "second.txt").write_text("second")
        from test.test_plugins3_helpers import backend_add_and_commit

        backend_add_and_commit(self.plugin_dir, 'Second commit')

        with tempfile.TemporaryDirectory() as tmpdir:
            # Clone first commit
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir), ref=first_commit)

            commit_id = source.sync(target)

            self.assertEqual(commit_id, first_commit)
            self.assertFalse((target / "second.txt").exists())  # Should not have second commit

    def test_manager_install_from_git(self):
        """Test full install flow from git repository."""
        from picard.plugin3.manager import PluginManager

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_tagger = MockTagger()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            plugin_id = manager.install_plugin(str(self.plugin_dir))

            # Plugin ID comes from directory name after install (includes UUID prefix)
            self.assertTrue(plugin_id.startswith("test_plugin_"))
            plugin_path = manager._primary_plugin_dir / plugin_id
            self.assertTrue(plugin_path.exists())
            self.assertTrue((plugin_path / "MANIFEST.toml").exists())

            # Verify metadata was stored (need to get UUID from manifest)
            from picard.plugin3.plugin import Plugin

            plugin = Plugin(manager._primary_plugin_dir, plugin_id)
            plugin.read_manifest()
            metadata = manager._get_plugin_metadata(plugin.manifest.uuid)
            self.assertEqual(metadata.url, str(self.plugin_dir))
            self.assertEqual(metadata.ref, 'main')
            self.assertIsNotNone(metadata.commit)

    def test_manager_install_with_ref(self):
        """Test installing plugin from specific ref."""
        # Create dev branch
        from picard.git.factory import git_backend
        from picard.plugin3.manager import PluginManager

        backend = git_backend()
        repo = backend.create_repository(self.plugin_dir)
        repo.free()

        (self.plugin_dir / "dev.txt").write_text("dev")
        from test.test_plugins3_helpers import backend_add_and_commit, backend_create_branch

        dev_commit = backend_add_and_commit(self.plugin_dir, 'Dev')
        backend_create_branch(self.plugin_dir, 'dev', dev_commit)

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_tagger = MockTagger()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            plugin_id = manager.install_plugin(str(self.plugin_dir), ref='origin/dev')

            self.assertTrue(plugin_id.startswith("test_plugin_"))
            self.assertTrue((manager._primary_plugin_dir / plugin_id / "dev.txt").exists())

            # Verify ref was stored (should be the actual ref that resolved)
            from picard.plugin3.plugin import Plugin

            plugin = Plugin(manager._primary_plugin_dir, plugin_id)
            plugin.read_manifest()
            metadata = manager._get_plugin_metadata(plugin.manifest.uuid)
            self.assertEqual(metadata.ref, 'origin/dev')

    def test_manager_update_plugin_from_git(self):
        """Test updating plugin from git."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_tagger = MockTagger()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            # Install first
            plugin_id = manager.install_plugin(str(self.plugin_dir))

            # Create plugin object
            plugin = Plugin(manager._primary_plugin_dir, plugin_id)
            plugin.read_manifest()

            # Make update in source with new version
            manifest_content = """name = "Test Plugin"
authors = ["Test Author"]
version = "1.1.0"
description = "A test plugin - updated"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
uuid = "3fa397ec-0f2a-47dd-9223-e47ce9f2d692"
"""
            (self.plugin_dir / "MANIFEST.toml").write_text(manifest_content)
            (self.plugin_dir / "update.txt").write_text("updated")
            from test.test_plugins3_helpers import backend_add_and_commit

            backend_add_and_commit(self.plugin_dir, 'Update to 1.1.0')

            # Update
            result = manager.update_plugin(plugin)

            self.assertEqual(str(result.old_version), '1.0.0.final0')
            self.assertEqual(str(result.new_version), '1.1.0.final0')
            self.assertNotEqual(result.old_commit, result.new_commit)
            self.assertTrue((plugin.local_path / "update.txt").exists())

    def test_manifest_read_from_git_repo(self):
        """Test reading MANIFEST.toml from cloned git repository."""
        from picard.plugin3.plugin import (
            Plugin,
            PluginSourceGit,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir))
            source.sync(target)

            # Read manifest from cloned repo
            plugin = Plugin(target.parent, target.name)
            plugin.read_manifest()

            self.assertIsNotNone(plugin.manifest)
            self.assertEqual(plugin.manifest.name(), "Test Plugin")
            self.assertEqual(plugin.manifest.authors, ("Test Author",))
            self.assertEqual(str(plugin.manifest.version), "1.0.0.final0")
            self.assertEqual(plugin.manifest.description('en'), "A test plugin")

    def test_install_validates_manifest_from_git(self):
        """Test that install validates MANIFEST.toml from git repo."""
        from picard.plugin3.manager import PluginManager

        # Create repo without MANIFEST
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_plugin_dir = Path(tmpdir) / "bad-plugin"
            from test.test_plugins3_helpers import backend_init_and_commit

            backend_init_and_commit(bad_plugin_dir, {"README.md": "No manifest"}, 'Initial')

            # Try to install
            mock_tagger = MockTagger()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            from picard.plugin3.manager import PluginManifestNotFoundError

            with self.assertRaises(PluginManifestNotFoundError) as context:
                manager.install_plugin(str(bad_plugin_dir))

            self.assertIn('No MANIFEST.toml', str(context.exception))


@pytest.mark.skipif(not HAS_GIT_BACKEND, reason="git backend not available")
class TestCleanPythonCache(PicardTestCase):
    """Test clean_python_cache function."""

    def setUp(self):
        """Create a temporary directory with Python cache files."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.test_dir = Path(self.tmpdir) / "test"
        self.test_dir.mkdir()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_clean_pycache_directory(self):
        """Test removing __pycache__ directory."""
        from picard.plugin3.git_ops import clean_python_cache

        pycache = self.test_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "test.cpython-312.pyc").write_text("cache")

        clean_python_cache(self.test_dir)

        self.assertFalse(pycache.exists())

    def test_clean_pyc_files(self):
        """Test removing .pyc files."""
        from picard.plugin3.git_ops import clean_python_cache

        pyc_file = self.test_dir / "test.pyc"
        pyc_file.write_text("cache")

        clean_python_cache(self.test_dir)

        self.assertFalse(pyc_file.exists())

    def test_clean_pyo_files(self):
        """Test removing .pyo files."""
        from picard.plugin3.git_ops import clean_python_cache

        pyo_file = self.test_dir / "test.pyo"
        pyo_file.write_text("cache")

        clean_python_cache(self.test_dir)

        self.assertFalse(pyo_file.exists())

    def test_clean_nested_cache(self):
        """Test removing cache files in nested directories."""
        from picard.plugin3.git_ops import clean_python_cache

        subdir = self.test_dir / "subdir"
        subdir.mkdir()
        pycache = subdir / "__pycache__"
        pycache.mkdir()
        (pycache / "nested.cpython-312.pyc").write_text("cache")
        (subdir / "nested.pyc").write_text("cache")

        clean_python_cache(self.test_dir)

        self.assertFalse(pycache.exists())
        self.assertFalse((subdir / "nested.pyc").exists())
        self.assertTrue(subdir.exists())

    def test_clean_preserves_other_files(self):
        """Test that non-cache files are preserved."""
        from picard.plugin3.git_ops import clean_python_cache

        py_file = self.test_dir / "test.py"
        py_file.write_text("code")
        txt_file = self.test_dir / "readme.txt"
        txt_file.write_text("docs")

        clean_python_cache(self.test_dir)

        self.assertTrue(py_file.exists())
        self.assertTrue(txt_file.exists())


@pytest.mark.skipif(not HAS_GIT_BACKEND, reason="git backend not available")
class TestCheckDirtyWorkingDir(PicardTestCase):
    """Test check_dirty_working_dir function."""

    def setUp(self):
        """Create a temporary git repository."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.repo_dir = Path(self.tmpdir) / "test-repo"

        from test.test_plugins3_helpers import backend_init_and_commit

        backend_init_and_commit(self.repo_dir, {"file.txt": "content"}, 'Initial')

    def tearDown(self):
        """Clean up temporary directory."""
        import gc
        import shutil

        gc.collect()
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        super().tearDown()

    def test_clean_working_dir(self):
        """Test that clean working directory returns empty list."""
        from picard.plugin3.git_ops import GitOperations

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, [])

    def test_modified_file_detected(self):
        """Test that modified files are detected."""
        from picard.plugin3.git_ops import GitOperations

        (self.repo_dir / "file.txt").write_text("modified")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, ["file.txt"])

    def test_untracked_file_detected(self):
        """Test that untracked files are detected."""
        from picard.plugin3.git_ops import GitOperations

        (self.repo_dir / "new.txt").write_text("new")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, ["new.txt"])

    def test_pyc_files_ignored(self):
        """Test that .pyc files are ignored."""
        from picard.plugin3.git_ops import GitOperations

        (self.repo_dir / "test.pyc").write_text("cache")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, [])

    def test_pyo_files_ignored(self):
        """Test that .pyo files are ignored."""
        from picard.plugin3.git_ops import GitOperations

        (self.repo_dir / "test.pyo").write_text("cache")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, [])

    def test_pycache_directory_ignored(self):
        """Test that __pycache__ directory is ignored."""
        from picard.plugin3.git_ops import GitOperations

        pycache = self.repo_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "test.cpython-312.pyc").write_text("cache")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, [])

    def test_nested_pycache_ignored(self):
        """Test that nested __pycache__ is ignored."""
        from picard.plugin3.git_ops import GitOperations

        subdir = self.repo_dir / "subdir"
        subdir.mkdir()
        pycache = subdir / "__pycache__"
        pycache.mkdir()
        (pycache / "nested.cpython-312.pyc").write_text("cache")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, [])

    def test_real_changes_with_cache_files(self):
        """Test that real changes are detected even with cache files present."""
        from picard.plugin3.git_ops import GitOperations

        (self.repo_dir / "real.txt").write_text("real change")
        (self.repo_dir / "test.pyc").write_text("cache")
        pycache = self.repo_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "test.cpython-312.pyc").write_text("cache")

        changes = GitOperations.check_dirty_working_dir(self.repo_dir)

        self.assertEqual(changes, ["real.txt"])

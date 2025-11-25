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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

import pygit2


class TestPluginGitOperations(PicardTestCase):
    """Test git operations for plugin installation and updates."""

    def setUp(self):
        """Create a temporary git repository with a valid plugin."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.tmpdir) / "test-plugin"
        self.plugin_dir.mkdir()

        # Initialize git repo
        repo = pygit2.init_repository(str(self.plugin_dir))

        # Create MANIFEST.toml
        manifest_content = """name = "Test Plugin"
authors = ["Test Author"]
version = "1.0.0"
description = "A test plugin"
api = ["3.0"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
"""
        (self.plugin_dir / "MANIFEST.toml").write_text(manifest_content)

        # Create __init__.py
        (self.plugin_dir / "__init__.py").write_text("""
def enable(api):
    pass

def disable():
    pass
""")

        # Commit files
        index = repo.index
        index.add_all()
        index.write()

        tree = index.write_tree()
        author = pygit2.Signature("Test", "test@example.com")
        repo.create_commit('refs/heads/main', author, author, 'Initial commit', tree, [])

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

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
            repo = pygit2.Repository(str(self.plugin_dir))
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            repo.create_commit('refs/heads/main', author, author, 'Add new file', tree, [repo.head.target])

            # Update - need to use origin/main after clone
            source_with_remote = PluginSourceGit(str(self.plugin_dir), ref='origin/main')
            old, new = source_with_remote.update(target)

            self.assertNotEqual(old, new)
            self.assertEqual(old, old_commit)
            self.assertTrue((target / "newfile.txt").exists())
            self.assertEqual((target / "newfile.txt").read_text(), "new content")

    def test_plugin_source_git_with_branch(self):
        """Test cloning specific branch."""
        from picard.plugin3.plugin import PluginSourceGit

        # Create a dev branch in source
        repo = pygit2.Repository(str(self.plugin_dir))
        main_commit = repo.head.target

        # Create file on dev branch
        (self.plugin_dir / "dev-feature.txt").write_text("dev only")
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        author = pygit2.Signature("Test", "test@example.com")
        dev_commit = repo.create_commit('refs/heads/dev', author, author, 'Dev feature', tree, [main_commit])

        with tempfile.TemporaryDirectory() as tmpdir:
            # Clone dev branch
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir), ref='origin/dev')

            commit_id = source.sync(target)

            self.assertEqual(commit_id, str(dev_commit))
            self.assertTrue((target / "dev-feature.txt").exists())

    def test_plugin_source_git_with_tag(self):
        """Test cloning specific tag."""
        from picard.plugin3.plugin import PluginSourceGit

        # Create a tag in source
        repo = pygit2.Repository(str(self.plugin_dir))
        commit = repo.head.target
        author = pygit2.Signature("Test", "test@example.com")
        repo.create_tag('v1.0.0', commit, pygit2.GIT_OBJECT_COMMIT, author, 'Version 1.0.0')

        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "cloned"
            source = PluginSourceGit(str(self.plugin_dir), ref='v1.0.0')

            commit_id = source.sync(target)

            self.assertIsNotNone(commit_id)
            self.assertTrue(target.exists())

    def test_plugin_source_git_with_commit_hash(self):
        """Test cloning specific commit."""
        from picard.plugin3.plugin import PluginSourceGit

        repo = pygit2.Repository(str(self.plugin_dir))
        first_commit = str(repo.head.target)

        # Make another commit
        (self.plugin_dir / "second.txt").write_text("second")
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        author = pygit2.Signature("Test", "test@example.com")
        repo.create_commit('refs/heads/main', author, author, 'Second commit', tree, [repo.head.target])

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
            mock_tagger = Mock()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            plugin_id = manager.install_plugin(str(self.plugin_dir))

            # Plugin ID comes from directory name after install
            self.assertIn(plugin_id, ["test_plugin", "test-plugin"])
            plugin_path = manager._primary_plugin_dir / plugin_id
            self.assertTrue(plugin_path.exists())
            self.assertTrue((plugin_path / "MANIFEST.toml").exists())

            # Verify metadata was stored
            metadata = manager._get_plugin_metadata(plugin_id)
            self.assertEqual(metadata['url'], str(self.plugin_dir))
            self.assertEqual(metadata['ref'], 'main')
            self.assertIsNotNone(metadata['commit'])

    def test_manager_install_with_ref(self):
        """Test installing plugin from specific ref."""
        from picard.plugin3.manager import PluginManager

        # Create dev branch
        repo = pygit2.Repository(str(self.plugin_dir))
        main_commit = repo.head.target
        (self.plugin_dir / "dev.txt").write_text("dev")
        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        author = pygit2.Signature("Test", "test@example.com")
        repo.create_commit('refs/heads/dev', author, author, 'Dev', tree, [main_commit])

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_tagger = Mock()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            plugin_id = manager.install_plugin(str(self.plugin_dir), ref='origin/dev')

            self.assertEqual(plugin_id, "test_plugin")
            self.assertTrue((manager._primary_plugin_dir / "test_plugin" / "dev.txt").exists())

            # Verify ref was stored
            metadata = manager._get_plugin_metadata("test_plugin")
            self.assertEqual(metadata['ref'], 'origin/dev')

    def test_manager_update_plugin_from_git(self):
        """Test updating plugin from git."""
        from picard.plugin3.manager import PluginManager
        from picard.plugin3.plugin import Plugin

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_tagger = Mock()
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
"""
            (self.plugin_dir / "MANIFEST.toml").write_text(manifest_content)
            (self.plugin_dir / "update.txt").write_text("updated")
            repo = pygit2.Repository(str(self.plugin_dir))
            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            repo.create_commit('refs/heads/main', author, author, 'Update to 1.1.0', tree, [repo.head.target])

            # Update
            old_ver, new_ver, old_commit, new_commit = manager.update_plugin(plugin)

            self.assertEqual(str(old_ver), '1.0.0.final0')
            self.assertEqual(str(new_ver), '1.1.0.final0')
            self.assertNotEqual(old_commit, new_commit)
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
            bad_plugin_dir.mkdir()

            repo = pygit2.init_repository(str(bad_plugin_dir))
            (bad_plugin_dir / "README.md").write_text("No manifest")

            index = repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature("Test", "test@example.com")
            repo.create_commit('refs/heads/main', author, author, 'Initial', tree, [])

            # Try to install
            mock_tagger = Mock()
            manager = PluginManager(mock_tagger)
            manager._primary_plugin_dir = Path(tmpdir) / "plugins"
            manager._primary_plugin_dir.mkdir()

            with self.assertRaises(ValueError) as context:
                manager.install_plugin(str(bad_plugin_dir))

            self.assertIn('No MANIFEST.toml', str(context.exception))

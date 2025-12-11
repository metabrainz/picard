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
from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.git.factory import has_git_backend
from picard.plugin3.plugin import (
    PluginSource,
    PluginSourceGit,
)


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

        from unittest.mock import patch

        from picard.git.factory import git_backend

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

        import tempfile

        from picard.plugin3.plugin import PluginSourceGit

        # Create a test git repo
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / 'source'
            from test.test_plugins3_helpers import backend_init_and_commit

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

        import tempfile

        from picard.plugin3.plugin import PluginSourceGit

        # Create a test git repo with a tag
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / 'source'
            from test.test_plugins3_helpers import backend_create_tag, backend_init_and_commit

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

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
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.git.backend import GitRefType
from picard.git.factory import has_git_backend
from picard.plugin3 import (
    GitBackendError,
    GitReferenceError,
)
from picard.plugin3.plugin import (
    PluginSourceGit,
    PluginSourceLocal,
    PluginSourceSyncError,
)


class TestPluginSourceGit(PicardTestCase):
    def test_plugin_source_git_without_backend(self):
        """Test PluginSourceGit raises error when git backend not available."""
        if has_git_backend():
            self.skipTest('git backend is available')

        with self.assertRaises(PluginSourceSyncError) as context:
            PluginSourceGit('https://example.com/repo.git')

        self.assertIn('git backend is not available', str(context.exception))

    def test_plugin_source_git_retry_on_network_error(self):
        """Test PluginSourceGit retries on network errors."""
        if not has_git_backend():
            self.skipTest('git backend is not available')

        source = PluginSourceGit('https://example.com/repo.git')

        # Mock operation that fails twice then succeeds
        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise GitBackendError('Failed to resolve host')
            return 'success'

        with patch('picard.plugin3.plugin.time.sleep'):  # Skip actual sleep
            result = source._retry_git_operation(mock_operation)

        self.assertEqual(call_count, 3)
        self.assertEqual(result, 'success')

    def test_plugin_source_git_no_retry_on_non_network_error(self):
        """Test PluginSourceGit does not retry on non-network errors."""
        if not has_git_backend():
            self.skipTest('git backend is not available')

        source = PluginSourceGit('https://example.com/repo.git')

        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            raise GitReferenceError('Invalid reference')

        with self.assertRaises(GitReferenceError):
            source._retry_git_operation(mock_operation)

        # Should only try once (no retries for non-network errors)
        self.assertEqual(call_count, 1)


class TestListAvailableRefs(PicardTestCase):
    def _make_mock_ref(self, shortname, ref_type, is_remote=False):
        ref = Mock()
        ref.shortname = shortname
        ref.ref_type = ref_type
        ref.is_remote = is_remote
        return ref

    def test_list_available_refs_with_generator(self):
        """_list_available_refs must work when list_references() returns a generator."""
        source = PluginSourceGit('https://example.com/repo.git')
        mock_repo = Mock()

        refs = [
            self._make_mock_ref('main', GitRefType.BRANCH),
            self._make_mock_ref('origin/main', GitRefType.BRANCH, is_remote=True),
            self._make_mock_ref('v1.0', GitRefType.TAG),
        ]
        # Use a generator (not a list) to expose the exhaustion bug
        mock_repo.list_references.return_value = (r for r in refs)

        result = source._list_available_refs(mock_repo)
        self.assertIn('main', result)
        self.assertIn('v1.0', result)

    def test_list_available_refs_truncation(self):
        """_list_available_refs must show truncation count correctly."""
        source = PluginSourceGit('https://example.com/repo.git')
        mock_repo = Mock()

        # 25 branches, limit=20 → should show "... (5 more)"
        refs = [self._make_mock_ref(f'branch-{i}', GitRefType.BRANCH) for i in range(25)]
        mock_repo.list_references.return_value = (r for r in refs)

        result = source._list_available_refs(mock_repo, limit=20)
        self.assertIn('5 more', result)

    def test_list_available_refs_no_limit(self):
        """_list_available_refs with limit<=0 must return all refs without truncation."""
        source = PluginSourceGit('https://example.com/repo.git')
        mock_repo = Mock()

        refs = [self._make_mock_ref(f'branch-{i}', GitRefType.BRANCH) for i in range(25)]
        mock_repo.list_references.return_value = iter(refs)

        result = source._list_available_refs(mock_repo, limit=0)
        self.assertNotIn('more', result)
        self.assertIn('branch-24', result)


class TestPluginSourceLocal(PicardTestCase):
    def test_plugin_source_local_sync(self):
        """Test PluginSourceLocal.sync() does nothing."""
        source = PluginSourceLocal()
        # Should not raise and return None
        self.assertIsNone(source.sync(Path('/tmp/test')))

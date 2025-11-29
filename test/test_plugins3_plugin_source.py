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

from test.picardtestcase import PicardTestCase

from picard.plugin3.plugin import (
    HAS_PYGIT2,
    PluginSourceSyncError,
)


class TestPluginSourceGit(PicardTestCase):
    def test_plugin_source_git_without_pygit2(self):
        """Test PluginSourceGit raises error when pygit2 not available."""
        if HAS_PYGIT2:
            self.skipTest('pygit2 is available')

        from picard.plugin3.plugin import PluginSourceGit

        with self.assertRaises(PluginSourceSyncError) as context:
            PluginSourceGit('https://example.com/repo.git')

        self.assertIn('pygit2 is not available', str(context.exception))

    def test_plugin_source_git_retry_on_network_error(self):
        """Test PluginSourceGit retries on network errors."""
        if not HAS_PYGIT2:
            self.skipTest('pygit2 is not available')

        from unittest.mock import patch

        from picard.plugin3.plugin import PluginSourceGit

        import pygit2

        source = PluginSourceGit('https://example.com/repo.git')

        # Mock operation that fails twice then succeeds
        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise pygit2.GitError('Failed to resolve host')
            return 'success'

        with patch('picard.plugin3.plugin.time.sleep'):  # Skip actual sleep
            result = source._retry_git_operation(mock_operation)

        self.assertEqual(call_count, 3)
        self.assertEqual(result, 'success')

    def test_plugin_source_git_no_retry_on_non_network_error(self):
        """Test PluginSourceGit does not retry on non-network errors."""
        if not HAS_PYGIT2:
            self.skipTest('pygit2 is not available')

        from picard.plugin3.plugin import PluginSourceGit

        import pygit2

        source = PluginSourceGit('https://example.com/repo.git')

        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            raise pygit2.GitError('Invalid reference')

        with self.assertRaises(pygit2.GitError):
            source._retry_git_operation(mock_operation)

        # Should only try once (no retries for non-network errors)
        self.assertEqual(call_count, 1)


class TestPluginSourceLocal(PicardTestCase):
    def test_plugin_source_local_sync(self):
        """Test PluginSourceLocal.sync() does nothing."""
        from pathlib import Path

        from picard.plugin3.plugin import PluginSourceLocal

        source = PluginSourceLocal()
        # Should not raise
        source.sync(Path('/tmp/test'))

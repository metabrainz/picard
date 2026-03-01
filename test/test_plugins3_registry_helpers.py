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

import os
from picard.const.sys import IS_WIN

from test.picardtestcase import PicardTestCase

from picard.git.utils import (
    is_local_path,
    normalize_git_url,
)


class TestRegistryHelpers(PicardTestCase):
    def test_normalize_git_url_empty(self):
        """Test normalize_git_url with empty string."""
        self.assertEqual(normalize_git_url(''), '')
        self.assertEqual(normalize_git_url(None), None)

    def test_normalize_git_url_remote(self):
        """Test normalize_git_url with remote URLs."""
        self.assertEqual(normalize_git_url('https://example.com/repo.git'), 'https://example.com/repo.git')
        self.assertEqual(normalize_git_url('git://example.com/repo.git'), 'git://example.com/repo.git')

    def test_normalize_git_url_file_protocol(self):
        """Test normalize_git_url with file:// protocol."""
        result = normalize_git_url('file:///tmp/repo')
        self.assertTrue(os.path.isabs(result))
        self.assertIn('tmp', result)

    def test_normalize_git_url_local_path(self):
        """Test normalize_git_url with local paths."""
        result = normalize_git_url('/tmp/repo')
        # Compare absolute paths to handle Windows vs Unix differences
        self.assertEqual(result, os.path.abspath('/tmp/repo'))

    def test_is_local_path_empty(self):
        """Test is_local_path with empty string."""
        self.assertFalse(is_local_path(''))
        self.assertFalse(is_local_path(None))

    def test_is_local_path_remote_urls(self):
        """Test is_local_path with remote URLs."""
        self.assertFalse(is_local_path('https://example.com/repo.git'))
        self.assertFalse(is_local_path('git://example.com/repo.git'))
        self.assertFalse(is_local_path('ssh://git@example.com/repo.git'))

    def test_is_local_path_file_protocol(self):
        """Test is_local_path with file:// protocol."""
        self.assertTrue(is_local_path('file:///tmp/repo'))

    def test_is_local_path_scp_syntax(self):
        """Test is_local_path with scp-like syntax."""
        self.assertFalse(is_local_path('git@github.com:user/repo.git'))
        self.assertFalse(is_local_path('user@host:path/to/repo'))
        self.assertFalse(is_local_path('github.com:user/repo.git'))
        self.assertFalse(is_local_path('host:path/to/repo'))

    def test_is_local_path_local_paths(self):
        """Test is_local_path with local paths."""
        self.assertTrue(is_local_path('/tmp/repo'))
        self.assertTrue(is_local_path('~/repo'))
        self.assertTrue(is_local_path('relative/path'))
        self.assertTrue(is_local_path('./dir:with-colon'))
        self.assertTrue(is_local_path('../dir:with-colon'))
        self.assertTrue(is_local_path('C:/repo'))
        self.assertTrue(is_local_path('D:\\repo'))
        if IS_WIN:
            self.assertTrue(is_local_path('C:repo'))
        else:
            self.assertFalse(is_local_path('C:repo'))

    def test_is_local_path_scp_short_host(self):
        """Test single-letter `host:path` handling is platform specific."""
        if IS_WIN:
            # On Windows this is interpreted as drive-relative path.
            self.assertTrue(is_local_path('a:repo'))
        else:
            # On POSIX this is treated like an scp-style remote.
            self.assertFalse(is_local_path('a:repo'))

    def test_normalize_git_url_caching(self):
        """Test that normalize_git_url caches results."""
        from picard.git.utils import normalize_git_url

        url = 'https://github.com/test/plugin.git'

        # Clear cache
        normalize_git_url.cache_clear()

        # First call
        result1 = normalize_git_url(url)
        cache_info1 = normalize_git_url.cache_info()

        # Second call with same URL
        result2 = normalize_git_url(url)
        cache_info2 = normalize_git_url.cache_info()

        # Results should be identical
        self.assertEqual(result1, result2)

        # Cache should have been hit
        self.assertEqual(cache_info1.hits, 0)
        self.assertEqual(cache_info1.misses, 1)
        self.assertEqual(cache_info2.hits, 1)
        self.assertEqual(cache_info2.misses, 1)

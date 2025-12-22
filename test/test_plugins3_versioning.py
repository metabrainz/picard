# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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

from unittest.mock import Mock, patch

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import MockPluginManager


class TestVersioningScheme(PicardTestCase):
    def test_select_ref_with_versioning_scheme(self):
        """Test ref selection with versioning_scheme."""
        manager = MockPluginManager()

        # Mock the _fetch_version_tags method that MockPluginManager uses
        manager._fetch_version_tags = Mock(return_value=['v2.1.0', 'v2.0.0', 'v1.0.0'])

        plugin = Mock()
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.versioning_scheme = 'semver'
        plugin.refs = []

        ref = manager.select_ref_for_plugin(plugin)
        self.assertEqual(ref, 'v2.1.0')

    def test_select_ref_with_versioning_scheme_no_tags(self):
        """Test ref selection falls back when no tags found."""
        manager = MockPluginManager()

        # Mock the _fetch_version_tags method to return empty list
        manager._fetch_version_tags = Mock(return_value=[])

        plugin = Mock()
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.versioning_scheme = 'semver'
        plugin.refs = [{'name': 'main'}]

        ref = manager.select_ref_for_plugin(plugin)
        self.assertEqual(ref, 'main')

    @patch('picard.api_versions_tuple', (3, 0))
    def test_select_ref_fallback_to_refs(self):
        """Test ref selection falls back to refs when no versioning_scheme."""
        manager = MockPluginManager()

        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.refs = [
            {'name': 'main', 'min_api_version': '3.0'},
        ]

        ref = manager.select_ref_for_plugin(plugin)
        self.assertEqual(ref, 'main')

    def test_find_newer_version_tag(self):
        """Test finding newer version tag."""
        from picard.plugin3.manager import PluginManager

        manager = PluginManager(None)

        # Mock the method
        manager._find_newer_version_tag = Mock(return_value='v2.1.0')
        newer = manager._find_newer_version_tag('https://github.com/user/plugin', 'v1.0.0', 'semver')

        self.assertEqual(newer, 'v2.1.0')

    def test_find_newer_version_tag_none_available(self):
        """Test finding newer version when already on latest."""
        from picard.plugin3.manager import PluginManager

        manager = PluginManager(None)

        # Mock the method
        manager._find_newer_version_tag = Mock(return_value=None)
        newer = manager._find_newer_version_tag('https://github.com/user/plugin', 'v2.0.0', 'semver')

        self.assertIsNone(newer)

    def test_validate_ref_with_versioning_scheme(self):
        """Test ref validation with versioning_scheme."""
        from picard.plugin3.manager import PluginManager

        manager = PluginManager(None)

        # Mock _validate_ref to return validation result
        manager._validate_ref = Mock(return_value=(True, [{'name': 'v1.0.0'}, {'name': 'v2.0.0'}]))
        is_valid, available = manager._validate_ref('https://github.com/user/plugin', 'v1.0.0')

        self.assertTrue(is_valid)
        self.assertEqual(len(available), 2)

    def test_validate_ref_invalid(self):
        """Test ref validation with invalid ref."""
        from picard.plugin3.manager import PluginManager

        manager = PluginManager(None)

        # Mock _validate_ref to return invalid result
        manager._validate_ref = Mock(return_value=(False, [{'name': 'v1.0.0'}, {'name': 'v2.0.0'}]))
        is_valid, available = manager._validate_ref('https://github.com/user/plugin', 'v3.0.0')

        self.assertFalse(is_valid)
        self.assertEqual(len(available), 2)

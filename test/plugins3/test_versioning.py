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

from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.manager import PluginManager
from picard.plugin3.manager.registry import (
    PluginRegistryManager,
    _parse_version_safely,
    _strip_to_first_digit,
)
from picard.version import Version


class TestStripToFirstDigit(PicardTestCase):
    def test_strips_prefix(self):
        self.assertEqual(_strip_to_first_digit('v1.0.0'), '1.0.0')

    def test_no_prefix(self):
        self.assertEqual(_strip_to_first_digit('1.0.0'), '1.0.0')

    def test_long_prefix(self):
        self.assertEqual(_strip_to_first_digit('release-2.0'), '2.0')

    def test_no_digits(self):
        self.assertEqual(_strip_to_first_digit('abc'), 'abc')


class TestParseVersionSafely(PicardTestCase):
    def test_valid_semver(self):
        v = _parse_version_safely('v1.2.3')
        self.assertIsNotNone(v)

    def test_invalid_returns_none(self):
        self.assertIsNone(_parse_version_safely('not-a-version'))


class TestSortTags(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.mgr = PluginRegistryManager(Mock())

    def test_semver_sort(self):
        tags = ['v1.0.0', 'v2.1.0', 'v1.5.0']
        result = self.mgr._sort_tags(tags, 'semver')
        self.assertEqual(result, ['v2.1.0', 'v1.5.0', 'v1.0.0'])

    def test_semver_with_prefix_variations(self):
        tags = ['release-1.0.0', 'v2.0.0', '3.0.0']
        result = self.mgr._sort_tags(tags, 'semver')
        self.assertEqual(result[0], '3.0.0')

    def test_calver_sort(self):
        tags = ['2024.01.15', '2025.06.01', '2024.12.30']
        result = self.mgr._sort_tags(tags, 'calver')
        self.assertEqual(result, ['2025.06.01', '2024.12.30', '2024.01.15'])

    def test_custom_regex_sort_with_versions(self):
        tags = ['build-1.0', 'build-2.0', 'build-1.5']
        result = self.mgr._sort_tags(tags, 'regex:^build-')
        self.assertEqual(result[0], 'build-2.0')

    def test_custom_regex_sort_no_version(self):
        """Tags that can't be parsed as versions use natural sort."""
        tags = ['abc', 'xyz', 'def']
        result = self.mgr._sort_tags(tags, 'regex:.*')
        self.assertEqual(result, ['xyz', 'def', 'abc'])


class TestFetchVersionTags(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager_mock = Mock()
        self.mgr = PluginRegistryManager(self.manager_mock)

    def test_semver_filters_and_sorts(self):
        self.manager_mock.fetch_all_git_refs.return_value = {
            'tags': [{'name': 'v1.0.0'}, {'name': 'v2.0.0'}, {'name': 'latest'}, {'name': 'v1.5.0'}],
        }
        result = self.mgr._fetch_version_tags('https://example.com/repo', 'semver')
        self.assertEqual(result, ['v2.0.0', 'v1.5.0', 'v1.0.0'])
        self.assertNotIn('latest', result)

    def test_calver_filters(self):
        self.manager_mock.fetch_all_git_refs.return_value = {
            'tags': [{'name': '2024.01.15'}, {'name': '2025.06.01'}, {'name': 'nope'}],
        }
        result = self.mgr._fetch_version_tags('https://example.com/repo', 'calver')
        self.assertEqual(result, ['2025.06.01', '2024.01.15'])

    def test_custom_regex(self):
        self.manager_mock.fetch_all_git_refs.return_value = {
            'tags': [{'name': 'rel-1.0'}, {'name': 'rel-2.0'}, {'name': 'v1.0'}],
        }
        result = self.mgr._fetch_version_tags('https://example.com/repo', 'regex:^rel-')
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t.startswith('rel-') for t in result))

    def test_unknown_scheme_returns_empty(self):
        result = self.mgr._fetch_version_tags('https://example.com/repo', 'unknown')
        self.assertEqual(result, [])

    def test_no_refs_returns_empty(self):
        self.manager_mock.fetch_all_git_refs.return_value = None
        result = self.mgr._fetch_version_tags('https://example.com/repo', 'semver')
        self.assertEqual(result, [])


class TestFindNewerVersionTag(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = PluginManager(None)

    def test_semver_finds_newer(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=['v2.1.0', 'v2.0.0', 'v1.0.0'])
        result = self.manager._find_newer_version_tag('url', 'v1.0.0', 'semver')
        self.assertEqual(result, 'v2.1.0')

    def test_semver_none_when_latest(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=['v2.0.0'])
        result = self.manager._find_newer_version_tag('url', 'v2.0.0', 'semver')
        self.assertIsNone(result)

    def test_no_tags_returns_none(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=[])
        result = self.manager._find_newer_version_tag('url', 'v1.0.0', 'semver')
        self.assertIsNone(result)

    def test_calver_finds_newer(self):
        self.manager._registry_manager._fetch_version_tags = Mock(
            return_value=['2025.06.01', '2024.12.30', '2024.01.15']
        )
        result = self.manager._find_newer_version_tag('url', '2024.01.15', 'calver')
        self.assertEqual(result, '2025.06.01')

    def test_calver_none_when_latest(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=['2025.06.01'])
        result = self.manager._find_newer_version_tag('url', '2025.06.01', 'calver')
        self.assertIsNone(result)

    def test_custom_regex_lexicographic_fallback(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=['build-3', 'build-2', 'build-1'])
        result = self.manager._find_newer_version_tag('url', 'build-1', 'regex:^build-')
        self.assertEqual(result, 'build-3')

    def test_unparseable_current_tag_returns_none(self):
        self.manager._registry_manager._fetch_version_tags = Mock(return_value=['v2.0.0'])
        result = self.manager._find_newer_version_tag('url', 'not-a-version', 'semver')
        self.assertIsNone(result)


class TestGetRegistryPluginLatestVersion(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.mgr = PluginRegistryManager(Mock())

    def test_returns_latest_tag(self):
        self.mgr._fetch_version_tags = Mock(return_value=['v2.0.0', 'v1.0.0'])
        plugin = Mock()
        plugin.versioning_scheme = 'semver'
        plugin.git_url = 'https://example.com/repo'
        self.assertEqual(self.mgr.get_registry_plugin_latest_version(plugin), 'v2.0.0')

    def test_no_versioning_scheme(self):
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'https://example.com/repo'
        self.assertEqual(self.mgr.get_registry_plugin_latest_version(plugin), '')

    def test_no_git_url(self):
        plugin = Mock()
        plugin.versioning_scheme = 'semver'
        plugin.git_url = None
        self.assertEqual(self.mgr.get_registry_plugin_latest_version(plugin), '')

    def test_no_tags_found(self):
        self.mgr._fetch_version_tags = Mock(return_value=[])
        plugin = Mock()
        plugin.versioning_scheme = 'semver'
        plugin.git_url = 'https://example.com/repo'
        self.assertEqual(self.mgr.get_registry_plugin_latest_version(plugin), '')

    def test_error_returns_empty(self):
        self.mgr._fetch_version_tags = Mock(side_effect=Exception('fail'))
        plugin = Mock()
        plugin.versioning_scheme = 'semver'
        plugin.git_url = 'https://example.com/repo'
        self.assertEqual(self.mgr.get_registry_plugin_latest_version(plugin), '')


class TestSelectRefForPlugin(PicardTestCase):
    def test_versioning_scheme_returns_latest_tag(self):
        mgr = PluginRegistryManager(Mock())
        mgr._fetch_version_tags = Mock(return_value=['v2.1.0', 'v2.0.0', 'v1.0.0'])
        plugin = Mock()
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.versioning_scheme = 'semver'
        plugin.refs = []
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'v2.1.0')

    def test_versioning_scheme_no_tags_falls_back(self):
        mgr = PluginRegistryManager(Mock())
        mgr._fetch_version_tags = Mock(return_value=[])
        plugin = Mock()
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.versioning_scheme = 'semver'
        plugin.refs = [{'name': 'main'}]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'main')

    @patch('picard.plugin3.manager.registry.api_versions_tuple', [Version.from_string('3.0')])
    def test_no_versioning_uses_refs(self):
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'https://github.com/user/plugin'
        plugin.refs = [{'name': 'main', 'min_api_version': '3.0'}]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'main')

    @patch('picard.plugin3.manager.registry.api_versions_tuple', [Version.from_string('3.0')])
    def test_api_version_skips_incompatible_refs(self):
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'url'
        plugin.refs = [
            {'name': 'main', 'min_api_version': '4.0'},
            {'name': 'picard-v3', 'min_api_version': '3.0', 'max_api_version': '3.99'},
        ]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'picard-v3')

    @patch('picard.plugin3.manager.registry.api_versions_tuple', [Version.from_string('5.0')])
    def test_api_version_above_max_skips(self):
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'url'
        plugin.refs = [
            {'name': 'picard-v3', 'min_api_version': '3.0', 'max_api_version': '3.99'},
            {'name': 'main', 'min_api_version': '4.0'},
        ]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'main')

    def test_no_refs_returns_none(self):
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'url'
        plugin.refs = []
        self.assertIsNone(mgr.select_ref_for_plugin(plugin))

    @patch('picard.plugin3.manager.registry.api_versions_tuple', [Version.from_string('2.0')])
    def test_no_compatible_ref_uses_first(self):
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'url'
        plugin.refs = [
            {'name': 'main', 'min_api_version': '3.0'},
        ]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'main')

    @patch('picard.plugin3.manager.registry.api_versions_tuple', [Version.from_string('10.0')])
    def test_api_version_multi_digit_comparison(self):
        """Ensure API version 10.0 is correctly compared (not string-based)."""
        mgr = PluginRegistryManager(Mock())
        plugin = Mock()
        plugin.versioning_scheme = None
        plugin.git_url = 'url'
        plugin.refs = [
            {'name': 'main', 'min_api_version': '4.0'},
        ]
        self.assertEqual(mgr.select_ref_for_plugin(plugin), 'main')

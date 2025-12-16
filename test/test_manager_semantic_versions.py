# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

from picard.git.utils import RefItem
from picard.plugin3.manager import PluginManager


class TestManagerSemanticVersions(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = PluginManager()

    def test_sort_by_semantic_version(self):
        """Test semantic version sorting."""
        ref_items = [
            RefItem(name="v1.0.0", is_tag=True),
            RefItem(name="v2.1.0", is_tag=True),
            RefItem(name="v1.5.2", is_tag=True),
            RefItem(name="v2.0.0-beta", is_tag=True),
            RefItem(name="v2.0.0", is_tag=True),
            RefItem(name="v10.0.0", is_tag=True),
        ]

        sorted_versions = self.manager._sort_by_semantic_version(ref_items)

        # Should be sorted highest to lowest, stable versions before prereleases
        expected_names = ["v10.0.0", "v2.1.0", "v2.0.0", "v2.0.0-beta", "v1.5.2", "v1.0.0"]
        actual_names = [item.name for item in sorted_versions]

        self.assertEqual(actual_names, expected_names)

    def test_sort_by_semantic_version_mixed_formats(self):
        """Test semantic version sorting with mixed formats."""
        ref_items = [
            RefItem(name="1.0.0", is_tag=True),  # No 'v' prefix
            RefItem(name="v2.0.0", is_tag=True),  # With 'v' prefix
            RefItem(name="v1.5.0-alpha", is_tag=True),  # Prerelease
            RefItem(name="not-a-version", is_tag=True),  # Not semantic version
        ]

        sorted_versions = self.manager._sort_by_semantic_version(ref_items)

        # Only semantic versions should be returned
        expected_names = ["v2.0.0", "v1.5.0-alpha", "1.0.0"]
        actual_names = [item.name for item in sorted_versions]

        self.assertEqual(actual_names, expected_names)

    def test_sort_by_semantic_version_no_semantic_versions(self):
        """Test semantic version sorting when no semantic versions exist."""
        ref_items = [
            RefItem(name="main", is_tag=True),
            RefItem(name="latest", is_tag=True),
            RefItem(name="release", is_tag=True),
        ]

        sorted_versions = self.manager._sort_by_semantic_version(ref_items)

        # Should return empty list
        self.assertEqual(sorted_versions, [])

    def test_default_ref_preference_with_semantic_versions(self):
        """Test default ref preference with semantic versions."""
        ref_items = [
            RefItem(name="main", is_branch=True),
            RefItem(name="v1.0.0", is_tag=True),
            RefItem(name="v2.0.0", is_tag=True),
            RefItem(name="latest", is_tag=True),
        ]

        preferred = self.manager._default_ref_preference(ref_items)

        # Should prefer the highest semantic version tag
        self.assertEqual(preferred.name, "v2.0.0")
        self.assertTrue(preferred.is_tag)

    def test_default_ref_preference_no_semantic_versions(self):
        """Test default ref preference when no semantic versions exist."""
        ref_items = [
            RefItem(name="main", is_branch=True),
            RefItem(name="latest", is_tag=True),
            RefItem(name="release", is_tag=True),
        ]

        preferred = self.manager._default_ref_preference(ref_items)

        # Should prefer first tag (alphabetically)
        self.assertEqual(preferred.name, "latest")
        self.assertTrue(preferred.is_tag)

    def test_default_ref_preference_only_branches(self):
        """Test default ref preference with only branches."""
        ref_items = [
            RefItem(name="main", is_branch=True),
            RefItem(name="develop", is_branch=True),
        ]

        preferred = self.manager._default_ref_preference(ref_items)

        # Should prefer first branch (alphabetically)
        self.assertEqual(preferred.name, "develop")
        self.assertTrue(preferred.is_branch)

    def test_semantic_version_prerelease_handling(self):
        """Test that stable versions are preferred over prereleases."""
        ref_items = [
            RefItem(name="v2.0.0-beta", is_tag=True),
            RefItem(name="v2.0.0-alpha", is_tag=True),
            RefItem(name="v2.0.0", is_tag=True),
            RefItem(name="v1.9.0", is_tag=True),
        ]

        sorted_versions = self.manager._sort_by_semantic_version(ref_items)

        # v2.0.0 (stable) should come before v2.0.0-beta and v2.0.0-alpha
        expected_names = ["v2.0.0", "v2.0.0-beta", "v2.0.0-alpha", "v1.9.0"]
        actual_names = [item.name for item in sorted_versions]

        self.assertEqual(actual_names, expected_names)

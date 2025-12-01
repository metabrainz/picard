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

from test.picardtestcase import PicardTestCase

from picard.plugin3.constants import (
    CATEGORIES,
    MAX_DESCRIPTION_LENGTH,
    MAX_LONG_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    REGISTRY_TRUST_LEVELS,
    REQUIRED_MANIFEST_FIELDS,
    UUID_PATTERN,
)


class TestPluginConstants(PicardTestCase):
    def test_registry_trust_levels(self):
        """Test that registry trust levels are defined correctly."""
        self.assertEqual(REGISTRY_TRUST_LEVELS, ['official', 'trusted', 'community'])
        self.assertEqual(len(REGISTRY_TRUST_LEVELS), 3)

    def test_categories(self):
        """Test that plugin categories are defined."""
        expected = ['metadata', 'coverart', 'ui', 'scripting', 'formats', 'other']
        self.assertEqual(CATEGORIES, expected)
        self.assertEqual(len(CATEGORIES), 6)

    def test_required_manifest_fields(self):
        """Test that required manifest fields are defined."""
        expected = ['uuid', 'name', 'description', 'api']
        self.assertEqual(REQUIRED_MANIFEST_FIELDS, expected)
        self.assertEqual(len(REQUIRED_MANIFEST_FIELDS), 4)

    def test_string_length_constraints(self):
        """Test that string length constraints are positive integers."""
        self.assertEqual(MAX_NAME_LENGTH, 100)
        self.assertEqual(MAX_DESCRIPTION_LENGTH, 200)
        self.assertEqual(MAX_LONG_DESCRIPTION_LENGTH, 2000)
        self.assertGreater(MAX_NAME_LENGTH, 0)
        self.assertGreater(MAX_DESCRIPTION_LENGTH, 0)
        self.assertGreater(MAX_LONG_DESCRIPTION_LENGTH, 0)

    def test_uuid_pattern_valid(self):
        """Test that UUID pattern matches valid UUID v4."""
        valid_uuids = [
            '550e8400-e29b-41d4-a716-446655440000',
            'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d',
            '12345678-1234-4234-8234-123456789012',
            'AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE',  # uppercase
            'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',  # lowercase
        ]
        for uuid in valid_uuids:
            self.assertTrue(UUID_PATTERN.match(uuid), f"Should match valid UUID: {uuid}")

    def test_uuid_pattern_invalid(self):
        """Test that UUID pattern rejects invalid UUIDs."""
        invalid_uuids = [
            '',
            'not-a-uuid',
            '550e8400-e29b-41d4-a716',  # too short
            '550e8400-e29b-41d4-a716-446655440000-extra',  # too long
            '550e8400-e29b-31d4-a716-446655440000',  # wrong version (3 instead of 4)
            '550e8400-e29b-51d4-a716-446655440000',  # wrong version (5 instead of 4)
            '550e8400-e29b-41d4-1716-446655440000',  # wrong variant (1 instead of 8/9/a/b)
            '550e8400e29b41d4a716446655440000',  # no hyphens
        ]
        for uuid in invalid_uuids:
            self.assertFalse(UUID_PATTERN.match(uuid), f"Should not match invalid UUID: {uuid}")

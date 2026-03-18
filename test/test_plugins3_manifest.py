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
from unittest.mock import patch

from test.picardtestcase import PicardTestCase
from test.test_plugins3_helpers import load_plugin_manifest

from picard.plugin3.manifest import PluginManifest
from picard.version import Version


def _manifest_from_toml(content):
    """Create a PluginManifest from a TOML content string."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    try:
        with open(temp_path, 'rb') as f:
            return PluginManifest('test', f)
    finally:
        temp_path.unlink()


class TestPluginManifest(PicardTestCase):
    def test_load_from_toml(self):
        manifest = load_plugin_manifest('example')
        self.assertEqual(manifest.module_name, 'example')
        self.assertEqual(manifest.name(), 'Example plugin')
        self.assertEqual(manifest.authors, ('Philipp Wolfer',))
        self.assertEqual(manifest.description(), "This is an example plugin")
        self.assertEqual(manifest.description('en'), "This is an example plugin")
        self.assertEqual(manifest.description('fr'), "Ceci est un exemple de plugin")
        self.assertEqual(manifest.description('it'), "This is an example plugin")
        self.assertEqual(manifest.version, Version(1, 0, 0))
        self.assertEqual(manifest.api_versions, (Version(3, 0, 0), Version(3, 1, 0)))
        self.assertEqual(manifest.license, 'CC0-1.0')
        self.assertEqual(manifest.license_url, 'https://creativecommons.org/publicdomain/zero/1.0/')

    def test_manifest_missing_translation(self):
        """Test manifest description with missing translation."""
        manifest = load_plugin_manifest('example')

        # Request German translation (exists)
        desc_de = manifest.description('de')
        self.assertEqual(desc_de, "Dies ist ein Beispiel-Plugin")

        # Request non-existent language, should fallback to English
        desc_it = manifest.description('it')
        self.assertEqual(desc_it, "This is an example plugin")

    def test_manifest_name_translation(self):
        """Test manifest name translation."""
        manifest = load_plugin_manifest('example')

        # English (default)
        self.assertEqual(manifest.name('en'), 'Example plugin')

        # German translation
        self.assertEqual(manifest.name('de'), 'Beispiel-Plugin')

        # French translation
        self.assertEqual(manifest.name('fr'), 'Plugin d\'exemple')

        # Non-existent translation falls back to base
        self.assertEqual(manifest.name('it'), 'Example plugin')

    def test_manifest_locale_with_region(self):
        """Test locale with region code (e.g., de_DE) falls back to language (de)."""
        manifest = load_plugin_manifest('example')

        # de_DE should fall back to de
        self.assertEqual(manifest.name('de_DE'), 'Beispiel-Plugin')
        self.assertEqual(manifest.description('de_AT'), "Dies ist ein Beispiel-Plugin")

    def test_manifest_long_description(self):
        """Test long_description field and translation."""
        manifest = load_plugin_manifest('example')

        # English long description
        long_desc = manifest.long_description('en')
        self.assertIn('detailed', long_desc.lower())

        # German long description
        long_desc_de = manifest.long_description('de')
        self.assertIn('ausführlich', long_desc_de.lower())

        # Non-existent translation falls back to English
        long_desc_it = manifest.long_description('it')
        self.assertEqual(long_desc_it, long_desc)

    def test_get_current_locale_no_config(self):
        """_get_current_locale must not crash when get_config() returns None."""
        manifest = load_plugin_manifest('example')
        with patch('picard.config.get_config', return_value=None):
            locale = manifest._get_current_locale()
        self.assertIsInstance(locale, str)
        self.assertTrue(len(locale) > 0)

    def test_manifest_validate_valid(self):
        manifest = load_plugin_manifest('example')
        errors = manifest.validate()
        self.assertEqual(errors, [])

    def test_manifest_validate_missing_fields(self):
        """Test validation catches missing required fields."""
        # Create minimal invalid manifest
        manifest_content = """
name = "Test"
"""
        manifest = _manifest_from_toml(manifest_content)

        errors = manifest.validate()
        self.assertGreater(len(errors), 0)
        # Should have errors for missing required fields
        error_text = ' '.join(errors)
        self.assertIn('uuid', error_text)
        self.assertIn('description', error_text)
        self.assertIn('api', error_text)

    def test_manifest_validate_invalid_types(self):
        """Test validation catches invalid field types."""
        manifest_content = """
name = 123
authors = "not an array"
api = "not an array"
version = "1.0.0"
description = "Test"
license = "MIT"
license_url = "https://example.com"
"""
        manifest = _manifest_from_toml(manifest_content)

        errors = manifest.validate()
        self.assertGreater(len(errors), 0)
        error_text = ' '.join(errors)
        self.assertIn('name', error_text)
        self.assertIn('authors', error_text)
        self.assertIn('api', error_text)

    def test_manifest_validate_empty_i18n_sections(self):
        """Test validation warns about empty i18n sections."""
        manifest_content = """
name = "Test"
authors = ["Author"]
version = "1.0.0"
description = "Test"
api = ["3.0"]
license = "MIT"
license_url = "https://example.com"

[name_i18n]

[description_i18n]
"""
        manifest = _manifest_from_toml(manifest_content)

        errors = manifest.validate()
        self.assertGreater(len(errors), 0)
        error_text = ' '.join(errors)
        self.assertIn('name_i18n', error_text)
        self.assertIn('description_i18n', error_text)
        self.assertIn('empty', error_text.lower())

    def test_manifest_properties(self):
        """Test manifest property accessors."""
        manifest = load_plugin_manifest('example')

        # Test all properties are accessible
        self.assertIsNotNone(manifest.module_name)
        self.assertIsNotNone(manifest.name())
        self.assertIsNotNone(manifest.authors)
        self.assertIsNotNone(manifest.version)
        self.assertIsNotNone(manifest.api_versions)
        self.assertIsNotNone(manifest.license)
        self.assertIsNotNone(manifest.license_url)

    def test_manifest_invalid_version(self):
        """Test manifest with invalid version string."""
        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "invalid"
description = "Test"
api = ["3.0"]
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        manifest = _manifest_from_toml(manifest_content)

        # Should return None for invalid version
        self.assertIsNone(manifest.version)

    def test_manifest_invalid_api_versions(self):
        """Test manifest with invalid API version strings."""
        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "1.0.0"
description = "Test"
api = ["invalid", "bad"]
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        manifest = _manifest_from_toml(manifest_content)

        # Should return empty tuple for invalid versions
        self.assertEqual(manifest.api_versions, tuple())

    def test_manifest_missing_api_versions(self):
        """Test manifest with missing API versions."""
        manifest_content = """
uuid = "550e8400-e29b-41d4-a716-446655440000"
name = "Test"
version = "1.0.0"
description = "Test"
authors = ["Test"]
license = "MIT"
license_url = "https://example.com"
"""
        manifest = _manifest_from_toml(manifest_content)

        # Should return empty tuple when api field is missing
        self.assertEqual(manifest.api_versions, tuple())

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

from picard.plugin3.validator import (
    PLACEHOLDER_UUIDS,
    _is_placeholder_uuid,
    render_markdown,
    validate_manifest_dict,
)


def _valid_manifest(**overrides):
    """Return a valid manifest dict, with optional field overrides."""
    manifest = {
        'uuid': '550e8400-e29b-41d4-a716-446655440000',
        'name': 'Test Plugin',
        'version': '1.0.0',
        'description': 'A test plugin',
        'api': ['3.0'],
        'authors': ['Test Author'],
        'license': 'GPL-2.0-or-later',
        'license_url': 'https://www.gnu.org/licenses/gpl-2.0.html',
    }
    manifest.update(overrides)
    return manifest


class TestManifestValidator(PicardTestCase):
    def test_validate_valid_manifest(self):
        """Test validation of a valid manifest."""
        manifest = _valid_manifest()
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

    def test_validate_missing_required_fields(self):
        """Test validation catches missing required fields."""
        manifest = {'name': 'Test Plugin'}
        errors = validate_manifest_dict(manifest)
        self.assertIn("Missing required field: uuid", errors)
        self.assertIn("Missing required field: description", errors)
        self.assertIn("Missing required field: api", errors)

    def test_validate_invalid_uuid(self):
        """Test validation catches invalid UUID."""
        manifest = _valid_manifest(uuid='not-a-uuid')
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any("must be a valid UUID v4" in e for e in errors))

    def test_validate_invalid_field_types(self):
        """Test validation catches invalid field types."""
        manifest = _valid_manifest(name=123, api='3.0', authors='Test Author')
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'name' must be a string", errors)
        self.assertIn("Field 'authors' must be an array", errors)
        self.assertIn("Field 'api' must be an array", errors)

    def test_validate_string_length_constraints(self):
        """Test validation enforces string length constraints."""
        # Name too long
        manifest = _valid_manifest(name='x' * 101)
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any("Field 'name' must be 1-100 characters" in e for e in errors))

        # Description too long
        manifest['name'] = 'Test Plugin'
        manifest['description'] = 'x' * 201  # Max is 200
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any("Field 'description' must be 1-200 characters" in e for e in errors))

        # Long description too long
        manifest['description'] = 'A test plugin'
        manifest['long_description'] = 'x' * 2001  # Max is 2000
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any("Field 'long_description' must be max 2000 characters" in e for e in errors))

    def test_validate_empty_strings(self):
        """Test validation catches empty strings as missing fields."""
        manifest = _valid_manifest(name='', description='')
        errors = validate_manifest_dict(manifest)
        # Empty strings are caught by "missing required field" check
        self.assertIn("Missing required field: name", errors)
        self.assertIn("Missing required field: description", errors)

    def test_validate_invalid_api_version(self):
        """Test validation catches invalid API version."""
        manifest = _valid_manifest(api=[''])
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any("Invalid API version" in e for e in errors))

    def test_validate_empty_authors(self):
        """Test validation catches empty authors array."""
        manifest = _valid_manifest(authors=[])
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'authors' must contain at least one author if present", errors)

    def test_validate_invalid_category(self):
        """Test that unknown categories are accepted (forward compatibility)."""
        manifest = _valid_manifest(categories=['invalid_category'])
        errors = validate_manifest_dict(manifest)
        # Categories are not validated to allow forward/backward compatibility
        self.assertEqual(errors, [])

    def test_validate_categories(self):
        """Test validation of categories field."""
        # Valid categories
        manifest = _valid_manifest(categories=['metadata', 'coverart'])
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # Empty categories
        manifest['categories'] = []
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'categories' must contain at least one category if present", errors)

        # Wrong type
        manifest['categories'] = 'metadata'
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'categories' must be an array", errors)

    def test_validate_empty_i18n_sections(self):
        """Test validation catches empty i18n sections."""
        manifest = _valid_manifest(name_i18n={}, description_i18n={})
        errors = validate_manifest_dict(manifest)
        self.assertIn("Section 'name_i18n' is present but empty", errors)
        self.assertIn("Section 'description_i18n' is present but empty", errors)

    def test_validate_valid_i18n_sections(self):
        """Test validation accepts valid i18n sections."""
        manifest = _valid_manifest(name_i18n={'de': 'Test Plugin'}, description_i18n={'de': 'Ein Test Plugin'})
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

    def test_validate_source_locale(self):
        """Test validation of source_locale field."""
        manifest = _valid_manifest()

        # Valid locales
        for locale in ['en', 'de', 'fr', 'pt', 'en_US', 'pt_BR', 'zh_CN']:
            with self.subTest(locale=locale):
                manifest['source_locale'] = locale
                errors = validate_manifest_dict(manifest)
                self.assertEqual(errors, [])

        # Invalid formats
        for locale in ['', 'e', 'english', 'en-US', 'en_us', 'EN', 'en_USA', '123']:
            with self.subTest(locale=locale):
                manifest['source_locale'] = locale
                errors = validate_manifest_dict(manifest)
                self.assertTrue(any('source_locale' in e for e in errors))

        # Wrong type
        manifest['source_locale'] = 123
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'source_locale' must be a string", errors)

    def test_validate_license_field(self):
        """Test validation of license field."""
        manifest = _valid_manifest()

        # Valid license
        manifest['license'] = 'GPL-2.0-or-later'
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # Empty license
        manifest['license'] = ''
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'license' must not be empty", errors)

        # Wrong type
        manifest['license'] = 123
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'license' must be a string", errors)

    def test_validate_url_fields(self):
        """Test validation of URL fields (license_url, homepage)."""
        manifest = _valid_manifest()

        # Valid URLs
        manifest['license_url'] = 'https://www.gnu.org/licenses/gpl-2.0.html'
        manifest['homepage'] = 'https://github.com/user/plugin'
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # Empty license_url
        manifest['license_url'] = ''
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'license_url' must not be empty", errors)

        # Wrong type for homepage
        manifest['license_url'] = 'https://example.com'
        manifest['homepage'] = 123
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'homepage' must be a string", errors)

    def test_validate_min_python_version(self):
        """Test validation of min_python_version field."""
        manifest = _valid_manifest()

        # Valid version
        manifest['min_python_version'] = '3.9'
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # Empty version
        manifest['min_python_version'] = ''
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'min_python_version' must not be empty", errors)

        # Wrong type
        manifest['min_python_version'] = 3.9
        errors = validate_manifest_dict(manifest)
        self.assertIn("Field 'min_python_version' must be a string", errors)

    def test_validate_markdown_in_long_description(self):
        """Test validation of markdown in long_description."""
        manifest = _valid_manifest()

        # Valid markdown
        manifest['long_description'] = '''
This is **bold** and *italic*.

- List item 1
- List item 2

`code example`
'''
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # HTML tags (not allowed)
        manifest['long_description'] = 'This has <b>HTML</b> tags'
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any('HTML tags' in e for e in errors))

        # Script tag (dangerous)
        manifest['long_description'] = 'This has <script>alert("xss")</script>'
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any('dangerous' in e for e in errors))

        # Excessive nesting (36+ spaces = 9+ nesting levels)
        manifest['long_description'] = ' ' * 40 + '- deeply nested item'
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any('excessive' in e for e in errors))

    def test_validate_markdown_in_long_description_i18n(self):
        """Test validation of markdown in long_description_i18n."""
        manifest = _valid_manifest(long_description='Valid **markdown**')

        # Valid markdown in i18n
        manifest['long_description_i18n'] = {'de': 'Gültig **markdown**', 'fr': 'Valide **markdown**'}
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # HTML in i18n (should fail)
        manifest['long_description_i18n']['de'] = 'HTML <b>tags</b>'
        errors = validate_manifest_dict(manifest)
        self.assertTrue(any('long_description_i18n.de' in e and 'HTML' in e for e in errors))

    def test_validate_markdown_parsing(self):
        """Test that markdown module is used to validate syntax."""
        # Skip test if markdown module is not available
        if render_markdown is None:
            self.skipTest("Markdown module not available")

        manifest = _valid_manifest()

        # Valid markdown with code blocks
        manifest['long_description'] = '''
Example code:

```python
def hello():
    print("world")
```

And a list:
- Item 1
- Item 2
'''
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [])

        # Test that complex markdown is actually parsed
        manifest['long_description'] = '''
# Heading

**Bold** and *italic* text.

- List item 1
- List item 2

```python
code block
```

[Link](https://example.com)
'''
        errors = validate_manifest_dict(manifest)
        self.assertEqual(errors, [], "Valid complex markdown should not produce errors")

    def test_validate_placeholder_uuids(self):
        """Test validation catches various placeholder/test UUIDs."""
        for uuid in PLACEHOLDER_UUIDS:
            with self.subTest(uuid=uuid):
                manifest = _valid_manifest(uuid=uuid)
                errors = validate_manifest_dict(manifest)
                self.assertTrue(any('placeholder/test UUID' in e for e in errors))

    def test_validate_all_known_placeholders_fail_entropy(self):
        """Test that all UUIDs in PLACEHOLDER_UUIDS fail Shannon entropy check."""
        for placeholder_uuid in PLACEHOLDER_UUIDS:
            with self.subTest(uuid=placeholder_uuid):
                self.assertTrue(
                    _is_placeholder_uuid(placeholder_uuid), f"UUID {placeholder_uuid} should be detected as placeholder"
                )

    def test_validate_real_uuids(self):
        """Test that real UUIDs are not flagged as placeholders."""
        real_uuids = [
            '74807b76-c451-419f-bbd4-42a78e2444a6',  # ReplayGain plugin
            '550e8400-e29b-41d4-a716-446655440000',
            'f47ac10b-58cc-4372-a567-0e02b2c3d479',
            '3d6f0e4a-8c9b-4f2e-a1d7-5b8c9e0f1a2b',
        ]
        for uuid in real_uuids:
            with self.subTest(uuid=uuid):
                manifest = _valid_manifest(uuid=uuid)
                errors = validate_manifest_dict(manifest)
                self.assertEqual(errors, [])

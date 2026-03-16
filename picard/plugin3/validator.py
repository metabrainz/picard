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

"""Standalone manifest validation with minimal dependencies.

This module can be copied to registry maintenance tools without
requiring the full Picard codebase.
"""

from collections import Counter
from collections.abc import Callable
import math
import re
import uuid


render_markdown: Callable[[str], str] | None = None

try:
    from markdown import markdown as render_markdown  # type: ignore[unresolved-import,no-redef]
except ImportError:
    pass


# Required MANIFEST.toml fields
REQUIRED_MANIFEST_FIELDS = ['uuid', 'name', 'description', 'api']

# String length constraints for MANIFEST.toml fields
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 200
MAX_LONG_DESCRIPTION_LENGTH = 2000

# UUID v4 regex pattern (RFC 4122)
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)

# Known placeholder/test UUIDs that should be rejected
PLACEHOLDER_UUIDS = {
    'a1b2c3d4-e5f6-4789-8b9c-1d2e3f4a5b6c',  # Sequential pattern
    '00000000-0000-4000-8000-000000000000',  # All zeros
    '12345678-1234-4234-8234-123456789abc',  # Simple sequential
    'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',  # All same character
    'deadbeef-dead-4eef-beef-deadbeefdead',  # Common test pattern
    'cafebabe-cafe-4abe-babe-cafebabecafe',  # Common test pattern
    'ffffffff-ffff-4fff-bfff-ffffffffffff',  # All F's
    '11111111-1111-4111-8111-111111111111',  # All 1's
}


def _is_valid_locale(locale):
    """Check if locale string is valid.

    Valid formats:
    - Language code: 'en', 'de', 'fr'
    - Language with region: 'en_US', 'pt_BR', 'zh_CN'

    Args:
        locale: Locale string to validate

    Returns:
        bool: True if valid locale format
    """
    # Pattern: 2-3 letter language code, optionally followed by underscore and 2 letter region
    pattern = r'^[a-z]{2,3}(_[A-Z]{2})?$'
    return bool(re.match(pattern, locale))


def _validate_markdown(text, field_name, errors):
    """Validate markdown text for security and formatting issues.

    Args:
        text: Markdown text to validate
        field_name: Name of field being validated (for error messages)
        errors: List to append errors to
    """
    # Check for HTML tags (not allowed)
    html_pattern = r'<[^>]+>'
    if re.search(html_pattern, text):
        errors.append(f"Field '{field_name}' contains HTML tags (not allowed, use Markdown only)")

    # Check for potentially dangerous patterns
    # Script tags (even in code blocks should be flagged)
    if '<script' in text.lower():
        errors.append(f"Field '{field_name}' contains potentially dangerous content (<script>)")

    # Check for excessive nesting (could indicate malformed markdown)
    # Look for lines with deep indentation before list markers
    for line in text.split('\n'):
        stripped = line.lstrip()
        if stripped and stripped[0] in '-*+':
            indent = len(line) - len(stripped)
            # Each nesting level is typically 2-4 spaces, so 36+ spaces = 9+ levels
            if indent >= 36:
                errors.append(f"Field '{field_name}' has excessive list nesting (max 9 levels)")
                break

    # If markdown module is available, try to parse it
    if render_markdown:
        try:
            render_markdown(text, output_format='html')
        except Exception as e:
            errors.append(f"Field '{field_name}' raised markdown exception: {e}")


def _validate_string_field(manifest_data, field_name, errors, min_len=None, max_len=None):
    """Validate that a field is a non-empty string if present.

    Args:
        manifest_data: Manifest dictionary
        field_name: Name of field to validate
        errors: List to append errors to
        min_len: Minimum length (optional)
        max_len: Maximum length (optional)
    """
    if field_name in manifest_data:
        value = manifest_data[field_name]
        if not isinstance(value, str):
            errors.append(f"Field '{field_name}' must be a string")
        elif not value.strip():
            errors.append(f"Field '{field_name}' must not be empty")
        elif min_len is not None or max_len is not None:
            length = len(value)
            if min_len and max_len and (length < min_len or length > max_len):
                errors.append(f"Field '{field_name}' must be {min_len}-{max_len} characters (got {length})")
            elif max_len and length > max_len:
                errors.append(f"Field '{field_name}' must be max {max_len} characters (got {length})")


def _validate_array_field(manifest_data, field_name, errors, item_type='item', check_items=None):
    """Validate that a field is a non-empty array if present.

    Args:
        manifest_data: Manifest dictionary
        field_name: Name of field to validate
        errors: List to append errors to
        item_type: Type name for error message (e.g., 'author', 'category')
        check_items: Optional function to validate each item
    """
    if field_name in manifest_data:
        value = manifest_data.get(field_name, [])
        if not isinstance(value, list):
            errors.append(f"Field '{field_name}' must be an array")
        elif len(value) == 0:
            errors.append(f"Field '{field_name}' must contain at least one {item_type} if present")
        elif check_items:
            for item in value:
                check_items(item, errors)


def _validate_locale_field(manifest_data, field_name, errors):
    """Validate that a field is a valid locale code if present.

    Args:
        manifest_data: Manifest dictionary
        field_name: Name of field to validate
        errors: List to append errors to
    """
    # First validate it's a non-empty string
    _validate_string_field(manifest_data, field_name, errors)

    # Then validate locale format if no errors so far
    if field_name in manifest_data and not any(field_name in e for e in errors):
        value = manifest_data[field_name]
        if not _is_valid_locale(value):
            errors.append(f"Field '{field_name}' must be a valid locale code (got '{value}')")


def _is_placeholder_uuid(uuid_str: str) -> bool:
    """Check if UUID appears to be a placeholder/test UUID.

    Uses Shannon entropy to detect low-randomness patterns that indicate
    manually typed or template UUIDs.

    Args:
        uuid_str: UUID string to check

    Returns:
        bool: True if UUID looks like a placeholder
    """
    uuid_lower = uuid_str.lower()

    # Check against known placeholders
    if uuid_lower in PLACEHOLDER_UUIDS:
        return True

    # Calculate Shannon entropy on hex digits only
    hex_only = uuid_lower.replace('-', '')
    if not hex_only:
        return True

    frequencies = Counter(hex_only)
    len_data = len(hex_only)
    entropy = -sum((count / len_data) * math.log2(count / len_data) for count in frequencies.values())

    # Threshold 2.8: Real UUIDs have ~3.5-4.0 entropy, placeholders typically < 2.8
    # Note: ~0.0003% of uuid4() values fall below 2.8, use generate_uuid() to avoid this.
    return entropy < 2.8


def _is_valid_uuid(uuid_str: str) -> tuple[bool, str | None]:
    """Check if UUID is valid and not a placeholder.

    Args:
        uuid_str: UUID string to check

    Returns:
        tuple: (is_valid, error_message)
    """
    if not UUID_PATTERN.match(uuid_str):
        return False, f"Field 'uuid' must be a valid UUID v4 (got '{uuid_str}')"

    if _is_placeholder_uuid(uuid_str):
        return False, (
            f"Field 'uuid' appears to be a placeholder/test UUID (got '{uuid_str}'). "
            "Generate a real UUID using 'picard-plugins --manifest', 'uuidgen', or Python's uuid.uuid4()"
        )

    return True, None


def generate_uuid() -> str:
    """Generate a UUID v4 that is guaranteed to pass manifest validation."""
    while True:
        result = str(uuid.uuid4())
        if not _is_placeholder_uuid(result):
            return result


def validate_manifest_dict(manifest_data):
    """Validate manifest dictionary (no Version dependency).

    Args:
        manifest_data: Parsed TOML data as dict

    Returns:
        list: Validation errors (empty if valid)
    """
    errors = []

    # Required fields
    for field in REQUIRED_MANIFEST_FIELDS:
        if not manifest_data.get(field):
            errors.append(f"Missing required field: {field}")

    # UUID validation (only if present, required check above catches missing)
    if 'uuid' in manifest_data:
        is_valid, error_msg = _is_valid_uuid(manifest_data['uuid'])
        if not is_valid:
            errors.append(error_msg)

    # String fields with length constraints
    _validate_string_field(manifest_data, 'name', errors, min_len=1, max_len=MAX_NAME_LENGTH)
    _validate_string_field(manifest_data, 'description', errors, min_len=1, max_len=MAX_DESCRIPTION_LENGTH)
    _validate_string_field(manifest_data, 'long_description', errors, max_len=MAX_LONG_DESCRIPTION_LENGTH)

    # Validate markdown in long_description
    if 'long_description' in manifest_data and isinstance(manifest_data['long_description'], str):
        _validate_markdown(manifest_data['long_description'], 'long_description', errors)

    _validate_string_field(manifest_data, 'version', errors)

    # API version validation
    def check_api_version(item, errs):
        if not isinstance(item, str) or not item.strip():
            errs.append(f"Invalid API version: {item}")

    _validate_array_field(manifest_data, 'api', errors, 'API version', check_items=check_api_version)

    # Locale validation
    _validate_locale_field(manifest_data, 'source_locale', errors)

    # Optional string fields
    _validate_string_field(manifest_data, 'license', errors)
    _validate_string_field(manifest_data, 'license_url', errors)
    _validate_string_field(manifest_data, 'homepage', errors)
    _validate_string_field(manifest_data, 'min_python_version', errors)

    # Optional array fields
    _validate_array_field(manifest_data, 'authors', errors, 'author')
    _validate_array_field(manifest_data, 'maintainers', errors, 'maintainer')
    _validate_array_field(manifest_data, 'categories', errors, 'category')

    # Empty i18n sections
    for section in ['name_i18n', 'description_i18n', 'long_description_i18n']:
        if section in manifest_data:
            value = manifest_data[section]
            if not value or (isinstance(value, dict) and len(value) == 0):
                errors.append(f"Section '{section}' is present but empty")

    # Validate markdown in long_description_i18n
    if 'long_description_i18n' in manifest_data:
        i18n_data = manifest_data['long_description_i18n']
        if isinstance(i18n_data, dict):
            for locale, text in i18n_data.items():
                if isinstance(text, str):
                    _validate_markdown(text, f'long_description_i18n.{locale}', errors)

    return errors

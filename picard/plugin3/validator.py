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

import re

from .constants import (
    MAX_DESCRIPTION_LENGTH,
    MAX_LONG_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    REQUIRED_MANIFEST_FIELDS,
    UUID_PATTERN,
)


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


def _validate_string_field(manifest_data, field_name, errors):
    """Validate that a field is a non-empty string if present.

    Args:
        manifest_data: Manifest dictionary
        field_name: Name of field to validate
        errors: List to append errors to
    """
    if field_name in manifest_data:
        value = manifest_data[field_name]
        if not isinstance(value, str):
            errors.append(f"Field '{field_name}' must be a string")
        elif not value.strip():
            errors.append(f"Field '{field_name}' must not be empty")


def _validate_array_field(manifest_data, field_name, errors, item_type='item'):
    """Validate that a field is a non-empty array if present.

    Args:
        manifest_data: Manifest dictionary
        field_name: Name of field to validate
        errors: List to append errors to
        item_type: Type name for error message (e.g., 'author', 'category')
    """
    if field_name in manifest_data:
        value = manifest_data.get(field_name, [])
        if not isinstance(value, list):
            errors.append(f"Field '{field_name}' must be an array")
        elif len(value) == 0:
            errors.append(f"Field '{field_name}' must contain at least one {item_type} if present")


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

    # UUID validation
    uuid = manifest_data.get('uuid', '')
    if uuid and not UUID_PATTERN.match(uuid):
        errors.append(f"Field 'uuid' must be a valid UUID v4 (got '{uuid}')")

    # Field type validation
    if manifest_data.get('name') and not isinstance(manifest_data['name'], str):
        errors.append("Field 'name' must be a string")

    if manifest_data.get('authors') and not isinstance(manifest_data['authors'], list):
        errors.append("Field 'authors' must be an array")

    if manifest_data.get('api') and not isinstance(manifest_data['api'], list):
        errors.append("Field 'api' must be an array")

    # String length validation
    name = manifest_data.get('name', '')
    if name and isinstance(name, str) and (len(name) < 1 or len(name) > MAX_NAME_LENGTH):
        errors.append(f"Field 'name' must be 1-{MAX_NAME_LENGTH} characters (got {len(name)})")

    description = manifest_data.get('description', '')
    if description and isinstance(description, str):
        if len(description) < 1 or len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(f"Field 'description' must be 1-{MAX_DESCRIPTION_LENGTH} characters (got {len(description)})")

    long_description = manifest_data.get('long_description', '')
    if long_description and isinstance(long_description, str):
        if len(long_description) > MAX_LONG_DESCRIPTION_LENGTH:
            errors.append(
                f"Field 'long_description' must be max {MAX_LONG_DESCRIPTION_LENGTH} characters (got {len(long_description)})"
            )

    # Version validation (basic string format check)
    if manifest_data.get('version'):
        version = manifest_data['version']
        if not isinstance(version, str) or not version.strip():
            errors.append("Field 'version' must be a non-empty string")

    # API version validation (basic check)
    if manifest_data.get('api'):
        for api_ver in manifest_data['api']:
            if not isinstance(api_ver, str) or not api_ver.strip():
                errors.append(f"Invalid API version: {api_ver}")

    # Source locale validation
    if 'source_locale' in manifest_data:
        source_locale = manifest_data['source_locale']
        if not isinstance(source_locale, str):
            errors.append("Field 'source_locale' must be a string")
        elif not source_locale.strip():
            errors.append("Field 'source_locale' must not be empty")
        elif not _is_valid_locale(source_locale):
            errors.append(f"Field 'source_locale' must be a valid locale code (got '{source_locale}')")

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

    return errors

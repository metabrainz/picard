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

from .constants import (
    MAX_DESCRIPTION_LENGTH,
    MAX_LONG_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    REQUIRED_MANIFEST_FIELDS,
    UUID_PATTERN,
)


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

    # Authors validation (optional field)
    if 'authors' in manifest_data:
        authors = manifest_data.get('authors', [])
        if not isinstance(authors, list):
            errors.append("Field 'authors' must be an array")
        elif len(authors) == 0:
            errors.append("Field 'authors' must contain at least one author if present")

    # Maintainers validation (optional field)
    if 'maintainers' in manifest_data:
        maintainers = manifest_data.get('maintainers', [])
        if not isinstance(maintainers, list):
            errors.append("Field 'maintainers' must be an array")
        elif len(maintainers) == 0:
            errors.append("Field 'maintainers' must contain at least one maintainer if present")

    # Categories - no validation, list is informational only
    # This allows forward/backward compatibility when categories change

    # Empty i18n sections
    for section in ['name_i18n', 'description_i18n', 'long_description_i18n']:
        if section in manifest_data:
            value = manifest_data[section]
            if not value or (isinstance(value, dict) and len(value) == 0):
                errors.append(f"Section '{section}' is present but empty")

    return errors

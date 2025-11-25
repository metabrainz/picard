# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023-2024 Philipp Wolfer
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

try:
    from tomllib import load as load_toml
except ImportError:
    from tomlkit import load as load_toml

from typing import (
    BinaryIO,
    Tuple,
)

from picard.version import (
    Version,
    VersionError,
)


class PluginManifest:
    """Provides access to the plugin metadata from a MANIFEST.toml file."""

    def __init__(self, module_name: str, manifest_fp: BinaryIO) -> None:
        self.module_name = module_name
        self._data = load_toml(manifest_fp)

    def name(self, locale: str = 'en') -> str:
        """Get plugin name, optionally translated."""
        i18n = self._data.get('name_i18n') or {}
        if locale in i18n:
            return i18n[locale]
        # Try language without region (e.g., 'de' from 'de_DE')
        lang = locale.split('_')[0]
        if lang in i18n:
            return i18n[lang]
        return self._data.get('name', '')

    @property
    def authors(self) -> Tuple[str]:
        authors = self._data.get('authors', [])
        return tuple(authors) if authors else tuple()

    def description(self, locale: str = 'en') -> str:
        """Get short description, optionally translated."""
        i18n = self._data.get('description_i18n') or {}
        if locale in i18n:
            return i18n[locale]
        # Try language without region
        lang = locale.split('_')[0]
        if lang in i18n:
            return i18n[lang]
        return self._data.get('description', '')

    def long_description(self, locale: str = 'en') -> str:
        """Get long description, optionally translated."""
        i18n = self._data.get('long_description_i18n') or {}
        if locale in i18n:
            return i18n[locale]
        # Try language without region
        lang = locale.split('_')[0]
        if lang in i18n:
            return i18n[lang]
        return self._data.get('long_description', '')

    @property
    def version(self) -> Version:
        try:
            return Version.from_string(self._data.get('version'))
        except VersionError:
            return Version(0, 0, 0)

    @property
    def api_versions(self) -> Tuple[Version]:
        versions = self._data.get('api')
        if not versions:
            return tuple()
        try:
            return tuple(Version.from_string(v) for v in versions)
        except VersionError:
            return tuple()

    @property
    def license(self) -> str:
        return self._data.get('license')

    @property
    def license_url(self) -> str:
        return self._data.get('license_url')

    def validate(self) -> list:
        """Validate manifest and return list of errors.

        Returns:
            List of error messages. Empty list if valid.
        """
        errors = []

        # Required fields
        required = ['name', 'version', 'description', 'api', 'authors', 'license', 'license_url']
        for field in required:
            if not self._data.get(field):
                errors.append(f"Missing required field: {field}")

        # Field type validation
        if self._data.get('name') and not isinstance(self._data['name'], str):
            errors.append("Field 'name' must be a string")

        if self._data.get('authors') and not isinstance(self._data['authors'], list):
            errors.append("Field 'authors' must be an array")

        if self._data.get('api') and not isinstance(self._data['api'], list):
            errors.append("Field 'api' must be an array")

        # String length validation
        name = self._data.get('name', '')
        if name and isinstance(name, str) and (len(name) < 1 or len(name) > 100):
            errors.append(f"Field 'name' must be 1-100 characters (got {len(name)})")

        description = self._data.get('description', '')
        if description and isinstance(description, str) and (len(description) < 1 or len(description) > 200):
            errors.append(f"Field 'description' must be 1-200 characters (got {len(description)})")

        long_description = self._data.get('long_description', '')
        if long_description and isinstance(long_description, str) and len(long_description) > 2000:
            errors.append(f"Field 'long_description' must be max 2000 characters (got {len(long_description)})")

        # Version validation
        if self._data.get('version'):
            try:
                Version.from_string(self._data['version'])
            except (VersionError, Exception) as e:
                errors.append(f"Invalid version format: {e}")

        # API version validation
        if self._data.get('api'):
            for api_ver in self._data['api']:
                try:
                    Version.from_string(api_ver)
                except (VersionError, Exception) as e:
                    errors.append(f"Invalid API version '{api_ver}': {e}")

        # Authors validation
        authors = self._data.get('authors', [])
        if authors and len(authors) == 0:
            errors.append("Field 'authors' must contain at least one author")

        return errors

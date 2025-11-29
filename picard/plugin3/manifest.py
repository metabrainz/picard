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

from picard.plugin3.validator import validate_manifest_dict
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

    @property
    def uuid(self) -> str:
        """Get plugin UUID."""
        return self._data.get('uuid', '')

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
        # Use standalone validator for basic checks
        errors = validate_manifest_dict(self._data)

        # Add Picard-specific validation (Version parsing)
        if self._data.get('version'):
            try:
                Version.from_string(self._data['version'])
            except (VersionError, Exception) as e:
                errors.append(f"Invalid version format: {e}")

        if self._data.get('api'):
            for api_ver in self._data['api']:
                try:
                    Version.from_string(api_ver)
                except (VersionError, Exception) as e:
                    errors.append(f"Invalid API version '{api_ver}': {e}")

        return errors

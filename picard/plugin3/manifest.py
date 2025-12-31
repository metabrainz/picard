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
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from typing import (
    BinaryIO,
    Optional,
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
        self._data = tomllib.load(manifest_fp)

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
    def authors(self) -> tuple[str]:
        authors = self._data.get('authors', [])
        return tuple(authors) if authors else tuple()

    @property
    def maintainers(self) -> tuple[str]:
        maintainers = self._data.get('maintainers', [])
        return tuple(maintainers) if maintainers else tuple()

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

    def _get_current_locale(self) -> str:
        """Get current locale from Picard's UI language setting or system locale."""
        from picard.config import get_config

        config = get_config()
        locale = config.setting['ui_language']
        if not locale:
            # Fall back to system locale if no UI language set
            from PyQt6 import QtCore

            locale = QtCore.QLocale.system().name()
        return locale

    def name_i18n(self, locale: str | None = None) -> str:
        """Get plugin name with automatic locale detection."""
        if locale is None:
            locale = self._get_current_locale()
        return self.name(locale)

    def description_i18n(self, locale: str | None = None) -> str:
        """Get description with automatic locale detection."""
        if locale is None:
            locale = self._get_current_locale()
        return self.description(locale)

    def long_description_i18n(self, locale: str | None = None) -> str:
        """Get long description with automatic locale detection."""
        if locale is None:
            locale = self._get_current_locale()
        return self.long_description(locale)

    @property
    def version(self) -> Optional[Version]:
        version_str = self._data.get('version')
        if not version_str:
            return None
        try:
            return Version.from_string(version_str)
        except VersionError:
            return None

    @property
    def api_versions(self) -> tuple[Version, ...]:
        versions = self._data.get('api')
        if not versions:
            return ()
        try:
            return tuple(Version.from_string(v) for v in versions)
        except VersionError:
            return ()

    @property
    def license(self) -> str:
        return self._data.get('license', '')

    @property
    def license_url(self) -> str:
        return self._data.get('license_url', '')

    @property
    def source_locale(self) -> str:
        """Get source locale for translations, defaults to 'en'."""
        return self._data.get('source_locale', 'en')

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


def generate_manifest_template():
    """Generate a MANIFEST.toml template with a new UUID.

    Returns:
        str: MANIFEST.toml template content
    """
    import uuid

    from picard.plugin3.constants import CATEGORIES

    generated_uuid = str(uuid.uuid4())
    categories_str = ', '.join(f'"{c}"' for c in CATEGORIES)

    return f'''# MANIFEST.toml Template
# See https://picard-docs.musicbrainz.org/en/extending/plugins.html

# Required fields
uuid = "{generated_uuid}"  # Generated UUID - keep this value
name = "My Plugin Name"
description = "Short one-line description (1-200 characters)"
api = ["3.0"]

# Optional fields
# authors = ["Your Name"]
# maintainers = ["Your Name"]
# license = "GPL-2.0-or-later"
# license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
# long_description = """
# Detailed multi-line description (1-2000 characters).
# Explain features, requirements, usage notes, etc.
# """
# categories = [{categories_str}]
# homepage = "https://github.com/username/plugin-name"
# min_python_version = "3.9"
# source_locale = "en"  # Source language for translations (default: "en")

# Translation tables (optional)
# [name_i18n]
# de = "Mein Plugin Name"
# fr = "Mon nom de plugin"

# [description_i18n]
# de = "Kurze einzeilige Beschreibung"
# fr = "Courte description sur une ligne"

# [long_description_i18n]
# de = """
# Detaillierte mehrzeilige Beschreibung...
# """
# fr = """
# Description détaillée sur plusieurs lignes...
# """
'''

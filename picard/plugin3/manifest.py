# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2023-2026 Philipp Wolfer
# Copyright (C) 2025-2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


try:
    import tomllib  # type: ignore[unresolved-import]
except (ImportError, ModuleNotFoundError):
    import tomli as tomllib  # type: ignore[no-redef]

from typing import BinaryIO

from picard.plugin3.constants import (
    CATEGORIES,
    DEFAULT_SOURCE_LOCALE,
)
from picard.plugin3.validator import (
    generate_uuid,
    validate_manifest_dict,
)
from picard.version import (
    Version,
    VersionError,
)


class PluginManifest:
    """Provides access to the plugin metadata from a MANIFEST.toml file."""

    def __init__(self, module_name: str, manifest_fp: BinaryIO) -> None:
        self.module_name = module_name
        self._data = tomllib.load(manifest_fp)

    def _localized(self, i18n_field: str, plain_field: str, locale: str) -> str:
        """Return a localized string field, tolerating malformed manifest data.

        The ``*_i18n`` section and its values come from a plugin-authored
        MANIFEST.toml and may have the wrong type (the validator only rejects
        empty sections). Guard that the section is a dict and the resolved
        value is a string; otherwise fall back to the plain field. Always
        returns a string.
        """
        i18n = self._data.get(i18n_field)
        if isinstance(i18n, dict):
            value = i18n.get(locale)
            if not isinstance(value, str):
                # Try language without region (e.g., 'de' from 'de_DE')
                value = i18n.get(locale.split('_')[0])
            if isinstance(value, str):
                return value
        plain = self._data.get(plain_field, '')
        return plain if isinstance(plain, str) else ''

    def name(self, locale: str = 'en') -> str:
        """Get plugin name, optionally translated."""
        return self._localized('name_i18n', 'name', locale)

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
        return self._localized('description_i18n', 'description', locale)

    def long_description(self, locale: str = 'en') -> str:
        """Get long description, optionally translated."""
        return self._localized('long_description_i18n', 'long_description', locale)

    def _get_current_locale(self) -> str:
        """Get current locale from Picard's UI language setting or system locale."""
        # Avoid init-order issue: config not available at import time
        from picard.config import get_config

        config = get_config()
        if config is None:
            return 'en'
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
    def version(self) -> Version | None:
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
    def report_bugs_to(self) -> str:
        return self._data.get('report_bugs_to', '')

    @property
    def source_locale(self) -> str:
        """Get source locale for translations, defaults to 'en'."""
        return self._data.get('source_locale', DEFAULT_SOURCE_LOCALE)

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
            except Exception as e:
                errors.append(f"Invalid version format: {e}")

        if self._data.get('api'):
            for api_ver in self._data['api']:
                try:
                    Version.from_string(api_ver)
                except Exception as e:
                    errors.append(f"Invalid API version '{api_ver}': {e}")

        return errors


def generate_manifest_template():
    """Generate a MANIFEST.toml template with a new UUID.

    Returns:
        str: MANIFEST.toml template content
    """
    generated_uuid = generate_uuid()
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
# report_bugs_to = "https://github.com/username/plugin-name/issues"
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

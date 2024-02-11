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
    """Provides access to the plugin metadata from a MANIFEST.toml file.
    """

    def __init__(self, module_name: str, manifest_fp: BinaryIO) -> None:
        self.module_name = module_name
        self._data = load_toml(manifest_fp)

    @property
    def name(self) -> str:
        return self._data.get('name')

    @property
    def author(self) -> str:
        return self._data.get('author')

    def description(self, preferred_language: str = 'en') -> str:
        descriptions = self._data.get('description') or {}
        return descriptions.get(preferred_language, descriptions.get('en', ''))

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
        return self._data.get('license-url')

    @property
    def user_guide_url(self) -> str:
        return self._data.get('user-guide-url')

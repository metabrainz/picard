# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer, Laurent Monin
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

"""Plugin validation utilities."""

from pathlib import Path


class PluginValidation:
    """Handles plugin validation operations."""

    @staticmethod
    def validate_manifest(manifest):
        """Validate manifest and raise PluginManifestInvalidError if invalid.

        Args:
            manifest: PluginManifest to validate

        Raises:
            PluginManifestInvalidError: If manifest has validation errors
        """
        from picard.plugin3.manager import PluginManifestInvalidError

        errors = manifest.validate()
        if errors:
            raise PluginManifestInvalidError(errors)

    @staticmethod
    def read_and_validate_manifest(path, source_description):
        """Read MANIFEST.toml from path and validate it.

        Args:
            path: Directory path containing MANIFEST.toml
            source_description: Description of source for error messages (e.g., URL or path)

        Returns:
            PluginManifest: Validated manifest

        Raises:
            PluginManifestNotFoundError: If MANIFEST.toml doesn't exist
            PluginManifestInvalidError: If manifest has validation errors
        """
        from picard.plugin3.manager import PluginManifestNotFoundError
        from picard.plugin3.manifest import PluginManifest

        manifest_path = Path(path) / 'MANIFEST.toml'
        if not manifest_path.exists():
            raise PluginManifestNotFoundError(source_description)

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest(Path(path).name, f)
        PluginValidation.validate_manifest(manifest)
        return manifest

    @staticmethod
    def get_plugin_uuid(plugin):
        """Get plugin UUID, raising PluginNoUUIDError if not available.

        Args:
            plugin: Plugin object

        Returns:
            str: Plugin UUID

        Raises:
            PluginNoUUIDError: If plugin has no UUID
        """
        from picard.plugin3.manager import PluginNoUUIDError

        # Lazy-load manifest if not already loaded
        if not plugin.manifest:
            manifest_path = plugin.local_path / 'MANIFEST.toml'
            if manifest_path.exists():
                plugin.read_manifest()

        if not plugin.manifest or not plugin.manifest.uuid:
            raise PluginNoUUIDError(plugin.plugin_id)
        return plugin.manifest.uuid

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024-2025 Philipp Wolfer
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


class PluginFinder:
    """Handles plugin finding operations."""

    def __init__(self, manager):
        self.manager = manager

    def find_plugin(self, identifier):
        """Find a plugin by Plugin ID, display name, UUID, registry ID, or any prefix.

        Args:
            identifier: Plugin ID, display name, UUID, registry ID, or prefix of any

        Returns:
            Plugin object, None if not found, or 'multiple' if ambiguous
        """
        identifier_lower = identifier.lower()
        exact_matches = []
        prefix_matches = []

        for plugin in self.manager.plugins:
            # Collect all possible identifiers for this plugin
            identifiers = []

            # Plugin ID (case-insensitive)
            identifiers.append(plugin.plugin_id.lower())

            # UUID (case-insensitive)
            if plugin.uuid:
                identifiers.append(str(plugin.uuid).lower())

            # Display name (case-insensitive)
            if plugin.manifest:
                identifiers.append(plugin.manifest.name().lower())

            # Registry ID (case-insensitive) - lookup dynamically from current registry
            try:
                registry_id = self.manager.get_plugin_registry_id(plugin)
                if registry_id:
                    identifiers.append(registry_id.lower())
            except Exception:
                pass

            # Check for exact or prefix match
            for id_value in identifiers:
                if id_value == identifier_lower:
                    exact_matches.append(plugin)
                    break  # One exact match is enough
                elif id_value.startswith(identifier_lower):
                    prefix_matches.append(plugin)
                    break  # One prefix match is enough

        # Exact matches take priority
        if len(exact_matches) == 1:
            return exact_matches[0]
        elif len(exact_matches) > 1:
            return 'multiple'

        # Fall back to prefix matches
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        elif len(prefix_matches) > 1:
            return 'multiple'

        return None

    def _find_plugin_by_url(self, url):
        """Find plugin metadata by URL."""
        return self.manager._metadata.find_plugin_by_url(url)

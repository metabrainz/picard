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

import re

from picard import api_versions_tuple, log
from picard.util import parse_versioning_scheme
from picard.version import Version


def _strip_to_first_digit(tag):
    """Strip non-digit prefix to get version number."""
    match = re.search(r'\d', tag)
    return tag[match.start() :] if match else tag


def _parse_version_safely(tag):
    """Parse version string safely, returning None on failure."""
    try:
        return Version.from_string(_strip_to_first_digit(tag))
    except Exception:
        return None


class PluginRegistryManager:
    """Handles plugin registry operations."""

    def __init__(self, manager):
        self.manager = manager

    def search_registry_plugins(self, query=None, category=None, trust_level=None):
        """Search registry plugins with optional filters.

        Args:
            query: Search query (searches name, description, id)
            category: Filter by category
            trust_level: Filter by trust level

        Returns:
            list: Filtered plugin dictionaries from registry
        """
        plugins = self.manager._registry.list_plugins(category=category, trust_level=trust_level)

        if not query:
            return plugins

        query_lower = query.lower()
        return [
            p
            for p in plugins
            if query_lower in p.name.lower() or query_lower in p.description.lower() or query_lower in p.id.lower()
        ]

    def find_similar_plugin_ids(self, query, max_results=10):
        """Find similar plugin IDs for suggestions.

        Args:
            query: Partial plugin ID to search for
            max_results: Maximum number of suggestions to return

        Returns:
            list: Plugin dictionaries with similar IDs (empty if too many matches)
        """
        all_plugins = self.manager._registry.list_plugins()
        matches = [p for p in all_plugins if query.lower() in p['id'].lower()]
        return matches if 1 <= len(matches) <= max_results else []

    def get_registry_plugin_latest_version(self, plugin):
        """Get latest version tag for a registry plugin.

        Args:
            plugin: RegistryPlugin object

        Returns:
            Version string (latest tag or empty string)
        """
        if not plugin.versioning_scheme or not plugin.git_url:
            return ''

        try:
            tags = self._fetch_version_tags(plugin.git_url, plugin.versioning_scheme)
            return tags[0] if tags else ''
        except Exception:
            return ''

    def select_ref_for_plugin(self, plugin):
        """Select appropriate ref for plugin based on versioning scheme or Picard API version.

        Args:
            plugin: RegistryPlugin object

        Returns:
            str: Selected ref name, or None if no refs specified
        """
        versioning_scheme = plugin.versioning_scheme
        url = plugin.git_url
        refs = plugin.refs

        # Check for versioning_scheme first
        if versioning_scheme:
            if url:
                tags = self._fetch_version_tags(url, versioning_scheme)
                if tags:
                    # Return latest tag
                    return tags[0]
                else:
                    log.warning('No version tags found for %s with scheme %s', url, versioning_scheme)
                    # Fall through to ref selection

        # Original ref selection logic
        if not refs:
            return None

        # Get current Picard API version as string (e.g., "3.0")
        current_api = '.'.join(map(str, api_versions_tuple[:2]))

        # Find first compatible ref
        for ref in refs:
            min_api = ref.get('min_api_version')
            max_api = ref.get('max_api_version')

            # Skip if below minimum
            if min_api and current_api < min_api:
                continue

            # Skip if above maximum
            if max_api and current_api > max_api:
                continue

            # Compatible ref found
            return ref['name']

        # No compatible ref found, use first (default)
        return refs[0]['name']

    def _sort_tags(self, tags, versioning_scheme):
        """Sort tags based on versioning scheme.

        Args:
            tags: List of tag names
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            list: Sorted tags (newest first)
        """

        if versioning_scheme == 'semver':
            # Use picard.version for proper semver sorting
            try:
                return sorted(
                    tags, key=lambda t: _parse_version_safely(t) or Version.from_string('0.0.0'), reverse=True
                )
            except Exception as e:
                log.warning('Failed to parse semver tags: %s', e)
                return sorted(tags, key=_strip_to_first_digit, reverse=True)
        elif versioning_scheme == 'calver':
            # CalVer: YYYY.MM.DD format, sort by stripped version (newest first)
            return sorted(tags, key=_strip_to_first_digit, reverse=True)
        else:
            # Custom regex: try version parsing, fall back to natural sort
            def sort_key(tag):
                version = _parse_version_safely(tag)
                if version:
                    return (0, version)

                # Natural sort: split into text and number parts
                stripped = _strip_to_first_digit(tag)
                parts = []
                for part in re.split(r'(\d+)', stripped):
                    if part.isdigit():
                        parts.append((0, int(part)))
                    else:
                        parts.append((1, part))
                return (1, parts)

            return sorted(tags, key=sort_key, reverse=True)

    def _fetch_version_tags(self, url, versioning_scheme):
        """Fetch and filter version tags from repository.

        Args:
            url: Git repository URL
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            list: Sorted list of version tags (newest first), or empty list on error
        """
        # Parse versioning scheme
        pattern = parse_versioning_scheme(versioning_scheme)
        if not pattern:
            return []

        # Fetch all refs from repository
        all_refs = self.manager.fetch_all_git_refs(url)
        if not all_refs:
            return []

        # Filter and sort tags
        tags = [tag['name'] for tag in all_refs.get('tags', []) if pattern.match(tag['name'])]
        tags = self._sort_tags(tags, versioning_scheme)

        return tags

    def _find_newer_version_tag(self, url, current_tag, versioning_scheme):
        """Find newer version tag for plugin with versioning_scheme.

        Args:
            url: Git repository URL
            current_tag: Current version tag
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            str: Newer version tag, or None if no newer version found
        """
        tags = self._fetch_version_tags(url, versioning_scheme)
        if not tags:
            return None

        # Use version parsing for semver/calver, lexicographic for custom regex
        if versioning_scheme in ('semver', 'calver'):
            try:
                current_version = _parse_version_safely(current_tag)
                if not current_version:
                    return None

                for tag in tags:
                    tag_version = _parse_version_safely(tag)
                    if tag_version and tag_version > current_version:
                        return tag
                return None
            except Exception:
                pass

        # Fallback to lexicographic comparison for custom regex
        for tag in tags:
            if tag > current_tag:
                return tag

        return None

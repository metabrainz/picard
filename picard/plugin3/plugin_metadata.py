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

"""Plugin metadata storage and retrieval."""

from picard import log
from picard.plugin3.config_ops import ConfigOperations


class PluginMetadataManager:
    """Manages plugin metadata storage and retrieval."""

    def __init__(self, config, registry):
        self._config = config
        self._registry = registry

    def get_plugin_metadata(self, uuid: str):
        """Get metadata for a plugin by UUID."""
        metadata = ConfigOperations.get_config_value('plugins3', 'metadata', default={})
        # Handle both dict (new format) and list (old format) for backwards compatibility
        if isinstance(metadata, dict):
            return metadata.get(str(uuid))
        # Legacy list format
        for item in metadata:
            if item.get('uuid') == str(uuid):
                return item
        return None

    def save_plugin_metadata(self, metadata):
        """Save or update plugin metadata.

        Args:
            metadata: PluginMetadata object with uuid, url, ref, commit, etc.
        """
        metadata_dict_all = ConfigOperations.get_config_value('plugins3', 'metadata', default={})

        # Handle legacy list format - convert to dict
        if isinstance(metadata_dict_all, list):
            metadata_dict_all = {item['uuid']: item for item in metadata_dict_all if 'uuid' in item}

        # Convert metadata to dict and store by UUID
        metadata_dict_all[metadata.uuid] = metadata.to_dict()

        ConfigOperations.set_config_value('plugins3', 'metadata', value=metadata_dict_all)

    def find_plugin_by_url(self, url: str):
        """Find plugin metadata by URL.

        Args:
            url: Git repository URL

        Returns:
            dict: Plugin metadata or None if not found
        """
        metadata = ConfigOperations.get_config_value('plugins3', 'metadata', default={})
        # Handle both dict (new format) and list (old format)
        if isinstance(metadata, dict):
            for item in metadata.values():
                if item.get('url') == url:
                    return item
        else:
            # Legacy list format
            for item in metadata:
                if item.get('url') == url:
                    return item
        return None

    def check_redirects(self, old_url, old_uuid):
        """Check if plugin was redirected to new URL.

        Args:
            old_url: Original URL
            old_uuid: Original UUID

        Returns:
            tuple: (new_url, new_uuid, redirected) where redirected is True if changed
        """
        # Check if UUID exists in registry with different URL
        registry_plugin = self._registry.find_plugin(uuid=old_uuid)
        if registry_plugin:
            new_url = registry_plugin.get('git_url')
            if new_url and new_url != old_url:
                log.info('Plugin %s redirected from %s to %s', old_uuid, old_url, new_url)
                return new_url, old_uuid, True

        # Check if URL exists in registry with different UUID
        registry_plugin = self._registry.find_plugin(url=old_url)
        if registry_plugin:
            new_uuid = registry_plugin.get('uuid')
            if new_uuid and new_uuid != old_uuid:
                log.info('Plugin at %s changed UUID from %s to %s', old_url, old_uuid, new_uuid)
                return old_url, new_uuid, True

        return old_url, old_uuid, False

    def get_original_metadata(self, metadata, redirected, old_url, old_uuid):
        """Get original metadata before redirect.

        Args:
            metadata: Current metadata dict
            redirected: Whether plugin was redirected
            old_url: Original URL
            old_uuid: Original UUID

        Returns:
            tuple: (original_url, original_uuid) from metadata or old values if not found
        """
        if not redirected:
            return old_url, old_uuid

        # Try to find metadata by old UUID
        old_metadata = self.get_plugin_metadata(old_uuid)
        if old_metadata:
            return old_metadata.get('url', old_url), old_metadata.get('uuid', old_uuid)

        # Try to find metadata by old URL
        old_metadata = self.find_plugin_by_url(old_url)
        if old_metadata:
            return old_metadata.get('url', old_url), old_metadata.get('uuid', old_uuid)

        return old_url, old_uuid

    def get_plugin_registry_id(self, plugin):
        """Get registry ID for a plugin by looking it up in the current registry.

        Args:
            plugin: Plugin to get registry ID for

        Returns:
            str: Registry ID or None if not in registry
        """
        if not plugin.manifest or not plugin.manifest.uuid:
            return None

        # Look up plugin in registry by UUID
        registry_plugin = self._registry.find_plugin(uuid=str(plugin.manifest.uuid))
        if registry_plugin:
            return registry_plugin.get('id')

        return None

    def get_plugin_refs_info(self, identifier, plugins):
        """Get plugin refs information from identifier (smart detection).

        Args:
            identifier: Plugin name, registry ID, UUID, or git URL
            plugins: List of installed plugins

        Returns:
            dict with keys:
                - url: Git URL
                - current_ref: Current ref (if installed)
                - current_commit: Current commit (if installed)
                - registry_id: Registry ID (if in registry)
                - plugin: Plugin object (if installed)
                - registry_plugin: Registry plugin data (if in registry)
            or None if not found
        """
        # Try to find installed plugin first
        plugin = None
        for p in plugins:
            registry_id = self.get_plugin_registry_id(p)
            if (
                p.plugin_id == identifier
                or (p.manifest and p.manifest.name() == identifier)
                or (p.manifest and str(p.manifest.uuid) == identifier)
                or registry_id == identifier
            ):
                plugin = p
                break

        if plugin:
            # Plugin is installed
            if not plugin.manifest:
                return None

            metadata = self.get_plugin_metadata(plugin.manifest.uuid)
            if not metadata or not metadata.get('url'):
                return None

            url = metadata['url']
            current_ref = metadata.get('ref')
            current_commit = metadata.get('commit')
            registry_id = self.get_plugin_registry_id(plugin)

            # Detect current ref from local git repo (overrides metadata)
            if plugin.local_path:
                try:
                    import pygit2

                    repo = pygit2.Repository(str(plugin.local_path))
                    current_commit = str(repo.head.target)

                    # Check if current commit matches a tag (prefer tag over branch)
                    current_ref = None
                    for ref_name in repo.references:
                        if ref_name.startswith('refs/tags/'):
                            tag_name = ref_name[10:]
                            if tag_name.endswith('^{}'):
                                continue
                            ref = repo.references[ref_name]
                            target = ref.peel()
                            if str(target.id) == current_commit:
                                current_ref = tag_name
                                break

                    # If no tag found, use branch name
                    if not current_ref and not repo.head_is_detached:
                        current_ref = repo.head.shorthand
                except Exception:
                    pass  # Ignore errors, use metadata values
        else:
            # Not installed - try registry ID, UUID, or URL
            if '://' in identifier or '/' in identifier:
                # Looks like a URL
                url = identifier
                registry_id = self._registry.get_registry_id(url=url)
                current_ref = None
                current_commit = None
            else:
                # Try as registry ID or UUID
                registry_plugin = self._registry.find_plugin(plugin_id=identifier)
                if not registry_plugin:
                    # Try as UUID
                    registry_plugin = self._registry.find_plugin(uuid=identifier)

                if not registry_plugin:
                    return None

                url = registry_plugin['git_url']
                registry_id = registry_plugin.get('id', identifier)
                current_ref = None
                current_commit = None

        # Get registry data if available
        registry_plugin = self._registry.find_plugin(plugin_id=registry_id) if registry_id else None

        return {
            'url': url,
            'current_ref': current_ref,
            'current_commit': current_commit,
            'registry_id': registry_id,
            'plugin': plugin,
            'registry_plugin': registry_plugin,
        }

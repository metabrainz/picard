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

from dataclasses import asdict, dataclass

from picard import log
from picard.config import get_config


@dataclass
class PluginMetadata:
    """Plugin metadata stored in config."""

    url: str
    ref: str
    commit: str
    name: str = ''
    uuid: str | None = None
    original_url: str | None = None
    original_uuid: str | None = None

    @classmethod
    def from_dict(cls, data: dict):
        """Create PluginMetadata from dict, filtering unknown fields."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self):
        """Convert to dict for config storage, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class PluginMetadataManager:
    """Manages plugin metadata storage and retrieval."""

    def __init__(self, registry):
        self._registry = registry

    def get_plugin_metadata(self, uuid: str):
        """Get metadata for a plugin by UUID.

        Returns:
            PluginMetadata object or None if not found
        """
        metadata_dict = get_config().setting['plugins3_metadata'].get(str(uuid))
        if not metadata_dict:
            return None
        return PluginMetadata.from_dict(metadata_dict)

    def save_plugin_metadata(self, metadata):
        """Save or update plugin metadata.

        Args:
            metadata: PluginMetadata object with uuid, url, ref, commit, etc.
        """
        config = get_config()
        # Get the current dict, modify it, and set it back to trigger save
        metadata_dict = config.setting['plugins3_metadata'] or {}
        metadata_dict[metadata.uuid] = metadata.to_dict()
        config.setting['plugins3_metadata'] = metadata_dict
        # Force write to disk immediately (if sync is available)
        if hasattr(config, 'sync'):
            config.sync()

    def find_plugin_by_url(self, url: str):
        """Find plugin metadata by URL.

        Args:
            url: Git repository URL

        Returns:
            PluginMetadata: Plugin metadata or None if not found
        """
        metadata = get_config().setting['plugins3_metadata']
        # Handle both dict (new format) and list (old format)
        if isinstance(metadata, dict):
            for item in metadata.values():
                if item.get('url') == url:
                    return PluginMetadata.from_dict(item)
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
            return old_metadata.url or old_url, old_metadata.uuid or old_uuid

        # Try to find metadata by old URL
        old_metadata = self.find_plugin_by_url(old_url)
        if old_metadata:
            return old_metadata.url or old_url, old_metadata.uuid or old_uuid

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
            url = metadata.url if metadata else None

            # If no URL in metadata, try to get from registry
            if not url:
                registry_plugin = self._registry.find_plugin(uuid=str(plugin.manifest.uuid))
                if not registry_plugin:
                    return None
                url = registry_plugin['git_url']

            current_ref = metadata.ref if metadata else None
            current_commit = metadata.commit if metadata else None
            registry_id = self.get_plugin_registry_id(plugin)

            # Detect current ref from local git repo (overrides metadata)
            if plugin.local_path:
                try:
                    from picard.plugin3.git_factory import git_backend

                    backend = git_backend()
                    repo = backend.create_repository(plugin.local_path)
                    current_commit = repo.get_head_target()

                    # Check if current commit matches a tag (prefer tag over branch)
                    current_ref = None
                    for ref_name in repo.list_references():
                        if ref_name.startswith('refs/tags/'):
                            tag_name = ref_name[10:]
                            if tag_name.endswith('^{}'):
                                continue
                            try:
                                obj = repo.revparse_single(ref_name)
                                target = repo.peel_to_commit(obj)
                                if target.id == current_commit:
                                    current_ref = tag_name
                                    break
                            except Exception:
                                # Skip invalid tags and continue to next one
                                continue  # nosec try_except_continue

                    # If no tag found, use branch name
                    if not current_ref and not repo.is_head_detached():
                        current_ref = repo.get_head_shorthand()
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

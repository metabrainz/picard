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
from typing import TYPE_CHECKING

from picard import log
from picard.config import get_config
from picard.git.backend import GitRef, GitRefType
from picard.git.factory import git_backend


if TYPE_CHECKING:
    from picard.plugin3.plugin import Plugin


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
    ref_type: str | None = None  # 'tag' or 'branch' to indicate installation method
    git_ref: GitRef | None = None  # New GitRef object (preferred over ref/ref_type)

    def to_dict(self):
        """Convert to dict for config storage, excluding None values."""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        # Serialize git_ref to tuple for storage
        if self.git_ref:
            data['git_ref_tuple'] = self.git_ref.to_tuple()
        data.pop('git_ref', None)  # Remove non-serializable GitRef object
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Create PluginMetadata from dict, reconstructing GitRef from tuple."""
        # Reconstruct GitRef from tuple if present
        git_ref = None
        if 'git_ref_tuple' in data:
            git_ref = GitRef.from_tuple(data.pop('git_ref_tuple'))

        # Filter unknown fields and create instance
        filtered_data = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        instance = cls(**filtered_data)
        instance.git_ref = git_ref
        return instance

    def get_git_ref(self):
        """Get GitRef object, preferring stored GitRef over reconstructed from ref/ref_type."""
        if self.git_ref:
            return self.git_ref

        # Reconstruct GitRef from legacy ref/ref_type data
        if self.ref or self.commit:
            # Ensure we always store full canonical ref names in GitRef
            if self.ref:
                if self.ref.startswith('refs/'):
                    # Already a full name, use as-is
                    full_name = self.ref
                else:
                    # Short name, construct full name based on ref_type
                    if self.ref_type == 'tag':
                        full_name = f"refs/tags/{self.ref}"
                    elif self.ref_type == 'branch':
                        full_name = f"refs/heads/{self.ref}"
                    else:
                        # Unknown type, assume it's a short name and guess
                        if self.ref.startswith('v') or '.' in self.ref:
                            full_name = f"refs/tags/{self.ref}"
                        else:
                            full_name = f"refs/heads/{self.ref}"
            else:
                # Only commit, no ref name
                full_name = self.commit

            # Determine ref_type from full name if not already set
            if self.ref_type == 'tag':
                ref_type = GitRefType.TAG
            elif self.ref_type == 'branch':
                ref_type = GitRefType.BRANCH
            elif full_name.startswith('refs/tags/'):
                ref_type = GitRefType.TAG
            elif full_name.startswith('refs/heads/'):
                ref_type = GitRefType.BRANCH
            else:
                ref_type = None

            return GitRef(name=full_name, target=self.commit, ref_type=ref_type)

        return GitRef(name='', target='')


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
            new_url = registry_plugin.git_url
            if new_url and new_url != old_url:
                log.info('Plugin %s redirected from %s to %s', old_uuid, old_url, new_url)
                return new_url, old_uuid, True

        # Check if URL exists in registry with different UUID
        registry_plugin = self._registry.find_plugin(url=old_url)
        if registry_plugin:
            new_uuid = registry_plugin.uuid
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
        if not plugin.uuid:
            return None

        # Look up plugin in registry by UUID
        registry_plugin = self._registry.find_plugin(uuid=str(plugin.uuid))
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
        # Initialize variables
        metadata = None
        current_ref = None
        current_commit = None
        current_ref_type = None

        # Try to find installed plugin first
        plugin = None
        for p in plugins:
            registry_id = self.get_plugin_registry_id(p)
            if (
                p.plugin_id == identifier
                or (p.manifest and p.manifest.name() == identifier)
                or (p.uuid and str(p.uuid) == identifier)
                or registry_id == identifier
            ):
                plugin = p
                break

        if plugin:
            # Plugin is installed
            if not plugin.manifest:
                return None

            metadata = self.get_plugin_metadata(plugin.uuid)
            url = metadata.url if metadata else None

            # If no URL in metadata, try to get from registry
            if not url:
                registry_plugin = self._registry.find_plugin(uuid=str(plugin.uuid))
                if not registry_plugin:
                    return None
                url = registry_plugin.git_url

            registry_id = self.get_plugin_registry_id(plugin)

            # Get current ref info from local repo
            current_ref, current_commit = self._get_current_ref_info(plugin)
            if not current_ref:
                if metadata:
                    git_ref = metadata.get_git_ref()
                    current_ref = git_ref.shortname if git_ref.shortname else None
                    current_commit = metadata.commit
            else:
                # Prefer metadata ref over detected ref for consistency
                if metadata and metadata.ref:
                    git_ref = metadata.get_git_ref()
                    current_ref = git_ref.shortname if git_ref.shortname else metadata.ref

            # Set ref type from metadata
            current_ref_type = metadata.ref_type if metadata else None

        else:
            # Not installed - try registry ID, UUID, or URL
            if '://' in identifier or '/' in identifier:
                # Looks like a URL
                url = identifier
                registry_id = self._registry.get_registry_id(url=url)
            else:
                # Try as registry ID or UUID
                registry_plugin = self._registry.find_plugin(plugin_id=identifier)
                if not registry_plugin:
                    # Try as UUID
                    registry_plugin = self._registry.find_plugin(uuid=identifier)

                if not registry_plugin:
                    return None

                url = registry_plugin.git_url
                registry_id = registry_plugin.id or identifier

        # Get registry data if available
        registry_plugin = self._registry.find_plugin(plugin_id=registry_id) if registry_id else None

        return {
            'url': url,
            'current_ref': current_ref,
            'current_commit': current_commit,
            'current_ref_type': current_ref_type,
            'registry_id': registry_id,
            'plugin': plugin,
            'registry_plugin': registry_plugin,
        }

    def _get_current_ref_info(self, plugin: 'Plugin | None'):
        """Get current ref name and commit for installed plugin.

        Returns:
            tuple: (ref_name, commit_id) or (None, None) if not available
        """
        if not plugin or not plugin.local_path:
            return None, None

        try:
            backend = git_backend()
            with backend.create_repository(plugin.local_path) as repo:
                current_commit = repo.get_head_target()

                # Check if current commit matches a tag (prefer tag over branch)
                for git_ref in repo.list_references():
                    if git_ref.ref_type == GitRefType.TAG:
                        target = repo.revparse_to_commit(git_ref.name)
                        if target.id == current_commit:
                            return git_ref.shortname, current_commit

                # No tag match, check if on a branch
                if not repo.is_head_detached():
                    current_branch = repo.get_head_shorthand()
                    return current_branch, current_commit
                else:
                    # Detached HEAD
                    return current_commit, current_commit

        except Exception:
            return None, None

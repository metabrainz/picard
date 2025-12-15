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

import gc
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import TYPE_CHECKING, NamedTuple

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
)

from picard import log


if TYPE_CHECKING:
    from picard.tagger import Tagger

from picard import (
    api_versions_tuple,
)
from picard.config import get_config
from picard.const.appdirs import cache_folder
from picard.extension_points import (
    set_plugin_uuid,
    unset_plugin_uuid,
)
from picard.git.backend import GitObjectType
from picard.git.factory import git_backend
from picard.git.ops import GitOperations
from picard.git.ref_utils import get_ref_type
from picard.git.utils import get_local_repository_path
from picard.plugin3.installable import LocalInstallablePlugin, UrlInstallablePlugin
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
    PluginState,
    hash_string,
    short_commit_id,
)
from picard.plugin3.plugin_metadata import PluginMetadata, PluginMetadataManager
from picard.plugin3.refs_cache import RefsCache
from picard.plugin3.registry import PluginRegistry
from picard.plugin3.validation import PluginValidation
from picard.version import Version


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


class UpdateResult(NamedTuple):
    """Result of a plugin update operation."""

    old_version: str
    new_version: str
    old_commit: str
    new_commit: str
    old_ref: str
    new_ref: str
    commit_date: int


class UpdateCheck(NamedTuple):
    """Result of checking for plugin updates."""

    plugin_id: str
    old_commit: str
    new_commit: str
    commit_date: int
    old_ref: str
    new_ref: str


class UpdateAllResult(NamedTuple):
    """Result of updating a plugin in update_all operation."""

    plugin_id: str
    success: bool
    result: UpdateResult
    error: str


class PluginManagerError(Exception):
    """Base exception for plugin manager errors."""

    pass


class PluginDirtyError(PluginManagerError):
    """Raised when installed plugin directory has uncommitted changes."""

    def __init__(self, plugin_name, changes):
        self.plugin_name = plugin_name
        self.changes = changes
        super().__init__(f"Plugin {plugin_name} has uncommitted changes")


class PluginAlreadyInstalledError(PluginManagerError):
    """Raised when trying to install a plugin that's already installed."""

    def __init__(self, plugin_name, url):
        self.plugin_name = plugin_name
        self.url = url
        super().__init__(f"Plugin {plugin_name} is already installed")


class PluginBlacklistedError(PluginManagerError):
    """Raised when trying to install a blacklisted plugin."""

    def __init__(self, url, reason, uuid=None):
        self.url = url
        self.reason = reason
        self.uuid = uuid
        super().__init__(f"Plugin is blacklisted: {reason}")


class PluginManifestNotFoundError(PluginManagerError):
    """Raised when MANIFEST.toml is not found in plugin source."""

    def __init__(self, source):
        self.source = source
        super().__init__(f"No MANIFEST.toml found in {source}")


class PluginManifestReadError(PluginManagerError):
    """Raised when MANIFEST.toml cannot be read."""

    def __init__(self, e, source):
        self.source = source
        super().__init__(f"Failed to read MANIFEST.toml in {source}: {e}")


class PluginManifestInvalidError(PluginManagerError):
    """Raised when MANIFEST.toml validation fails."""

    def __init__(self, errors):
        self.errors = errors
        error_list = '\n  '.join(errors) if isinstance(errors, list) else str(errors)
        super().__init__(f"Invalid MANIFEST.toml:\n  {error_list}")


class PluginNoSourceError(PluginManagerError):
    """Raised when plugin has no stored source URL for update/switch-ref."""

    def __init__(self, plugin_id, operation):
        self.plugin_id = plugin_id
        self.operation = operation
        super().__init__(f"Plugin {plugin_id} has no stored URL, cannot {operation}")


class PluginRefSwitchError(PluginManagerError):
    """Raised when switching to a git ref fails."""

    def __init__(self, plugin_id, ref, original_error):
        self.plugin_id = plugin_id
        self.ref = ref
        self.original_error = original_error
        super().__init__(f"Cannot switch to ref {ref}: {original_error}")


class PluginRefNotFoundError(PluginManagerError):
    """Raised when requested ref is not found or not available."""

    def __init__(self, plugin_id, ref):
        self.plugin_id = plugin_id
        self.ref = ref
        super().__init__(f"Ref '{ref}' not found for plugin {plugin_id}")


class PluginNoUUIDError(PluginManagerError):
    """Raised when plugin has no UUID in manifest."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id} has no UUID")


class PluginCommitPinnedError(PluginManagerError):
    """Raised when trying to update a commit-pinned plugin."""

    def __init__(self, plugin_id, commit):
        self.plugin_id = plugin_id
        self.commit = commit
        super().__init__(f'Plugin is pinned to commit "{commit}" and cannot be updated')


class PluginUUIDConflictError(PluginManagerError):
    """Raised when trying to install plugin with conflicting UUID."""

    def __init__(self, uuid, existing_plugin_id, existing_source, new_source):
        self.uuid = uuid
        self.existing_plugin_id = existing_plugin_id
        self.existing_source = existing_source
        self.new_source = new_source
        super().__init__(
            f'Plugin UUID {uuid} already exists in plugin "{existing_plugin_id}" '
            f'from source "{existing_source}". Cannot install from different source "{new_source}".'
        )


def get_plugin_directory_name(manifest) -> str:
    """Get plugin directory name from manifest (sanitized name + full UUID).

    Args:
        manifest: PluginManifest instance

    Returns:
        Directory name: <sanitized_name>_<uuid>
        Example: my_plugin_f8bf81d7-c5e2-472b-ba96-62140cefc9e1
    """
    # Sanitize name: lowercase, alphanumeric + underscore
    name = manifest.name()
    sanitized = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    sanitized = sanitized[:50] if sanitized else 'plugin'

    uuid_str = manifest.uuid if manifest.uuid else 'no_uuid'
    return f'{sanitized}_{uuid_str}'


class PluginManager(QObject):
    """Installs, loads and updates plugins from multiple plugin directories."""

    plugin_installed = pyqtSignal(Plugin)
    plugin_uninstalled = pyqtSignal(Plugin)
    plugin_enabled = pyqtSignal(Plugin)
    plugin_disabled = pyqtSignal(Plugin)
    plugin_state_changed = pyqtSignal(Plugin)  # Emitted for both enable/disable
    plugin_ref_switched = pyqtSignal(Plugin)

    _primary_plugin_dir: Path | None = None
    _plugin_dirs: list[Path] = []

    def __init__(self, tagger: 'Tagger | None' = None) -> None:
        from picard.tagger import Tagger

        # Tests pass in a mock object and not an actual Tagger instance,
        # hence check type before passing it to QObject.
        super().__init__(parent=tagger if isinstance(tagger, QObject) else None)
        self._tagger: Tagger | None = tagger
        self._plugins: list[Plugin] = []  # Instance variable, not class variable
        self._enabled_plugins: set[str] = set()
        self._failed_plugins: list[tuple[Path, str, str]] = []  # List of (path, name, error_message) tuples
        self._load_config()

        # Initialize registry for blacklist checking

        cache_dir = cache_folder()
        self._registry = PluginRegistry(cache_dir=cache_dir)

        # Initialize refs cache

        self._refs_cache = RefsCache(self._registry)

        # Initialize metadata manager

        self._metadata = PluginMetadataManager(self._registry)

        # Register cleanup and clean up any leftover temp directories
        if tagger:
            tagger.register_cleanup(self._cleanup_temp_directories)
        self._cleanup_temp_directories()

    @property
    def plugins(self):
        return self._plugins

    @property
    def registry(self):
        return self._registry

    def _cleanup_temp_directories(self):
        """Remove leftover temporary plugin directories from failed installs."""
        if not self._primary_plugin_dir or not self._primary_plugin_dir.exists():
            return

        for entry in self._primary_plugin_dir.iterdir():
            if entry.is_dir() and entry.name.startswith('.tmp-'):
                shutil.rmtree(entry, ignore_errors=True)
                log.debug('Cleaned up temporary plugin directory: %s', entry)

    def refresh_registry_and_caches(self):
        """Refresh plugin registry and clear related caches."""
        self._registry.fetch_registry(use_cache=False)
        self._refs_cache.clear_cache()
        self._cleanup_version_cache()

    def get_default_ref_info(self, plugin_uuid):
        """Get default ref name and description for a plugin.

        Args:
            plugin_uuid: Plugin UUID to look up

        Returns:
            tuple: (ref_name, description) or (None, None) if not found
        """
        try:
            registry_plugin = self.registry.find_plugin(uuid=plugin_uuid)
            if registry_plugin:
                default_ref = self.select_ref_for_plugin(registry_plugin)
                if default_ref:
                    # Determine description based on whether it's a version tag or branch
                    if registry_plugin.versioning_scheme:
                        description = "latest version"
                    else:
                        description = "main branch"
                    return default_ref, description
        except Exception:
            pass
        return None, None

    def format_refs_for_display(self, refs, current_ref=None):
        """Format refs for display with commit IDs and current markers.

        Args:
            refs: Dict with 'tags' and 'branches' lists
            current_ref: Current ref name to mark as (current)

        Returns:
            dict: Formatted refs with display_name for each ref
        """
        formatted_refs = {'tags': [], 'branches': []}

        # Format tags
        for ref in refs.get('tags', []):
            from picard.git.utils import RefItem

            ref_item = RefItem(
                name=ref['name'],
                commit=ref.get('commit', ''),
                is_current=(current_ref and ref['name'] == current_ref),
                is_tag=True,
            )
            formatted_refs['tags'].append(
                {'name': ref['name'], 'commit': ref.get('commit'), 'display_name': ref_item.format()}
            )

        # Format branches
        for ref in refs.get('branches', []):
            ref_item = RefItem(
                name=ref['name'],
                commit=ref.get('commit', ''),
                is_current=(current_ref and ref['name'] == current_ref),
                is_branch=True,
            )
            formatted_refs['branches'].append(
                {'name': ref['name'], 'commit': ref.get('commit'), 'display_name': ref_item.format()}
            )

        return formatted_refs

    def fetch_all_git_refs(self, url, use_cache=True, force_refresh=False):
        """Fetch all branches and tags from a git repository.

        Args:
            url: Git repository URL
            use_cache: Whether to use cached data if available
            force_refresh: If True, ignore cache and fetch from network

        Returns:
            dict with keys:
                - branches: List of branch names
                - tags: List of tag names
            or None on error
        """
        # Check cache first
        if use_cache and not force_refresh:
            # Use cached data even if expired to avoid network calls
            cached_refs = self._refs_cache.get_cached_all_refs(url, allow_expired=True)
            if cached_refs is not None:
                return cached_refs
        elif use_cache:
            # Only use non-expired cache when force refreshing
            cached_refs = self._refs_cache.get_cached_all_refs(url)
            if cached_refs is not None:
                return cached_refs

        remote_refs = GitOperations.fetch_remote_refs(url, use_callbacks=True)
        if not remote_refs:
            # Try to use expired cache as fallback
            if use_cache:
                stale_cache = self._refs_cache.get_cached_all_refs(url, allow_expired=True)
                if stale_cache:
                    log.info('Using stale refs cache for %s due to fetch error', url)
                    return stale_cache
            return None

        # Separate branches and tags with their commit IDs
        # For annotated tags, git provides both the tag object and dereferenced commit (^{})
        branches = []
        tags = {}  # Use dict to merge tag object with dereferenced commit

        for ref in remote_refs:
            ref_name = ref.name if hasattr(ref, 'name') else str(ref)
            commit_id = str(ref.target) if hasattr(ref, 'target') and ref.target else None

            if ref_name.startswith('refs/heads/'):
                branch_name = ref_name[len('refs/heads/') :]
                branches.append({'name': branch_name, 'commit': commit_id})
            elif ref_name.startswith('refs/tags/'):
                tag_name = ref_name[len('refs/tags/') :]
                # Check if this is a dereferenced tag (^{})
                if tag_name.endswith('^{}'):
                    # This is the actual commit for an annotated tag
                    base_tag = tag_name[:-3]  # Remove ^{}
                    if base_tag in tags:
                        tags[base_tag]['commit'] = commit_id  # Update with actual commit
                else:
                    # Regular tag or annotated tag object
                    if tag_name not in tags:
                        tags[tag_name] = {'name': tag_name, 'commit': commit_id}

        result = {
            'branches': sorted(branches, key=lambda x: x['name']),
            'tags': sorted(tags.values(), key=lambda x: x['name'], reverse=True),
        }

        # Cache the result
        if use_cache:
            self._refs_cache.cache_all_refs(url, result)

        return result

    def get_plugin_refs_info(self, identifier):
        """Get plugin refs information from identifier.

        Args:
            identifier: Plugin name, registry ID, UUID, or git URL

        Returns:
            dict with plugin refs info or None if not found
        """
        return self._metadata.get_plugin_refs_info(identifier, self.plugins)

    def get_plugin_registry_id(self, plugin):
        """Get registry ID for a plugin."""
        return self._metadata.get_plugin_registry_id(plugin)

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

        for plugin in self.plugins:
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
                registry_id = self.get_plugin_registry_id(plugin)
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

    def _get_plugin_metadata(self, uuid):
        """Get metadata for a plugin by UUID."""
        return self._metadata.get_plugin_metadata(uuid)

    def get_preferred_version(self, plugin_uuid, manifest_version=''):
        """Get preferred version for display, preferring git tag over manifest version.

        Args:
            plugin_uuid: Plugin UUID to look up metadata
            manifest_version: Fallback version from manifest

        Returns:
            Version string (git tag if available and looks like version, otherwise manifest version)
        """
        metadata = self._get_plugin_metadata(plugin_uuid) if plugin_uuid else None
        if not metadata:
            return manifest_version

        ref = metadata.ref or ''
        commit = metadata.commit or ''

        # If ref looks like a version tag (not a commit hash), use it
        if ref and commit and not ref.startswith(short_commit_id(commit)):
            return ref

        return manifest_version

    def _save_plugin_metadata(self, metadata):
        """Save plugin metadata."""
        return self._metadata.save_plugin_metadata(metadata)

    def _find_plugin_by_url(self, url):
        """Find plugin metadata by URL."""
        return self._metadata.find_plugin_by_url(url)

    def _get_plugin_uuid(self, plugin):
        """Get plugin UUID."""
        return PluginValidation.get_plugin_uuid(plugin)

    def _read_and_validate_manifest(self, path, source_description):
        """Read and validate manifest."""
        return PluginValidation.read_and_validate_manifest(path, source_description)

    def _clean_plugin_config(self, plugin_uuid):
        """Delete plugin configuration."""
        config = get_config()
        config_key = f'plugin.{plugin_uuid}'
        config.beginGroup(config_key)
        for key in config.childKeys():
            config.remove(key)
        config.endGroup()
        config.sync()
        log.info('Deleted configuration for plugin %s', plugin_uuid)

    def get_orphaned_plugin_configs(self):
        """Get list of plugin configs that don't have corresponding installed plugins.

        Returns:
            list: List of plugin UUIDs that have config but no installed plugin
        """
        config = get_config()
        installed_uuids = {p.uuid for p in self.plugins if p.uuid}

        orphaned = []
        for group in config.childGroups():
            if group.startswith('plugin.'):
                plugin_uuid = group[7:]  # Remove 'plugin.' prefix
                if plugin_uuid not in installed_uuids:
                    config.beginGroup(group)
                    if config.childKeys():  # Only include if it has settings
                        orphaned.append(plugin_uuid)
                    config.endGroup()

        return sorted(orphaned)

    def _check_uuid_conflict(self, manifest, source_url):
        """Check if plugin UUID conflicts with existing plugin from different source.

        Args:
            manifest: Plugin manifest to check
            source_url: Source URL of the plugin being installed

        Returns:
            tuple: (has_conflict: bool, existing_plugin: Plugin|None)
        """
        if not manifest.uuid:
            return False, None

        # Normalize source URL for comparison
        source_url = str(source_url).rstrip('/')

        for existing_plugin in self._plugins:
            if existing_plugin.uuid and str(existing_plugin.uuid).lower() == str(manifest.uuid).lower():
                # Get existing plugin's source URL
                existing_metadata = self._metadata.get_plugin_metadata(existing_plugin.uuid)
                existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
                existing_source = str(existing_source).rstrip('/')

                # Same UUID + same source = no conflict (reinstall case)
                if existing_source.lower() == source_url.lower():
                    return False, None

                # Same UUID + different source = conflict
                return True, existing_plugin

        return False, None

    def _cleanup_version_cache(self):
        """Remove cache entries for URLs no longer in registry."""
        return self._refs_cache.cleanup_cache()

    def _ensure_plugin_url(self, plugin, operation):
        """Ensure plugin has URL metadata, creating it from registry if needed.

        Args:
            plugin: Plugin to check
            operation: Operation name for error message

        Raises:
            PluginNoSourceError: If URL cannot be found in metadata or registry
        """
        uuid = PluginValidation.get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)

        if metadata and metadata.url:
            return  # URL exists in metadata

        # No metadata or no URL - check if plugin is in registry and create metadata
        registry_plugin = self._registry.find_plugin(uuid=uuid)
        if not registry_plugin:
            raise PluginNoSourceError(plugin.plugin_id, operation)

        # Create metadata from registry
        metadata_obj = PluginMetadata(
            name=plugin.manifest.name(),
            url=registry_plugin.git_url,
            ref='',
            commit='',
            uuid=uuid,
        )
        self._metadata.save_plugin_metadata(metadata_obj)

    def _fetch_version_tags(self, url, versioning_scheme):
        """Fetch and filter version tags from repository."""
        return self._fetch_version_tags_impl(url, versioning_scheme)

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
        from picard import api_versions_tuple

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

    def search_registry_plugins(self, query=None, category=None, trust_level=None):
        """Search registry plugins with optional filters.

        Args:
            query: Search query (searches name, description, id)
            category: Filter by category
            trust_level: Filter by trust level

        Returns:
            list: Filtered plugin dictionaries from registry
        """
        plugins = self._registry.list_plugins(category=category, trust_level=trust_level)

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
        all_plugins = self._registry.list_plugins()
        matches = [p for p in all_plugins if query.lower() in p['id'].lower()]
        return matches if 1 <= len(matches) <= max_results else []

    def get_registry_plugin_latest_version(self, plugin):
        """Get latest version tag for a registry plugin.

        Args:
            plugin: RegistryPlugin object

        Returns:
            Version string (latest tag or empty string)
        """
        versioning_scheme = plugin.versioning_scheme
        url = plugin.git_url

        if not versioning_scheme:
            return ''

        if not url:
            return ''

        try:
            tags = self._fetch_version_tags(url, versioning_scheme)
            return tags[0] if tags else ''
        except Exception:
            return ''

    def switch_ref(self, plugin, ref, discard_changes=False):
        """Switch plugin to a different git ref."""
        self._ensure_plugin_url(plugin, 'switch ref')

        # Check if plugin is currently enabled
        was_enabled = plugin.state == PluginState.ENABLED

        # Disable plugin if it's enabled to unload the module
        if was_enabled:
            self.disable_plugin(plugin)

        old_ref, new_ref, old_commit, new_commit = GitOperations.switch_ref(plugin, ref, discard_changes)

        # Update metadata with new ref
        uuid = PluginValidation.get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)
        if metadata:
            # Update existing metadata
            metadata.ref = new_ref
            metadata.commit = new_commit
            self._metadata.save_plugin_metadata(metadata)

        # Re-enable plugin if it was enabled before to reload the module
        if was_enabled:
            self.enable_plugin(plugin)

        self.plugin_ref_switched.emit(plugin)
        return old_ref, new_ref, old_commit, new_commit

    def add_directory(self, dir_path: str, primary: bool = False) -> None:
        """Add a directory to scan for plugins.

        Args:
            dir_path: Path to plugin directory
            primary: Whether this is the primary plugin directory
        """
        plugin_dir = Path(os.path.normpath(dir_path))
        if plugin_dir in self._plugin_dirs:
            log.warning('Plugin directory %s already registered', plugin_dir)
            return

        log.debug('Registering plugin directory %s', plugin_dir)
        if not plugin_dir.exists():
            os.makedirs(plugin_dir)

        for entry in plugin_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith('.'):
                plugin = self._load_plugin(plugin_dir, entry.name)
                if plugin:
                    log.debug('Found plugin %s in %s', plugin.plugin_id, plugin.local_path)
                    self._plugins.append(plugin)

        self._plugin_dirs.append(plugin_dir)
        if primary:
            self._primary_plugin_dir = plugin_dir

    def _preserve_original_ref_if_needed(self, url_or_path, ref, reinstall):
        """Preserve original ref if reinstalling and no ref specified.

        Args:
            url_or_path: Plugin URL or local path
            ref: Current ref (may be None)
            reinstall: Whether this is a reinstall operation

        Returns:
            str|None: Preserved ref or original ref
        """
        if not (reinstall and ref is None):
            return ref

        try:
            # Check existing plugins in memory first
            for existing_plugin in self._plugins:
                # Ensure manifest is loaded
                if not existing_plugin.manifest:
                    try:
                        existing_plugin.read_manifest()
                    except Exception:
                        continue

                if existing_plugin.uuid:
                    existing_metadata = self._metadata.get_plugin_metadata(existing_plugin.uuid)
                    if (
                        existing_metadata
                        and existing_metadata.url
                        and str(existing_metadata.url).rstrip('/') == str(url_or_path).rstrip('/')
                    ):
                        if existing_metadata.ref:
                            log.debug('Preserving original ref "%s" for plugin reinstall', existing_metadata.ref)
                            return existing_metadata.ref
        except Exception as e:
            log.debug('Could not preserve original ref: %s', e)

        return ref

    def install_plugin(
        self, url, ref=None, reinstall=False, force_blacklisted=False, discard_changes=False, enable_after_install=False
    ):
        """Install a plugin from a git URL or local directory.

        Args:
            url: Git repository URL or local directory path
            ref: Git ref (branch/tag/commit) to checkout (ignored for local paths)
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
            discard_changes: If True, discard uncommitted changes on reinstall
            enable_after_install: If True, enable the plugin after successful installation

        Raises:
            PluginDirtyError: If reinstalling and plugin has uncommitted changes
        """

        # Check if url is a local directory
        local_path = get_local_repository_path(url)

        # Check blacklist before installing
        if not force_blacklisted:
            # Create appropriate InstallablePlugin for blacklist checking
            if local_path:
                plugin = LocalInstallablePlugin(str(local_path), ref, self._registry)
            else:
                plugin = UrlInstallablePlugin(url, ref, self._registry)

            is_blacklisted, blacklist_reason = plugin.is_blacklisted()
            if is_blacklisted:
                raise PluginBlacklistedError(url, blacklist_reason)

        # Install from local directory or remote URL
        if local_path:
            return self._install_from_local_directory(
                local_path, reinstall, force_blacklisted, ref, discard_changes, enable_after_install
            )

        # Preserve original ref if reinstalling and no ref specified
        ref = self._preserve_original_ref_if_needed(url, ref, reinstall)

        # Handle git URL - use temp dir in plugin directory for atomic rename

        url_hash = hash_string(url)
        temp_path = self._primary_plugin_dir / f'.tmp-plugin-{url_hash}'

        try:
            # Reuse temp dir if it's already a git repo, otherwise remove it
            if temp_path.exists():
                if not (temp_path / '.git').exists():
                    # Not a git repo, remove it
                    shutil.rmtree(temp_path)

            # Clone or update temporary location with single-branch optimization
            source = PluginSourceGit(url, ref)
            try:
                commit_id = source.sync(temp_path, single_branch=True)
            except Exception as e:
                # If sync fails and we're using a preserved ref, try fallback to default
                if ref and reinstall:
                    log.warning('Failed to sync with preserved ref "%s": %s. Falling back to default ref.', ref, e)
                    source = PluginSourceGit(url, None)  # Use default ref
                    commit_id = source.sync(temp_path, single_branch=True)
                else:
                    raise

            # Read MANIFEST to get plugin ID
            manifest = PluginValidation.read_and_validate_manifest(temp_path, url)

            # Generate plugin directory name from sanitized name + UUID
            plugin_name = get_plugin_directory_name(manifest)

            # Check blacklist again with UUID
            if not force_blacklisted:
                plugin = UrlInstallablePlugin(url, ref, self._registry)
                plugin.plugin_uuid = manifest.uuid  # Update with actual UUID from manifest
                is_blacklisted, blacklist_reason = plugin.is_blacklisted()
                if is_blacklisted:
                    raise PluginBlacklistedError(url, blacklist_reason, manifest.uuid)

            # Check for UUID conflicts with existing plugins from different sources
            has_conflict, existing_plugin = self._check_uuid_conflict(manifest, url)
            if has_conflict and not reinstall:
                existing_metadata = self._metadata.get_plugin_metadata(existing_plugin.uuid)
                existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
                raise PluginUUIDConflictError(manifest.uuid, existing_plugin.plugin_id, existing_source, url)

            final_path = self._primary_plugin_dir / plugin_name

            # Check if already installed and handle reinstall
            if final_path.exists():
                if not reinstall:
                    raise PluginAlreadyInstalledError(plugin_name, url)

                # Find and unload existing plugin before reinstall
                existing_plugin = None
                for plugin in self._plugins:
                    if plugin.local_path == final_path:
                        existing_plugin = plugin
                        break

                if existing_plugin:
                    # Force disable the plugin to ensure all extensions are unregistered
                    # This is needed even if plugin is not in enabled list
                    try:
                        if existing_plugin.state != PluginState.DISABLED:
                            existing_plugin.disable()
                    except Exception:
                        # If disable fails, continue anyway
                        pass

                    # Remove from enabled plugins list if present
                    if existing_plugin.plugin_id in self._enabled_plugins:
                        self._enabled_plugins.discard(existing_plugin.plugin_id)

                    # Remove plugin from plugins list
                    if existing_plugin in self.plugins:
                        self.plugins.remove(existing_plugin)

                # Check for uncommitted changes before removing
                if not discard_changes:
                    changes = GitOperations.check_dirty_working_dir(final_path)
                    if changes:
                        raise PluginDirtyError(plugin_name, changes)

                shutil.rmtree(final_path)

            # Atomic rename from temp to final location
            temp_path.rename(final_path)

            # Update version tag cache from cloned repo if plugin has versioning_scheme
            registry_plugin = self._registry.find_plugin(url=url)
            if registry_plugin:
                versioning_scheme = registry_plugin.versioning_scheme
                if versioning_scheme:
                    self._refs_cache.update_cache_from_local_repo(final_path, url, versioning_scheme)

            # Store plugin metadata
            self._metadata.save_plugin_metadata(
                PluginMetadata(
                    name=plugin_name,
                    url=url,
                    ref=source.resolved_ref,
                    commit=commit_id,
                    uuid=manifest.uuid,
                )
            )

            # Add newly installed plugin to the plugins list
            plugin = Plugin(self._primary_plugin_dir, plugin_name)
            self._plugins.append(plugin)
            self.plugin_installed.emit(plugin)

            # Enable plugin if requested
            if enable_after_install:
                self.enable_plugin(plugin)

            return plugin_name

        except Exception:
            # Clean up temp directory on failure
            if temp_path.exists():
                # Force garbage collection to release file handles on Windows
                gc.collect()
                shutil.rmtree(temp_path, ignore_errors=True)
            raise

    def _install_from_local_directory(
        self,
        local_path: Path,
        reinstall=False,
        force_blacklisted=False,
        ref=None,
        discard_changes=False,
        enable_after_install=False,
    ):
        """Install a plugin from a local directory.

        Args:
            local_path: Path to local plugin directory
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
            ref: Git ref to checkout if local_path is a git repository
            discard_changes: If True, discard uncommitted changes on reinstall
            enable_after_install: If True, enable the plugin after successful installation

        Returns:
            str: Plugin ID
        """
        # Preserve original ref if reinstalling and no ref specified
        ref = self._preserve_original_ref_if_needed(local_path, ref, reinstall)

        # Check if local directory is a git repository
        is_git_repo = (local_path / '.git').exists()

        if is_git_repo:
            # Check if source repository has uncommitted changes
            try:
                backend = git_backend()
                source_repo = backend.create_repository(local_path)
                if source_repo.get_status():
                    log.warning('Installing from local repository with uncommitted changes: %s', local_path)

                # If no ref specified, use the current branch
                if not ref and not source_repo.is_head_detached():
                    ref = source_repo.get_head_shorthand()
                    log.debug('Using current branch from local repo: %s', ref)
            except Exception:
                pass  # Ignore errors checking status

            # Use git operations to get ref and commit info

            url_hash = hash_string(str(local_path))
            temp_path = Path(tempfile.gettempdir()) / f'picard-plugin-{url_hash}'

            try:
                source = PluginSourceGit(str(local_path), ref)
                commit_id = source.sync(temp_path, single_branch=True)
                install_path = temp_path
                ref_to_save = source.resolved_ref
                commit_to_save = commit_id
            except Exception:
                # Clean up temp directory on failure
                if temp_path.exists():
                    gc.collect()
                    shutil.rmtree(temp_path, ignore_errors=True)
                raise
        else:
            # Direct copy for non-git directories
            install_path = local_path
            ref_to_save = ''
            commit_to_save = ''

        # Read MANIFEST to get plugin ID
        manifest = PluginValidation.read_and_validate_manifest(install_path, local_path)

        # Check for UUID conflicts with existing plugins from different sources
        has_conflict, existing_plugin = self._check_uuid_conflict(manifest, str(local_path))
        if has_conflict and not reinstall:
            existing_metadata = self._metadata.get_plugin_metadata(existing_plugin.uuid)
            existing_source = existing_metadata.url if existing_metadata else str(existing_plugin.local_path)
            raise PluginUUIDConflictError(manifest.uuid, existing_plugin.plugin_id, existing_source, str(local_path))

        # Generate plugin directory name from sanitized name + UUID
        plugin_name = get_plugin_directory_name(manifest)
        assert self._primary_plugin_dir is not None
        final_path = self._primary_plugin_dir / plugin_name

        # Check if already installed and handle reinstall
        if final_path.exists():
            if not reinstall:
                raise PluginAlreadyInstalledError(plugin_name, local_path)

            # Check for uncommitted changes before removing
            if not discard_changes:
                changes = GitOperations.check_dirty_working_dir(final_path)
                if changes:
                    raise PluginDirtyError(plugin_name, changes)

            shutil.rmtree(final_path)

        # Copy to plugin directory
        if is_git_repo:
            # Move from temp location (git repo was cloned to temp)
            shutil.move(str(install_path), str(final_path))
        else:
            # Copy from local directory (non-git)
            shutil.copytree(install_path, final_path)

        # Store metadata
        self._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin_name,
                url=str(local_path),
                ref=ref_to_save or '',
                commit=commit_to_save or '',
                uuid=manifest.uuid,
            )
        )

        # Add newly installed plugin to the plugins list
        plugin = Plugin(self._primary_plugin_dir, plugin_name)
        self._plugins.append(plugin)

        # Enable plugin if requested
        if enable_after_install:
            self.enable_plugin(plugin)

        log.info('Plugin %s installed from local directory %s', plugin_name, local_path)
        return plugin_name

    def _fetch_version_tags_impl(self, url, versioning_scheme):
        """Fetch and filter version tags from repository.

        Args:
            url: Git repository URL
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            list: Sorted list of version tags (newest first), or empty list on error
        """
        # Parse versioning scheme
        pattern = self._refs_cache.parse_versioning_scheme(versioning_scheme)
        if not pattern:
            return []

        # Try to reuse all_refs cache to avoid redundant fetch
        all_refs = self.fetch_all_git_refs(url, use_cache=True)
        if not all_refs:
            # Try to use expired cache as fallback
            stale_cache = self._refs_cache.get_cached_tags(url, versioning_scheme, allow_expired=True)
            if stale_cache:
                log.info('Using stale cache for %s due to fetch error', url)
                return stale_cache
            return []

        # Filter and sort tags from cached refs
        tags = [tag['name'] for tag in all_refs.get('tags', []) if pattern.match(tag['name'])]
        tags = self._refs_cache.sort_tags(tags, versioning_scheme)

        # Cache the result
        if tags:
            self._refs_cache.cache_tags(url, versioning_scheme, tags)

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
        tags = self._fetch_version_tags_impl(url, versioning_scheme)
        if not tags:
            return None

        # Use version parsing for semver/calver, lexicographic for custom regex
        if versioning_scheme in ('semver', 'calver'):
            try:
                # Strip any non-digit prefix for version comparison
                def strip_prefix(tag):
                    match = re.search(r'\d', tag)
                    return tag[match.start() :] if match else tag

                current_version = Version.from_string(strip_prefix(current_tag))
                for tag in tags:
                    tag_version = Version.from_string(strip_prefix(tag))
                    if tag_version > current_version:
                        return tag
                return None
            except Exception:
                pass

        # Fallback to lexicographic comparison for custom regex
        for tag in tags:
            if tag > current_tag:
                return tag

        return None

    def update_plugin(self, plugin: Plugin, discard_changes=False):
        """Update a single plugin to latest version.

        Args:
            plugin: Plugin to update
            discard_changes: If True, discard uncommitted changes

        Raises:
            PluginDirtyError: If plugin has uncommitted changes and discard_changes=False
            ValueError: If plugin is pinned to a specific commit
        """
        self._ensure_plugin_url(plugin, 'update')

        uuid = PluginValidation.get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)

        # Check for uncommitted changes
        if not discard_changes:
            assert plugin.local_path is not None
            changes = GitOperations.check_dirty_working_dir(plugin.local_path)
            if changes:
                raise PluginDirtyError(plugin.plugin_id, changes)

        old_version = str(plugin.manifest.version) if plugin.manifest and plugin.manifest.version else None
        old_url = metadata.url
        old_uuid = metadata.uuid
        old_ref = metadata.ref

        # Check if pinned to a specific commit (not tag - tags can be updated to newer tags)
        # Check the stored ref, not current HEAD (tags create detached HEAD but are still updatable)
        if old_ref:
            ref_type, _ = GitOperations.check_ref_type(plugin.local_path, old_ref)
            if ref_type == 'commit':
                raise PluginCommitPinnedError(plugin.plugin_id, old_ref)
        else:
            # No stored ref, check current HEAD state
            ref_type, ref_name = GitOperations.check_ref_type(plugin.local_path)
            if ref_type == 'commit':
                raise PluginCommitPinnedError(plugin.plugin_id, ref_name)

        # Check registry for redirects
        current_url, current_uuid, redirected = self._metadata.check_redirects(old_url, old_uuid)

        # Check if plugin has versioning_scheme and current ref is a version tag
        new_ref = old_ref
        registry_plugin = self._registry.find_plugin(url=current_url, uuid=current_uuid)
        if registry_plugin and registry_plugin.versioning_scheme and ref_type == 'tag':
            # Try to find newer version tags
            newer_tag = self._find_newer_version_tag(current_url, old_ref, registry_plugin.versioning_scheme)
            if newer_tag:
                new_ref = newer_tag
                log.info('Found newer version: %s -> %s', old_ref, new_ref)

        # Check if plugin is currently enabled - disable it to reload module after update
        was_enabled = plugin.state == PluginState.ENABLED
        if was_enabled:
            self.disable_plugin(plugin)

        source = PluginSourceGit(current_url, new_ref)
        assert plugin.local_path is not None
        old_commit, new_commit = source.update(plugin.local_path, single_branch=True)

        # Get commit date and resolve annotated tags to actual commit
        backend = git_backend()
        repo = backend.create_repository(plugin.local_path)
        obj = repo.revparse_single(new_commit)
        # Peel tag to commit if needed
        if obj.type == GitObjectType.TAG:
            commit = repo.peel_to_commit(obj)
            new_commit = commit.id  # Use actual commit ID, not tag object ID
        else:
            commit = obj
        # Get commit date using backend
        commit_date = repo.get_commit_date(commit.id)
        repo.free()

        # Reload manifest to get new version
        plugin.read_manifest()
        new_version = str(plugin.manifest.version) if plugin.manifest and plugin.manifest.version else None
        new_ref = source.ref  # May have been updated to a newer tag

        # Update metadata with current URL and UUID
        # If redirected, preserve original URL/UUID
        # Use source.ref which may have been updated to a newer tag
        original_url, original_uuid = self._metadata.get_original_metadata(metadata, redirected, old_url, old_uuid)
        self._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin.plugin_id,
                url=current_url,
                ref=new_ref or '',
                commit=new_commit,
                uuid=current_uuid,
                original_url=original_url,
                original_uuid=original_uuid,
            )
        )

        # Update version tag cache from updated repo
        if registry_plugin and registry_plugin.versioning_scheme:
            self._refs_cache.update_cache_from_local_repo(
                plugin.local_path, current_url, registry_plugin.versioning_scheme
            )

        # Re-enable plugin if it was enabled before to reload the module with new code
        if was_enabled:
            self.enable_plugin(plugin)

        # Emit signal to notify UI that plugin has been updated
        self.plugin_ref_switched.emit(plugin)

        return UpdateResult(
            old_version or '',
            new_version or '',
            old_commit,
            new_commit,
            old_ref or '',
            new_ref or '',
            commit_date,
        )

    def update_all_plugins(self):
        """Update all installed plugins."""
        results = []
        for plugin in self._plugins:
            try:
                result = self.update_plugin(plugin)
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=True, result=result, error=None))
            except PluginCommitPinnedError as e:
                # Commit-pinned plugins are skipped, not failed
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=True, result=None, error=str(e)))
            except Exception as e:
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=False, result=None, error=str(e)))
        return results

    def check_updates(self):
        """Check which plugins have updates available without installing."""
        updates = []
        for plugin in self._plugins:
            if not plugin.uuid:
                continue

            metadata = self._metadata.get_plugin_metadata(plugin.uuid)
            if not metadata or not metadata.url:
                continue

            try:
                backend = git_backend()
                repo = backend.create_repository(plugin.local_path)
                current_commit = repo.get_head_target()

                # Fetch without updating (suppress progress output)
                callbacks = backend.create_remote_callbacks()
                for remote in repo.get_remotes():
                    repo.fetch_remote(remote, None, callbacks._callbacks)

                # Update version tag cache from fetched repo if plugin has versioning_scheme
                registry_plugin = self._registry.find_plugin(uuid=plugin.uuid)
                if registry_plugin and registry_plugin.versioning_scheme:
                    self._refs_cache.update_cache_from_local_repo(
                        plugin.local_path, metadata.url, registry_plugin.versioning_scheme
                    )

                old_ref = metadata.ref or 'main'
                ref = old_ref

                # Check if currently on a tag
                current_is_tag = False
                current_tag = None
                ref_type, resolved_ref = get_ref_type(repo, ref)
                if ref_type == 'tag':
                    try:
                        repo.revparse_single(resolved_ref)
                        current_is_tag = True
                        current_tag = ref
                    except KeyError:
                        pass

                # If on a tag, check for newer version tag
                new_ref = None
                if current_is_tag and current_tag:
                    source = PluginSourceGit(metadata.url, ref)
                    latest_tag = source._find_latest_tag(repo, current_tag)
                    if latest_tag and latest_tag != current_tag:
                        # Found newer tag
                        ref = latest_tag
                        new_ref = latest_tag

                # Resolve ref with same logic as update() - try origin/ prefix for branches
                try:
                    if not ref.startswith('origin/') and not ref.startswith('refs/'):
                        # For tags, try refs/tags/ first, then origin/ for branches
                        try:
                            obj = repo.revparse_single(f'refs/tags/{ref}')
                        except KeyError:
                            # Not a tag, try origin/ prefix for branches
                            try:
                                obj = repo.revparse_single(f'origin/{ref}')
                            except KeyError:
                                # Fall back to original ref (might be commit hash)
                                obj = repo.revparse_single(ref)
                    elif ref.startswith('origin/'):
                        # Handle origin/ refs - these are branches, not tags
                        obj = repo.revparse_single(ref)
                    else:
                        obj = repo.revparse_single(ref)

                    # Peel annotated tags to get the actual commit
                    if obj.type == GitObjectType.TAG:
                        commit = repo.peel_to_commit(obj)
                    else:
                        commit = obj

                    latest_commit = commit.id
                    # Get commit date using backend
                    latest_commit_date = repo.get_commit_date(commit.id)
                except KeyError:
                    # Ref not found, skip this plugin
                    continue

                repo.free()

                if current_commit != latest_commit:
                    updates.append(
                        UpdateCheck(
                            plugin_id=plugin.plugin_id,
                            old_commit=short_commit_id(current_commit),
                            new_commit=short_commit_id(latest_commit),
                            commit_date=latest_commit_date,
                            old_ref=old_ref,
                            new_ref=new_ref,
                        )
                    )
            except KeyError:
                # Ref not found, skip this plugin (expected for some cases)
                continue
            except Exception as e:
                # Log unexpected errors but continue with other plugins
                log.warning("Failed to check updates for plugin %s: %s", plugin.plugin_id, e)
                continue

        return updates

    def get_plugin_update_status(self, plugin, force_refresh=False):
        """Check if a single plugin has an update available."""
        log.debug("Checking update status for plugin: %s", plugin.plugin_id)

        if not plugin.uuid:
            return False

        metadata = self._metadata.get_plugin_metadata(plugin.uuid)
        if not metadata or not metadata.url:
            return False

        current_ref = metadata.ref or 'main'

        # Try cached result first (unless force refresh)
        if not force_refresh:
            # Use cached result even if expired to avoid network calls
            cached_result = self._refs_cache.get_cached_update_status(plugin.plugin_id, current_ref, ttl=float('inf'))
            if cached_result is not None:
                log.debug("Using cached update status for plugin: %s", plugin.plugin_id)
                return cached_result
            else:
                # No cached data and not force refreshing - assume no update to avoid network calls
                log.debug("No cached update status for plugin %s, assuming no update available", plugin.plugin_id)
                return False

        try:
            backend = git_backend()
            repo = backend.create_repository(plugin.local_path)
            current_commit = repo.get_head_target()

            # Fetch without updating (suppress progress output)
            log.debug("Making network request for plugin: %s", plugin.plugin_id)
            callbacks = backend.create_remote_callbacks()
            for remote in repo.get_remotes():
                repo.fetch_remote(remote, None, callbacks._callbacks)

            # Update version tag cache from fetched repo if plugin has versioning_scheme
            registry_plugin = self._registry.find_plugin(uuid=plugin.uuid)
            if registry_plugin and registry_plugin.versioning_scheme:
                self._refs_cache.update_cache_from_local_repo(
                    plugin.local_path, metadata.url, registry_plugin.versioning_scheme
                )

            old_ref = metadata.ref or 'main'
            ref = old_ref

            # Check if currently on a tag by checking available refs
            current_is_tag = False
            current_tag = None
            ref_type, resolved_ref = get_ref_type(repo, ref)
            if ref_type == 'tag':
                current_is_tag = True
                current_tag = ref

            # If on a tag, check for newer version tag
            if current_is_tag and current_tag:
                source = PluginSourceGit(metadata.url, ref)
                latest_tag = source._find_latest_tag(repo, current_tag)
                if latest_tag and latest_tag != current_tag:
                    # Found newer tag
                    ref = latest_tag

            # Resolve ref with same logic as update() - try appropriate prefix based on ref type
            try:
                if not ref.startswith('origin/') and not ref.startswith('refs/'):
                    # If we know it's a tag, try refs/tags/ first
                    if current_is_tag:
                        try:
                            obj = repo.revparse_single(f'refs/tags/{ref}')
                        except KeyError:
                            # Fall back to original ref
                            obj = repo.revparse_single(ref)
                    else:
                        # For branches, try origin/ prefix first
                        try:
                            obj = repo.revparse_single(f'origin/{ref}')
                        except KeyError:
                            # Fall back to original ref (might be commit hash)
                            obj = repo.revparse_single(ref)
                elif ref.startswith('origin/'):
                    # Handle origin/ refs - these are branches, not tags
                    obj = repo.revparse_single(ref)
                else:
                    obj = repo.revparse_single(ref)

                # Peel annotated tags to get the actual commit
                if obj.type == GitObjectType.TAG:
                    commit = repo.peel_to_commit(obj)
                else:
                    commit = obj

                latest_commit = commit.id
            except KeyError:
                # Ref not found, no update available
                return False

            repo.free()
            has_update = current_commit != latest_commit
            # Cache the result with current ref
            self._refs_cache.cache_update_status(plugin.plugin_id, has_update, current_ref)
            return has_update
        except KeyError:
            # Ref not found, no update available
            self._refs_cache.cache_update_status(plugin.plugin_id, False, current_ref)
            return False
        except Exception as e:
            # Log unexpected errors
            log.warning("Failed to check update for plugin %s: %s", plugin.plugin_id, e)
            # Don't cache errors
            return False

    def get_plugin_remote_url(self, plugin):
        """Get plugin remote URL from metadata."""
        if not plugin.uuid:
            return None

        try:
            metadata = self._metadata.get_plugin_metadata(plugin.uuid)
            if metadata and hasattr(metadata, 'url'):
                return metadata.url
        except Exception:
            pass
        return None

    def get_plugin_version_display(self, plugin):
        """Get version display text for plugin."""
        version_text = ""

        try:
            # Try to get version from git metadata first (prioritize git ref)
            if plugin.uuid:
                metadata = self._metadata.get_plugin_metadata(plugin.uuid)
                if metadata:
                    git_info = self.get_plugin_git_info(metadata)
                    if git_info:
                        version_text = git_info
        except Exception:
            pass

        # Fallback to manifest version if no git metadata
        if not version_text:
            if plugin.manifest and hasattr(plugin.manifest, '_data'):
                version = plugin.manifest._data.get('version')
                if version:
                    version_text = version

        return version_text or "Unknown"

    def get_plugin_git_info(self, metadata):
        """Format git information for display."""
        if not metadata:
            return ""

        from picard.git.utils import RefItem

        ref_item = RefItem(name=getattr(metadata, 'ref', ''), commit=getattr(metadata, 'commit', ''))
        return ref_item.format()

    def get_plugin_homepage(self, plugin):
        """Get plugin homepage URL from manifest."""
        if not plugin.manifest or not hasattr(plugin.manifest, '_data'):
            return None
        return plugin.manifest._data.get('homepage')

    def long_description_as_html(self, plugin):
        """Get plugin long description converted from markdown to HTML."""
        if not plugin.manifest:
            return None

        try:
            description = plugin.manifest.long_description_i18n()
            if description and render_markdown:
                return render_markdown(description, output_format='html')
            return description
        except (AttributeError, Exception):
            return None

    def get_plugin_versioning_scheme(self, plugin):
        """Get versioning scheme for plugin from registry."""
        if plugin.uuid:
            return ""

        try:
            metadata = self._metadata.get_plugin_metadata(plugin.uuid)
            if metadata and hasattr(metadata, 'url'):
                registry_plugin = self._registry.find_plugin(uuid=plugin.uuid)
                if registry_plugin:
                    return registry_plugin.versioning_scheme or ''
        except Exception:
            pass
        return ""

    def uninstall_plugin(self, plugin: Plugin, purge=False):
        """Uninstall a plugin.

        Args:
            plugin: Plugin to uninstall
            purge: If True, also remove plugin configuration
        """
        self.disable_plugin(plugin)
        plugin_path = plugin.local_path

        # Safety check: ensure plugin_path is a child of primary plugin dir, not the dir itself
        assert self._primary_plugin_dir is not None
        assert plugin_path is not None
        if not plugin_path.is_relative_to(self._primary_plugin_dir) or plugin_path == self._primary_plugin_dir:
            raise ValueError(f'Plugin path must be a subdirectory of {self._primary_plugin_dir}: {plugin_path}')

        if os.path.islink(plugin_path):
            log.debug("Removing symlink %r", plugin_path)
            os.remove(plugin_path)
        elif os.path.isdir(plugin_path):
            log.debug("Removing directory %r", plugin_path)
            shutil.rmtree(plugin_path)

        # Remove metadata
        config = get_config()
        # Remove metadata by UUID if available
        if plugin.uuid:
            config.setting['plugins3_metadata'].pop(plugin.uuid, None)

        # Unregister UUID mapping
        if plugin.uuid:
            unset_plugin_uuid(plugin.uuid)

        # Remove plugin config if purge requested
        if purge and plugin.uuid:
            self._clean_plugin_config(plugin.uuid)

        # Remove plugin from plugins list
        if plugin in self.plugins:
            self.plugins.remove(plugin)

        self.plugin_uninstalled.emit(plugin)

    def plugin_has_saved_options(self, plugin: Plugin) -> bool:
        """Check if a plugin has any saved options.

        Args:
            plugin: Plugin to check

        Returns:
            True if plugin has saved options, False otherwise
        """
        if not plugin.uuid:
            return False
        config = get_config()
        config_key = f'plugin.{plugin.uuid}'
        config.beginGroup(config_key)
        has_options = len(config.childKeys()) > 0
        config.endGroup()
        return has_options

    def _check_blacklisted_plugins(self):
        """Check installed plugins against blacklist and disable if needed.

        Returns:
            list: List of tuples (plugin_id, reason) for blacklisted plugins
        """
        blacklisted_plugins = []

        for plugin in self._plugins:
            # Get UUID from plugin manifest
            if not plugin.uuid:
                continue

            metadata = self._metadata.get_plugin_metadata(plugin.uuid)
            url = metadata.url if metadata else None

            # Create InstallablePlugin for blacklist checking
            installable_plugin = UrlInstallablePlugin(url, registry=self._registry)
            installable_plugin.plugin_uuid = plugin.uuid

            is_blacklisted, reason = installable_plugin.is_blacklisted()
            if is_blacklisted:
                log.warning('Plugin %s is blacklisted: %s', plugin.plugin_id, reason)
                blacklisted_plugins.append((plugin.plugin_id, reason))

                if plugin.uuid in self._enabled_plugins:
                    log.warning('Disabling blacklisted plugin %s', plugin.plugin_id)
                    self._enabled_plugins.discard(plugin.uuid)
                    self._save_config()

        return blacklisted_plugins

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        uuid = PluginValidation.get_plugin_uuid(plugin)
        assert plugin.state is not None
        log.debug('Enabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        got_enabled = False
        if self._tagger:
            plugin.load_module()
            # Only enable if not already enabled
            if plugin.state != PluginState.ENABLED:
                plugin.enable(self._tagger)
                got_enabled = True

        # Ensure UUID mapping is set for extension points
        if plugin.uuid:
            set_plugin_uuid(plugin.uuid, plugin.plugin_id)

        self._enabled_plugins.add(uuid)
        self._save_config()
        log.info('Plugin %s enabled (state: %s)', plugin.plugin_id, plugin.state.value)

        # Only trigger signal, if plugin wasn't already enabled
        if got_enabled:
            self.plugin_enabled.emit(plugin)
            self.plugin_state_changed.emit(plugin)

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration.

        Returns:
            list: List of tuples (plugin_id, reason) for blacklisted plugins found
        """
        # Check for blacklisted plugins on startup
        blacklisted_plugins = self._check_blacklisted_plugins()

        enabled_count = 0
        for plugin in self._plugins:
            if plugin.uuid and plugin.uuid in self._enabled_plugins:
                try:
                    log.info('Loading plugin: %s', plugin.manifest.name() if plugin.manifest else plugin.plugin_id)
                    plugin.load_module()
                    plugin.enable(self._tagger)
                    enabled_count += 1
                except Exception as ex:
                    log.error('Failed initializing plugin %s from %s', plugin.plugin_id, plugin.local_path, exc_info=ex)

        log.info('Loaded %d plugin%s', enabled_count, 's' if enabled_count != 1 else '')
        return blacklisted_plugins

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""
        uuid = PluginValidation.get_plugin_uuid(plugin)
        assert plugin.state is not None
        log.debug('Disabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        # Only disable if not already disabled
        got_disabled = False
        if plugin.state != PluginState.DISABLED:
            plugin.disable()
            got_disabled = True

        self._enabled_plugins.discard(uuid)
        self._save_config()
        log.info('Plugin %s disabled (state: %s)', plugin.plugin_id, plugin.state.value)

        # Only trigger signal, if plugin wasn't already disabled
        if got_disabled:
            self.plugin_disabled.emit(plugin)
            self.plugin_state_changed.emit(plugin)

    def _load_config(self):
        """Load enabled plugins list from config."""
        config = get_config()
        enabled = config.setting['plugins3_enabled_plugins']
        self._enabled_plugins = set(enabled)
        log.debug('Loaded enabled plugins from config: %r', self._enabled_plugins)

    def _save_config(self):
        """Save enabled plugins list to config."""
        config = get_config()
        config.setting['plugins3_enabled_plugins'] = list(self._enabled_plugins)
        if hasattr(config, 'sync'):
            config.sync()
        log.debug('Saved enabled plugins to config: %r', self._enabled_plugins)

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        """Load a plugin and check API version compatibility.

        Returns:
            Plugin object if compatible, None otherwise
        """
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()

            # Register UUID mapping early so extension points can find enabled plugins
            if plugin.uuid:
                set_plugin_uuid(plugin.uuid, plugin.plugin_id)

            assert plugin.manifest is not None
            compatible_versions = _compatible_api_versions(plugin.manifest.api_versions)
            if compatible_versions:
                log.debug(
                    'Plugin "%s" is compatible (requires API %s, Picard supports %s)',
                    plugin.plugin_id,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return plugin
            else:
                log.warning(
                    'Plugin "%s" from "%s" is not compatible with this version of Picard. '
                    'Plugin requires API versions %s, but Picard supports %s.',
                    plugin.plugin_id,
                    plugin.local_path,
                    plugin.manifest.api_versions,
                    api_versions_tuple,
                )
                return None
        except Exception as ex:
            error_msg = str(ex)
            log.warning('Could not read plugin manifest from %r', plugin_dir.joinpath(plugin_name), exc_info=ex)
            self._failed_plugins.append((plugin_dir, plugin_name, error_msg))
            return None


def _compatible_api_versions(api_versions):
    return set(api_versions) & set(api_versions_tuple)

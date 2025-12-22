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
import shutil
import tempfile
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
)

from picard import log


if TYPE_CHECKING:
    from picard.tagger import Tagger

from picard.const.appdirs import cache_folder
from picard.git.backend import GitRefType
from picard.git.factory import git_backend
from picard.git.ops import GitOperations
from picard.plugin3.manager.clean import PluginCleanupManager
from picard.plugin3.manager.find import PluginFinder
from picard.plugin3.manager.install import PluginInstaller, get_plugin_directory_name
from picard.plugin3.manager.lifecycle import PluginLifecycleManager
from picard.plugin3.manager.registry import PluginRegistryManager
from picard.plugin3.manager.update import PluginUpdater, UpdateAllResult
from picard.plugin3.manager.validation import PluginValidationManager
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
    hash_string,
    short_commit_id,
)
from picard.plugin3.plugin_metadata import PluginMetadata, PluginMetadataManager
from picard.plugin3.ref_item import RefItem
from picard.plugin3.registry import PluginRegistry
from picard.plugin3.validation import PluginValidation


try:
    from markdown import markdown as render_markdown
except ImportError:
    render_markdown = None


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


class PluginManifestError(PluginManagerError):
    """Base class for plugin manifest-related errors."""

    pass


class PluginManifestNotFoundError(PluginManifestError):
    """Raised when MANIFEST.toml is not found in plugin source."""

    def __init__(self, source):
        self.source = source
        super().__init__(f"No MANIFEST.toml found in {source}")


class PluginManifestReadError(PluginManifestError):
    """Raised when MANIFEST.toml cannot be read."""

    def __init__(self, e, source):
        self.source = source
        super().__init__(f"Failed to read MANIFEST.toml in {source}: {e}")


class PluginManifestInvalidError(PluginManifestError):
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


class PluginNoUUIDError(PluginManifestError):
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

        # Initialize lifecycle manager early since _load_config depends on it
        self._lifecycle_manager = PluginLifecycleManager(self)
        self._load_config()

        # Initialize registry for blacklist checking
        cache_dir = cache_folder()
        self._registry = PluginRegistry(cache_dir=cache_dir)

        # Initialize metadata manager
        self._metadata = PluginMetadataManager(self._registry)

        # Initialize installer
        self._installer = PluginInstaller(self)

        # Initialize updater
        self._updater = PluginUpdater(self)

        # Initialize registry manager
        self._registry_manager = PluginRegistryManager(self)

        # Initialize validation manager
        self._validation_manager = PluginValidationManager(self)

        # Initialize cleanup manager
        self._cleanup_manager = PluginCleanupManager(self)

        # Initialize finder
        self._finder = PluginFinder(self)

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

    def _with_plugin_repo(self, plugin_path, callback):
        """Execute callback with git repository context."""
        backend = git_backend()
        with backend.create_repository(plugin_path) as repo:
            return callback(repo)

    def _get_plugin_uuid_and_metadata(self, plugin):
        """Get plugin UUID and metadata in one call."""
        uuid = PluginValidation.get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)
        return uuid, metadata

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
            # Create RefItem object for formatting
            ref_item = RefItem(
                shortname=ref['name'],
                ref_type=RefItem.Type.TAG,
                commit=ref.get('commit', ''),
            )
            is_current = current_ref and ref['name'] == current_ref
            formatted_refs['tags'].append(
                {
                    'name': ref['name'],
                    'commit': ref.get('commit'),
                    'display_name': ref_item.format(is_current=is_current),
                }
            )

        # Format branches
        for ref in refs.get('branches', []):
            # Create RefItem object for formatting
            ref_item = RefItem(
                shortname=ref['name'],
                ref_type=RefItem.Type.BRANCH,
                commit=ref.get('commit', ''),
            )
            is_current = current_ref and ref['name'] == current_ref
            formatted_refs['branches'].append(
                {
                    'name': ref['name'],
                    'commit': ref.get('commit'),
                    'display_name': ref_item.format(is_current=is_current),
                }
            )

        return formatted_refs

    def fetch_all_git_refs(self, url):
        """Fetch all branches and tags from a git repository.

        Args:
            url: Git repository URL

        Returns:
            dict with keys:
                - branches: List of branch names
                - tags: List of tag names
            or None on error
        """
        # Check if we have an installed plugin for this URL to reuse its repository
        repo_path = None
        for plugin in self._plugins:
            if plugin.uuid:
                metadata = self._metadata.get_plugin_metadata(plugin.uuid)
                if metadata and metadata.url == url and plugin.local_path:
                    repo_path = plugin.local_path
                    break

        remote_refs = GitOperations.fetch_remote_refs(url, use_callbacks=True, repo_path=repo_path)
        if not remote_refs:
            return None

        # Separate branches and tags using GitRef metadata
        branches = []
        tags = []
        seen_branches = set()  # Track branch names to avoid duplicates

        # Process local branches first (they take precedence over remote)
        local_refs = [ref for ref in remote_refs if ref.ref_type == GitRefType.BRANCH and not ref.is_remote]
        remote_branch_refs = [ref for ref in remote_refs if ref.ref_type == GitRefType.BRANCH and ref.is_remote]

        # Add local branches first
        for ref in local_refs:
            branch_name = ref.shortname
            seen_branches.add(branch_name)
            branches.append({'name': branch_name, 'commit': ref.target})

        # Add remote branches only if not already seen
        for ref in remote_branch_refs:
            # Strip remote prefix (e.g., "origin/main" -> "main")
            branch_name = ref.shortname.split('/', 1)[-1] if '/' in ref.shortname else ref.shortname

            # Skip if we've already seen this branch name (local takes precedence)
            if branch_name in seen_branches:
                continue

            seen_branches.add(branch_name)
            branches.append({'name': branch_name, 'commit': ref.target})

        # Process tags
        for ref in remote_refs:
            if ref.ref_type == GitRefType.TAG:
                # GitRef backend handles dereferencing using pygit2.peel()
                tags.append({'name': ref.shortname, 'commit': ref.target})

        result = {
            'branches': sorted(branches, key=lambda x: x['name']),
            'tags': sorted(tags, key=lambda x: x['name'], reverse=True),
        }

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
        """Find a plugin by Plugin ID, display name, UUID, registry ID, or any prefix."""
        return self._finder.find_plugin(identifier)

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

        git_ref = metadata.get_git_ref()
        ref_shortname = git_ref.shortname
        commit = metadata.commit or ''

        # If ref looks like a version tag (not a commit hash), use it
        if ref_shortname and commit and not ref_shortname.startswith(short_commit_id(commit)):
            return ref_shortname

        return manifest_version

    def _save_plugin_metadata(self, metadata):
        """Save plugin metadata."""
        return self._metadata.save_plugin_metadata(metadata)

    def _find_plugin_by_url(self, url):
        """Find plugin metadata by URL."""
        return self._finder._find_plugin_by_url(url)

    def _get_plugin_uuid(self, plugin):
        """Get plugin UUID."""
        return PluginValidation.get_plugin_uuid(plugin)

    def _read_and_validate_manifest(self, path, source_description):
        """Read and validate manifest."""
        return self._validation_manager._read_and_validate_manifest(path, source_description)

    def _clean_plugin_config(self, plugin_uuid):
        """Delete plugin configuration."""
        return self._cleanup_manager._clean_plugin_config(plugin_uuid)

    def get_orphaned_plugin_configs(self):
        """Get list of plugin configs that don't have corresponding installed plugins."""
        return self._cleanup_manager.get_orphaned_plugin_configs()

    def _check_uuid_conflict(self, manifest, source_url):
        """Check if plugin UUID conflicts with existing plugin from different source."""
        return self._validation_manager._check_uuid_conflict(manifest, source_url)

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
        return self._registry_manager._fetch_version_tags(url, versioning_scheme)

    def select_ref_for_plugin(self, plugin):
        """Select appropriate ref for plugin based on versioning scheme or Picard API version."""
        return self._registry_manager.select_ref_for_plugin(plugin)

    def search_registry_plugins(self, query=None, category=None, trust_level=None):
        """Search registry plugins with optional filters."""
        return self._registry_manager.search_registry_plugins(query, category, trust_level)

    def find_similar_plugin_ids(self, query, max_results=10):
        """Find similar plugin IDs for suggestions."""
        return self._registry_manager.find_similar_plugin_ids(query, max_results)

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
        """Switch plugin to a different git ref.

        Args:
            plugin: Plugin to switch
            ref: Git ref to switch to (string or GitRef object)
            discard_changes: If True, discard uncommitted changes
        """
        return self._updater.switch_ref(plugin, ref, discard_changes)

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

    def _rollback_plugin_to_commit(self, plugin, commit_id):
        """Rollback plugin to a specific commit after failed update.

        Args:
            plugin: Plugin to rollback
            commit_id: Commit ID to rollback to

        Raises:
            Exception: If rollback fails
        """
        log.warning('Rolling back plugin %s to commit %s', plugin.plugin_id, commit_id)
        try:

            def rollback_operation(repo):
                repo.reset_to_commit(commit_id, hard=True)

            self._with_plugin_repo(plugin.local_path, rollback_operation)
            log.debug('Git rollback completed for plugin %s', plugin.plugin_id)
        except Exception as git_error:
            log.error('Git rollback failed for plugin %s: %s', plugin.plugin_id, git_error)
            raise

        # Re-read manifest from rolled back version
        try:
            plugin.read_manifest()
            log.debug('Manifest re-read successful after rollback for plugin %s', plugin.plugin_id)
        except Exception as manifest_error:
            log.error('Failed to read manifest after rollback for plugin %s: %s', plugin.plugin_id, manifest_error)
            raise

    def _cleanup_failed_plugin_install(self, plugin, plugin_name, final_path):
        """Clean up failed plugin installation by removing plugin and directory.

        Args:
            plugin: Plugin object to remove
            plugin_name: Name of the plugin for logging
            final_path: Path to plugin directory to remove
        """
        try:
            # Remove from plugins list
            if plugin in self._plugins:
                self._plugins.remove(plugin)
            # Remove plugin directory
            self._safe_remove_directory(final_path, f"failed plugin directory for {plugin_name}")
            log.info('Successfully cleaned up failed plugin installation: %s', plugin_name)
        except Exception as cleanup_error:
            log.error('Failed to cleanup plugin %s after enable failure: %s', plugin_name, cleanup_error)

    def _safe_remove_directory(self, path, description="directory"):
        """Safely remove a directory with error logging.

        Args:
            path: Path to remove (Path object or string)
            description: Description for logging (default: "directory")
        """
        path = Path(path)
        if path.exists():
            try:
                # Force garbage collection to release file handles on Windows
                gc.collect()
                shutil.rmtree(path)
                log.debug('Cleaned up %s: %s', description, path)
            except Exception as e:
                log.error('Failed to remove %s %s: %s', description, path, e)

    def _validate_manifest_or_rollback(self, plugin, old_commit, was_enabled):
        """Validate plugin manifest after git operations, rollback on failure."""
        return self._validation_manager._validate_manifest_or_rollback(plugin, old_commit, was_enabled)

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
        return self._installer.install_plugin(
            url, ref, reinstall, force_blacklisted, discard_changes, enable_after_install
        )

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

                def check_status(source_repo):
                    if source_repo.get_status():
                        log.warning('Installing from local repository with uncommitted changes: %s', local_path)

                    # If no ref specified, use the current branch
                    if not ref and not source_repo.is_head_detached():
                        current_ref = source_repo.get_head_shorthand()
                        log.debug('Using current branch from local repo: %s', current_ref)
                        return current_ref
                    return ref

                ref = self._with_plugin_repo(local_path, check_status)
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
                ref_type_to_save = source.resolved_ref_type
                commit_to_save = commit_id
            except Exception:
                # Clean up temp directory on failure
                self._safe_remove_directory(temp_path, "temp directory after git sync failure")
                raise
        else:
            # All plugins must be git repositories
            raise ValueError(
                f"Plugin directory {local_path} is not a git repository. All plugins must be git repositories."
            )

        # Read MANIFEST to get plugin ID
        try:
            manifest = PluginValidation.read_and_validate_manifest(install_path, local_path)
        except Exception:
            # Clean up temp directory if manifest validation fails
            self._safe_remove_directory(temp_path, "temp directory after manifest validation failure")
            raise

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

            self._safe_remove_directory(final_path, f"existing plugin directory for {plugin_name}")

        # Copy to plugin directory
        # Move from temp location (git repo was cloned to temp)
        shutil.move(str(install_path), str(final_path))

        # Store metadata
        self._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin_name,
                url=str(local_path),
                ref=ref_to_save or '',
                commit=commit_to_save or '',
                uuid=manifest.uuid,
                ref_type=ref_type_to_save,
            )
        )

        # Add newly installed plugin to the plugins list
        plugin = Plugin(self._primary_plugin_dir, plugin_name, uuid=manifest.uuid)
        self._plugins.append(plugin)

        # Enable plugin if requested
        if enable_after_install:
            try:
                self.enable_plugin(plugin)
            except PluginManifestError as e:
                # Remove installed plugin on manifest validation failure during enable
                log.error('Local plugin installation failed during enable due to manifest error: %s', e)
                self._cleanup_failed_plugin_install(plugin, plugin_name, final_path)
                # Re-raise the original error
                raise

        log.info('Plugin %s installed from local directory %s', plugin_name, local_path)
        return plugin_name

    def _find_newer_version_tag(self, url, current_tag, versioning_scheme):
        """Find newer version tag for plugin with versioning_scheme."""
        return self._registry_manager._find_newer_version_tag(url, current_tag, versioning_scheme)

    def update_plugin(self, plugin, discard_changes=False):
        """Update a single plugin to latest version."""
        return self._updater.update_plugin(plugin, discard_changes)

    def _create_ref_item_from_metadata(self, ref_name, commit, ref_type):
        """Create RefItem from metadata information."""
        return self._updater._create_ref_item(ref_name, commit, ref_type)

    def _create_ref_item_from_source(self, source, commit):
        """Create RefItem from PluginSourceGit with accurate ref type information."""
        return self._updater._create_ref_item(source.ref, commit, getattr(source, 'resolved_ref_type', None))

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

    def _is_commit_pin(self, metadata):
        """Check if plugin is pinned to a commit (not updatable)."""
        # Use ref_type to reliably determine if plugin was installed as a commit
        return metadata.ref_type == 'commit'

    def _get_current_ref_for_updates(self, repo, metadata):
        """Get the current ref to use for update checking.

        When in detached HEAD, finds the first local branch instead of using commit hash.

        Returns:
            tuple: (ref_name, is_detached_head)
        """
        if repo.is_head_detached():
            # Detached HEAD - use the first local branch for update checking
            for git_ref in repo.list_references():
                if git_ref.ref_type == GitRefType.BRANCH and not git_ref.is_remote:
                    return git_ref.shortname, True
            # Fall back to stored metadata ref or default to main
            return metadata.ref or 'main', True
        else:
            # On a branch - use the actual branch name
            return repo.get_head_shorthand(), False

    def _should_fetch_plugin_refs(self, plugin, metadata):
        """Check if a plugin should have its refs fetched."""
        if not plugin.uuid or not metadata or not metadata.url:
            return False

        # Only fetch refs for plugins with remote URLs or local git repos
        # Local plugins without remotes can't be updated anyway
        return True

    def refresh_all_plugin_refs(self):
        """Fetch remote refs for all plugins to ensure ref selectors have latest data."""
        for plugin in self._plugins:
            metadata = self._metadata.get_plugin_metadata(plugin.uuid) if plugin.uuid else None
            if not self._should_fetch_plugin_refs(plugin, metadata):
                continue

            try:

                def fetch_refs(repo):
                    # Fetch without updating (suppress progress output)
                    backend = git_backend()
                    callbacks = backend.create_remote_callbacks()
                    for remote in repo.get_remotes():
                        # Fetch all refs including tags in a single operation
                        repo.fetch_remote_with_tags(remote, None, callbacks._callbacks)
                        log.debug("Fetched refs for plugin %s from remote %s", plugin.plugin_id, remote.name)

                self._with_plugin_repo(plugin.local_path, fetch_refs)
            except Exception as e:
                log.warning("Failed to fetch refs for plugin %s: %s", plugin.plugin_id, e)

    def _check_single_plugin_update(self, plugin, metadata, skip_fetch):
        """Check update status for a single plugin."""
        return self._updater._check_single_plugin_update(plugin, metadata, skip_fetch)

    def check_updates(self, skip_fetch=False):
        """Check which plugins have updates available without installing."""
        return self._updater.check_updates(skip_fetch)

    def get_plugin_update_status(self, plugin):
        """Check if a single plugin has an update available."""
        log.debug("Checking update status for plugin: %s", plugin.plugin_id)

        # FIXME
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

        git_ref = metadata.get_git_ref()
        # Convert GitRef to RefItem for formatting
        ref_item = RefItem.from_git_ref(git_ref)
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
        """Uninstall a plugin."""
        return self._lifecycle_manager.uninstall_plugin(plugin, purge)

    def plugin_has_saved_options(self, plugin: Plugin) -> bool:
        """Check if a plugin has any saved options."""
        return self._lifecycle_manager.plugin_has_saved_options(plugin)

    def _check_blacklisted_plugins(self):
        """Check installed plugins against blacklist and disable if needed."""
        return self._lifecycle_manager._check_blacklisted_plugins()

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        return self._lifecycle_manager.enable_plugin(plugin)

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration."""
        return self._lifecycle_manager.init_plugins()

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""
        return self._lifecycle_manager.disable_plugin(plugin)

    def _load_config(self):
        """Load enabled plugins list from config."""
        return self._lifecycle_manager._load_config()

    def _save_config(self):
        """Save enabled plugins list to config."""
        return self._lifecycle_manager._save_config()

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        """Load a plugin and check API version compatibility."""
        return self._lifecycle_manager._load_plugin(plugin_dir, plugin_name)

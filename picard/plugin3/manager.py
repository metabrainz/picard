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

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import re
import shutil
from typing import List, NamedTuple

from picard import (
    api_versions_tuple,
    log,
)
from picard.plugin3.plugin import (
    Plugin,
    PluginSourceGit,
    PluginState,
    short_commit_id,
)


@dataclass
class PluginMetadata:
    """Plugin metadata stored in config."""

    name: str
    url: str
    ref: str
    commit: str
    uuid: str = None
    original_url: str = None
    original_uuid: str = None

    def to_dict(self):
        """Convert to dict for config storage, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


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

    def __init__(self, plugin_id, ref, available_refs):
        self.plugin_id = plugin_id
        self.ref = ref
        self.available_refs = available_refs
        super().__init__(f"Ref '{ref}' not found for plugin {plugin_id}")


class PluginNoUUIDError(PluginManagerError):
    """Raised when plugin has no UUID in manifest."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id} has no UUID")


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


class PluginManager:
    """Installs, loads and updates plugins from multiple plugin directories."""

    _primary_plugin_dir: Path = None
    _plugin_dirs: List[Path] = []
    _plugins: List[Plugin] = []

    def __init__(self, tagger=None):
        from picard.tagger import Tagger

        self._tagger: Tagger | None = tagger
        self._enabled_plugins = set()
        self._failed_plugins = []  # List of (path, name, error_message) tuples
        self._load_config()

        # Initialize registry for blacklist checking
        from picard.const.appdirs import cache_folder
        from picard.plugin3.registry import PluginRegistry

        cache_dir = cache_folder()
        self._registry = PluginRegistry(cache_dir=cache_dir)

        # Initialize refs cache
        from picard.plugin3.refs_cache import RefsCache

        self._refs_cache = RefsCache(self._registry)

        # Initialize metadata manager
        from picard.plugin3.plugin_metadata import PluginMetadataManager

        self._metadata = PluginMetadataManager(self, self._registry)

        # Register cleanup and clean up any leftover temp directories
        if tagger:
            tagger.register_cleanup(self._cleanup_temp_directories)
        self._cleanup_temp_directories()

    @property
    def plugins(self):
        return self._plugins

    def _cleanup_temp_directories(self):
        """Remove leftover temporary plugin directories from failed installs."""
        if not self._primary_plugin_dir or not self._primary_plugin_dir.exists():
            return

        for entry in self._primary_plugin_dir.iterdir():
            if entry.is_dir() and entry.name.startswith('.tmp-'):
                shutil.rmtree(entry, ignore_errors=True)
                log.debug('Cleaned up temporary plugin directory: %s', entry)

    def _check_dirty_working_dir(self, path: Path):
        """Check if directory has uncommitted changes.

        Returns:
            list: Modified files, or empty list if clean
        """
        try:
            import pygit2

            repo = pygit2.Repository(str(path))
            status = repo.status()
            if status:
                return [file for file, flags in status.items()]
        except Exception:
            pass  # Not a git repo or error checking
        return []

    def _validate_manifest(self, manifest):
        """Validate manifest and raise PluginManifestInvalidError if invalid."""
        errors = manifest.validate()
        if errors:
            raise PluginManifestInvalidError(errors)

    def _read_and_validate_manifest(self, path, source_description):
        """Read MANIFEST.toml from path and validate it.

        Args:
            path: Directory path containing MANIFEST.toml
            source_description: Description of source for error messages (e.g., URL or path)

        Returns:
            PluginManifest: Validated manifest

        Raises:
            PluginManifestNotFoundError: If MANIFEST.toml doesn't exist
            PluginManifestInvalidError: If manifest validation fails
        """
        from picard.plugin3.manifest import PluginManifest

        manifest_path = path / 'MANIFEST.toml'
        if not manifest_path.exists():
            raise PluginManifestNotFoundError(source_description)

        with open(manifest_path, 'rb') as f:
            manifest = PluginManifest('temp', f)

        self._validate_manifest(manifest)
        return manifest

    def _get_plugin_uuid(self, plugin: Plugin):
        """Get plugin UUID, raising PluginNoUUIDError if not available."""
        if not plugin.manifest or not plugin.manifest.uuid:
            raise PluginNoUUIDError(plugin.plugin_id)
        return plugin.manifest.uuid

    def _fetch_remote_refs(self, url, use_callbacks=True):
        """Fetch remote refs from a git repository.

        Args:
            url: Git repository URL
            use_callbacks: Whether to use GitRemoteCallbacks for authentication

        Returns:
            list: Remote refs from pygit2, or None on error
        """
        import tempfile

        import pygit2

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = pygit2.init_repository(tmpdir, bare=True)
                remote = repo.remotes.create('origin', url)

                if use_callbacks:
                    from picard.plugin3.plugin import GitRemoteCallbacks

                    callbacks = GitRemoteCallbacks()
                    return remote.list_heads(callbacks=callbacks)
                else:
                    return remote.list_heads()

        except Exception as e:
            log.warning('Failed to fetch remote refs from %s: %s', url, e)
            return None

    def fetch_all_git_refs(self, url, use_cache=True):
        """Fetch all branches and tags from a git repository.

        Args:
            url: Git repository URL
            use_cache: Whether to use cached data if available

        Returns:
            dict with keys:
                - branches: List of branch names
                - tags: List of tag names
            or None on error
        """
        # Check cache first
        if use_cache:
            cached_refs = self._refs_cache.get_cached_all_refs(url)
            if cached_refs is not None:
                return cached_refs

        remote_refs = self._fetch_remote_refs(url, use_callbacks=True)
        if not remote_refs:
            # Try to use expired cache as fallback
            if use_cache:
                stale_cache = self._refs_cache.get_cached_all_refs(url, allow_expired=True)
                if stale_cache:
                    log.info('Using stale refs cache for %s due to fetch error', url)
                    return stale_cache
            return None

        # Separate branches and tags
        branches = []
        tags = []

        for ref in remote_refs:
            ref_name = ref.name if hasattr(ref, 'name') else str(ref)
            if ref_name.startswith('refs/heads/'):
                branch_name = ref_name[len('refs/heads/') :]
                branches.append(branch_name)
            elif ref_name.startswith('refs/tags/'):
                tag_name = ref_name[len('refs/tags/') :]
                tags.append(tag_name)

        result = {'branches': sorted(branches), 'tags': sorted(tags, reverse=True)}

        # Cache the result
        if use_cache:
            self._refs_cache.cache_all_refs(url, result)

        return result

    def _get_config_value(self, *keys, default=None):
        """Get nested config value by keys.

        Args:
            *keys: Nested keys to traverse
            default: Default value if key path doesn't exist

        Returns:
            Config value or default
        """
        from picard.config import get_config

        config = get_config()
        value = config.setting
        for key in keys:
            try:
                # Try dict-like access (works for both dict and SettingConfigSection)
                if key in value:
                    value = value[key]
                else:
                    return default
            except (TypeError, KeyError):
                return default
        return value

    def _set_config_value(self, *keys, value):
        """Set nested config value by keys, creating intermediate dicts as needed.

        Args:
            *keys: Nested keys to traverse (last key is where value is set)
            value: Value to set
        """
        from picard.config import get_config

        config = get_config()
        current = config.setting

        # Navigate/create path to parent
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

        # Reassign top-level to persist (required by config system)
        config.setting[keys[0]] = config.setting[keys[0]]

    def add_directory(self, dir_path: str, primary: bool = False) -> None:
        dir_path = Path(os.path.normpath(dir_path))
        if dir_path in self._plugin_dirs:
            log.warning('Plugin directory %s already registered', dir_path)
            return

        log.debug('Registering plugin directory %s', dir_path)
        if not dir_path.exists():
            os.makedirs(dir_path)

        for entry in dir_path.iterdir():
            if entry.is_dir() and not entry.name.startswith('.'):
                plugin = self._load_plugin(dir_path, entry.name)
                if plugin:
                    log.debug('Found plugin %s in %s', plugin.plugin_id, plugin.local_path)
                    self._plugins.append(plugin)

        self._plugin_dirs.append(dir_path)
        if primary:
            self._primary_plugin_dir = dir_path

    def install_plugin(self, url, ref=None, reinstall=False, force_blacklisted=False, discard_changes=False):
        """Install a plugin from a git URL or local directory.

        Args:
            url: Git repository URL or local directory path
            ref: Git ref (branch/tag/commit) to checkout (ignored for local paths)
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
            discard_changes: If True, discard uncommitted changes on reinstall

        Raises:
            PluginDirtyError: If reinstalling and plugin has uncommitted changes
        """

        from picard.plugin3.registry import get_local_repository_path

        # Check blacklist before installing
        if not force_blacklisted:
            is_blacklisted, reason = self._registry.is_blacklisted(url)
            if is_blacklisted:
                raise PluginBlacklistedError(url, reason)

        # Check if url is a local directory
        local_path = get_local_repository_path(url)
        if local_path:
            return self._install_from_local_directory(local_path, reinstall, force_blacklisted, ref, discard_changes)

        # Handle git URL - use temp dir in plugin directory for atomic rename
        from picard.plugin3.plugin import hash_string

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
            commit_id = source.sync(temp_path, single_branch=True)

            # Read MANIFEST to get plugin ID
            manifest = self._read_and_validate_manifest(temp_path, url)

            # Generate plugin directory name from sanitized name + UUID
            plugin_name = get_plugin_directory_name(manifest)

            # Check blacklist again with UUID
            if not force_blacklisted:
                is_blacklisted, reason = self._registry.is_blacklisted(url, manifest.uuid)
                if is_blacklisted:
                    raise PluginBlacklistedError(url, reason, manifest.uuid)

            final_path = self._primary_plugin_dir / plugin_name

            # Check if already installed and handle reinstall
            if final_path.exists():
                if not reinstall:
                    raise PluginAlreadyInstalledError(plugin_name, url)

                # Check for uncommitted changes before removing
                if not discard_changes:
                    changes = self._check_dirty_working_dir(final_path)
                    if changes:
                        raise PluginDirtyError(plugin_name, changes)

                shutil.rmtree(final_path)

            # Atomic rename from temp to final location
            temp_path.rename(final_path)

            # Update version tag cache from cloned repo if plugin has versioning_scheme
            registry_plugin = self._registry.find_plugin(url=url)
            if registry_plugin:
                versioning_scheme = registry_plugin.get('versioning_scheme')
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

            return plugin_name

        except Exception:
            # Clean up temp directory on failure
            if temp_path.exists():
                import gc

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
    ):
        """Install a plugin from a local directory.

        Args:
            local_path: Path to local plugin directory
            reinstall: If True, reinstall even if already exists
            force_blacklisted: If True, bypass blacklist check (dangerous!)
            ref: Git ref to checkout if local_path is a git repository
            discard_changes: If True, discard uncommitted changes on reinstall

        Returns:
            str: Plugin ID
        """
        import tempfile

        # Check if local directory is a git repository
        is_git_repo = (local_path / '.git').exists()

        if is_git_repo:
            # Check if source repository has uncommitted changes
            try:
                import pygit2

                source_repo = pygit2.Repository(str(local_path))
                if source_repo.status():
                    log.warning('Installing from local repository with uncommitted changes: %s', local_path)

                # If no ref specified, use the current branch
                if not ref and not source_repo.head_is_detached:
                    ref = source_repo.head.shorthand
                    log.debug('Using current branch from local repo: %s', ref)
            except Exception:
                pass  # Ignore errors checking status

            # Use git operations to get ref and commit info
            from picard.plugin3.plugin import hash_string

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
                    import gc

                    gc.collect()
                    shutil.rmtree(temp_path, ignore_errors=True)
                raise
        else:
            # Direct copy for non-git directories
            install_path = local_path
            ref_to_save = ''
            commit_to_save = ''

        # Read MANIFEST to get plugin ID
        manifest = self._read_and_validate_manifest(install_path, local_path)

        # Generate plugin directory name from sanitized name + UUID
        plugin_name = get_plugin_directory_name(manifest)
        final_path = self._primary_plugin_dir / plugin_name

        # Check if already installed and handle reinstall
        if final_path.exists():
            if not reinstall:
                raise PluginAlreadyInstalledError(plugin_name, local_path)

            # Check for uncommitted changes before removing
            if not discard_changes:
                changes = self._check_dirty_working_dir(final_path)
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
                ref=ref_to_save,
                commit=commit_to_save,
                uuid=manifest.uuid,
            )
        )

        # Add newly installed plugin to the plugins list
        plugin = Plugin(self._primary_plugin_dir, plugin_name)
        self._plugins.append(plugin)

        log.info('Plugin %s installed from local directory %s', plugin_name, local_path)
        return plugin_name

    def _validate_ref(self, url, ref, uuid=None):
        """Validate that a ref exists and is available.

        Args:
            url: Git repository URL
            ref: Ref to validate
            uuid: Plugin UUID for registry lookup

        Returns:
            tuple: (is_valid, available_refs) where available_refs is a list of dicts
                   with 'name' and optional 'description' keys

        Raises:
            None - returns validation result instead
        """
        registry_plugin = self._registry.find_plugin(url=url, uuid=uuid)
        # Ensure registry_plugin is a dict, not a pygit2 object
        if registry_plugin and not isinstance(registry_plugin, dict):
            log.warning('registry_plugin is not a dict, got %s', type(registry_plugin))
            return True, []

        versioning_scheme = registry_plugin.get('versioning_scheme') if registry_plugin else None

        # If plugin has versioning_scheme, validate against version tags
        if versioning_scheme:
            tag_names = self._fetch_version_tags(url, versioning_scheme)
            if tag_names:
                tags = [{'name': tag} for tag in tag_names]
                if tags:
                    tags[0]['description'] = 'latest'
                is_valid = any(t['name'] == ref for t in tags)
                return is_valid, tags

        # If plugin has explicit refs in registry, validate against those
        if registry_plugin and registry_plugin.get('refs'):
            refs = registry_plugin['refs']
            # Ensure refs is a list (not a pygit2 References object)
            if not isinstance(refs, list):
                return True, []

            available = []
            for r in refs:
                ref_dict = {'name': r['name']}
                if r.get('description'):
                    ref_dict['description'] = r['description']
                available.append(ref_dict)

            is_valid = any(r['name'] == ref for r in refs)
            return is_valid, available

        # No validation possible - assume valid
        return True, []

    def _is_immutable_ref(self, ref):
        """Check if a ref is immutable (commit hash or non-version tag).

        Args:
            ref: Git ref (branch, tag, or commit)

        Returns:
            tuple: (is_immutable, ref_type) where ref_type is 'tag', 'commit', or None
        """
        if not ref:
            return False, None

        # Check if it looks like a commit hash (7-40 hex chars)
        if len(ref) >= 7 and len(ref) <= 40 and all(c in '0123456789abcdef' for c in ref.lower()):
            return True, 'commit'

        # Check if it starts with 'v' followed by a number (common tag pattern)
        # or contains dots (version-like: 1.0.0, v2.1.3, etc)
        if ref.startswith('v') and len(ref) > 1 and ref[1].isdigit():
            return True, 'tag'
        if '.' in ref and any(c.isdigit() for c in ref):
            return True, 'tag'

        return False, None

    def switch_ref(self, plugin: Plugin, ref: str, discard_changes=False):
        """Switch plugin to a different git ref (branch/tag/commit).

        Args:
            plugin: Plugin to switch
            ref: Git ref to switch to
            discard_changes: If True, discard uncommitted changes

        Raises:
            PluginDirtyError: If plugin has uncommitted changes and discard_changes=False
            PluginRefNotFoundError: If ref is invalid and validation is available
        """
        # Check for uncommitted changes
        if not discard_changes:
            changes = self._check_dirty_working_dir(plugin.local_path)
            if changes:
                raise PluginDirtyError(plugin.plugin_id, changes)

        uuid = self._get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)
        if not metadata or 'url' not in metadata:
            raise PluginNoSourceError(plugin.plugin_id, 'switch ref')

        # Validate ref (if possible)
        try:
            is_valid, available_refs = self._validate_ref(metadata['url'], ref, uuid)
            # Ensure available_refs is always a list
            if not isinstance(available_refs, list):
                log.warning('available_refs is not a list, got %s', type(available_refs))
                available_refs = []
            if not is_valid and available_refs:
                raise PluginRefNotFoundError(plugin.plugin_id, ref, available_refs)
        except PluginRefNotFoundError:
            raise  # Re-raise our own exception
        except Exception as e:
            log.warning('Could not validate ref: %s', e)
            # Continue anyway - let git handle the validation

        old_ref = metadata.get('ref', 'main')
        old_commit = metadata.get('commit', 'unknown')

        source = PluginSourceGit(metadata['url'], ref)
        new_commit = source.sync(plugin.local_path, fetch_ref=True)

        # Reload manifest to get potentially new version
        try:
            plugin.read_manifest()
        except ValueError as e:
            # Validation failed - rollback to old commit (not just ref name)
            log.warning('Manifest validation failed, rolling back to %s (%s)', old_ref, old_commit)
            if old_commit and old_commit != 'unknown':
                rollback_source = PluginSourceGit(metadata['url'], old_commit)
            else:
                rollback_source = PluginSourceGit(metadata['url'], old_ref)
            rollback_source.sync(plugin.local_path)
            plugin.read_manifest()  # Restore old manifest
            raise PluginRefSwitchError(plugin.plugin_id, ref, e) from e

        # Update metadata with new ref
        self._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin.plugin_id,
                url=metadata['url'],
                ref=ref,
                commit=new_commit,
                uuid=metadata.get('uuid'),
                original_url=metadata.get('original_url'),
                original_uuid=metadata.get('original_uuid'),
            )
        )

        return old_ref, ref, old_commit, new_commit

        # Check if it starts with 'v' followed by a number (common tag pattern)
        # or contains dots (version-like: 1.0.0, v2.1.3, etc)
        if ref.startswith('v') and len(ref) > 1 and ref[1].isdigit():
            return True, 'tag'
        if '.' in ref and any(c.isdigit() for c in ref):
            return True, 'tag'

        return False, None

    def _fetch_version_tags(self, url, versioning_scheme):
        """Fetch and filter version tags from repository.

        Args:
            url: Git repository URL
            versioning_scheme: Versioning scheme (semver, calver, or regex:<pattern>)

        Returns:
            list: Sorted list of version tags (newest first), or empty list on error
        """
        # Check cache first
        cached_tags = self._refs_cache.get_cached_tags(url, versioning_scheme)
        if cached_tags is not None:
            return cached_tags

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
        tags = [tag for tag in all_refs.get('tags', []) if pattern.match(tag)]
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
        from packaging import version

        tags = self._fetch_version_tags(url, versioning_scheme)
        if not tags:
            return None

        # Use version parsing for semver/calver, lexicographic for custom regex
        if versioning_scheme in ('semver', 'calver'):
            try:
                import re

                # Strip any non-digit prefix for version comparison
                def strip_prefix(tag):
                    match = re.search(r'\d', tag)
                    return tag[match.start() :] if match else tag

                current_version = version.parse(strip_prefix(current_tag))
                for tag in tags:
                    tag_version = version.parse(strip_prefix(tag))
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
        # Check for uncommitted changes
        if not discard_changes:
            changes = self._check_dirty_working_dir(plugin.local_path)
            if changes:
                raise PluginDirtyError(plugin.plugin_id, changes)

        uuid = self._get_plugin_uuid(plugin)
        metadata = self._metadata.get_plugin_metadata(uuid)
        if not metadata or 'url' not in metadata:
            raise PluginNoSourceError(plugin.plugin_id, 'update')

        # Check if pinned to a specific commit (not tag - tags can be updated to newer tags)
        ref = metadata.get('ref')
        if ref:
            is_immutable, ref_type = self._is_immutable_ref(ref)
            if is_immutable and ref_type == 'commit':
                raise ValueError(f'Plugin is pinned to commit "{ref}" and cannot be updated')

        old_version = str(plugin.manifest.version) if plugin.manifest else 'unknown'
        old_url = metadata['url']
        old_uuid = metadata.get('uuid')
        old_ref = metadata.get('ref')

        # Check registry for redirects
        current_url, current_uuid, redirected = self._metadata.check_redirects(old_url, old_uuid)

        # Check if plugin has versioning_scheme and current ref is a version tag
        new_ref = old_ref
        registry_plugin = self._registry.find_plugin(url=current_url, uuid=current_uuid)
        if registry_plugin and registry_plugin.get('versioning_scheme'):
            is_immutable, ref_type = self._is_immutable_ref(old_ref)
            if is_immutable and ref_type == 'tag':
                # Try to find newer version tags
                newer_tag = self._find_newer_version_tag(current_url, old_ref, registry_plugin['versioning_scheme'])
                if newer_tag:
                    new_ref = newer_tag
                    log.info('Found newer version: %s -> %s', old_ref, new_ref)

        source = PluginSourceGit(current_url, new_ref)
        old_commit, new_commit = source.update(plugin.local_path, single_branch=True)

        # Get commit date
        import pygit2

        repo = pygit2.Repository(plugin.local_path.absolute())
        obj = repo.get(new_commit)
        # Peel tag to commit if needed
        if obj.type == pygit2.GIT_OBJECT_TAG:
            commit = obj.peel(pygit2.GIT_OBJECT_COMMIT)
        else:
            commit = obj
        commit_date = commit.commit_time
        repo.free()

        # Reload manifest to get new version
        plugin.read_manifest()
        new_version = str(plugin.manifest.version) if plugin.manifest else 'unknown'
        new_ref = source.ref  # May have been updated to a newer tag

        # Update metadata with current URL and UUID
        # If redirected, preserve original URL/UUID
        # Use source.ref which may have been updated to a newer tag
        original_url, original_uuid = self._metadata.get_original_metadata(metadata, redirected, old_url, old_uuid)
        self._metadata.save_plugin_metadata(
            PluginMetadata(
                name=plugin.plugin_id,
                url=current_url,
                ref=new_ref,
                commit=new_commit,
                uuid=current_uuid,
                original_url=original_url,
                original_uuid=original_uuid,
            )
        )

        # Update version tag cache from updated repo
        if registry_plugin and registry_plugin.get('versioning_scheme'):
            self._refs_cache.update_cache_from_local_repo(
                plugin.local_path, current_url, registry_plugin['versioning_scheme']
            )

        return UpdateResult(old_version, new_version, old_commit, new_commit, old_ref, new_ref, commit_date)

    def update_all_plugins(self):
        """Update all installed plugins."""
        results = []
        for plugin in self._plugins:
            try:
                result = self.update_plugin(plugin)
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=True, result=result, error=None))
            except Exception as e:
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=False, result=None, error=str(e)))
        return results

    def check_updates(self):
        """Check which plugins have updates available without installing."""
        updates = []
        for plugin in self._plugins:
            if not plugin.manifest or not plugin.manifest.uuid:
                continue

            metadata = self._metadata.get_plugin_metadata(plugin.manifest.uuid)
            if not metadata or 'url' not in metadata:
                continue

            try:
                import pygit2

                repo = pygit2.Repository(plugin.local_path.absolute())
                current_commit = str(repo.head.target)

                # Fetch without updating (suppress progress output)
                for remote in repo.remotes:
                    remote.fetch()

                # Update version tag cache from fetched repo if plugin has versioning_scheme
                registry_plugin = self._registry.find_plugin(url=metadata['url'])
                if registry_plugin and registry_plugin.get('versioning_scheme'):
                    self._refs_cache.update_cache_from_local_repo(
                        plugin.local_path, metadata['url'], registry_plugin['versioning_scheme']
                    )

                old_ref = metadata.get('ref', 'main')
                ref = old_ref

                # Check if currently on a tag
                current_is_tag = False
                current_tag = None
                if ref:
                    try:
                        repo.revparse_single(f'refs/tags/{ref}')
                        current_is_tag = True
                        current_tag = ref
                    except KeyError:
                        pass

                # If on a tag, check for newer version tag
                new_ref = None
                if current_is_tag and current_tag:
                    from picard.plugin3.plugin import PluginSourceGit

                    source = PluginSourceGit(metadata['url'], ref)
                    latest_tag = source._find_latest_tag(repo, current_tag)
                    if latest_tag and latest_tag != current_tag:
                        # Found newer tag
                        ref = latest_tag
                        new_ref = latest_tag

                # Resolve ref with same logic as update() - try origin/ prefix for branches
                try:
                    if not ref.startswith('origin/') and not ref.startswith('refs/'):
                        # Try origin/ prefix first for branches
                        try:
                            obj = repo.revparse_single(f'origin/{ref}')
                        except KeyError:
                            # Fall back to original ref (might be tag or commit hash)
                            try:
                                obj = repo.revparse_single(f'refs/tags/{ref}')
                            except KeyError:
                                obj = repo.revparse_single(ref)
                    else:
                        obj = repo.revparse_single(ref)

                    # Peel annotated tags to get the actual commit
                    if obj.type == pygit2.GIT_OBJECT_TAG:
                        commit = obj.peel(pygit2.GIT_OBJECT_COMMIT)
                    else:
                        commit = obj

                    latest_commit = str(commit.id)
                    # Get commit date
                    latest_commit_date = commit.commit_time
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
            except Exception:
                pass

        return updates

    def uninstall_plugin(self, plugin: Plugin, purge=False):
        """Uninstall a plugin.

        Args:
            plugin: Plugin to uninstall
            purge: If True, also remove plugin configuration
        """
        self.disable_plugin(plugin)
        plugin_path = plugin.local_path

        # Safety check: ensure plugin_path is a child of primary plugin dir, not the dir itself
        if not plugin_path.is_relative_to(self._primary_plugin_dir) or plugin_path == self._primary_plugin_dir:
            raise ValueError(f'Plugin path must be a subdirectory of {self._primary_plugin_dir}: {plugin_path}')

        if os.path.islink(plugin_path):
            log.debug("Removing symlink %r", plugin_path)
            os.remove(plugin_path)
        elif os.path.isdir(plugin_path):
            log.debug("Removing directory %r", plugin_path)
            shutil.rmtree(plugin_path)

        # Remove metadata
        from picard.config import get_config

        config = get_config()
        if 'plugins3' in config.setting and 'metadata' in config.setting['plugins3']:
            # Remove by UUID if available
            if plugin.manifest and plugin.manifest.uuid:
                config.setting['plugins3']['metadata'].pop(plugin.manifest.uuid, None)

        # Remove plugin config if purge requested
        if purge:
            self._clean_plugin_config(plugin.plugin_id)

    def _clean_plugin_config(self, plugin_name: str):
        """Remove plugin-specific configuration."""
        from picard.config import get_config

        config = get_config()
        # Remove plugin section if it exists
        if plugin_name in config.setting:
            del config.setting[plugin_name]
            log.debug('Removed configuration for plugin %s', plugin_name)

    def init_plugins(self):
        """Initialize and enable plugins that are enabled in configuration."""
        # Check for blacklisted plugins on startup
        self._check_blacklisted_plugins()

        enabled_count = 0
        for plugin in self._plugins:
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if plugin_uuid and plugin_uuid in self._enabled_plugins:
                try:
                    log.info('Loading plugin: %s', plugin.manifest.name() if plugin.manifest else plugin.plugin_id)
                    plugin.load_module()
                    plugin.enable(self._tagger)
                    enabled_count += 1
                except Exception as ex:
                    log.error('Failed initializing plugin %s from %s', plugin.plugin_id, plugin.local_path, exc_info=ex)

        log.info('Loaded %d plugin%s', enabled_count, 's' if enabled_count != 1 else '')

    def _check_blacklisted_plugins(self):
        """Check installed plugins against blacklist and disable if needed."""
        blacklisted_plugins = []

        for plugin in self._plugins:
            # Get UUID from plugin manifest
            plugin_uuid = plugin.manifest.uuid if plugin.manifest else None
            if not plugin_uuid:
                continue

            metadata = self._metadata.get_plugin_metadata(plugin_uuid)
            url = metadata.get('url') if metadata else None

            is_blacklisted, reason = self._registry.is_blacklisted(url, plugin_uuid)
            if is_blacklisted:
                log.warning('Plugin %s is blacklisted: %s', plugin.plugin_id, reason)
                blacklisted_plugins.append((plugin.plugin_id, reason))

                if plugin_uuid in self._enabled_plugins:
                    log.warning('Disabling blacklisted plugin %s', plugin.plugin_id)
                    self._enabled_plugins.discard(plugin_uuid)
                    self._save_config()

        # Show warning to user if any plugins were blacklisted
        if blacklisted_plugins:
            self._show_blacklist_warning(blacklisted_plugins)

    def _show_blacklist_warning(self, blacklisted_plugins):
        """Show warning dialog to user about blacklisted plugins."""
        # Skip GUI warning if no tagger (CLI mode)
        if not self._tagger:
            return

        from PyQt6.QtWidgets import QMessageBox

        plugin_list = '\n'.join([f'• {name}: {reason}' for name, reason in blacklisted_plugins])
        message = (
            f'The following plugins have been blacklisted and disabled:\n\n'
            f'{plugin_list}\n\n'
            f'These plugins may contain security vulnerabilities or malicious code. '
            f'They have been automatically disabled for your protection.'
        )

        QMessageBox.warning(
            self._tagger.window if hasattr(self._tagger, 'window') else None, 'Blacklisted Plugins Detected', message
        )
        log.info('Showed blacklist warning for %d plugin(s)', len(blacklisted_plugins))

    def enable_plugin(self, plugin: Plugin):
        """Enable a plugin and save to config."""
        uuid = self._get_plugin_uuid(plugin)
        log.debug('Enabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        if self._tagger:
            plugin.load_module()
            # Only enable if not already enabled
            if plugin.state != PluginState.ENABLED:
                plugin.enable(self._tagger)

        self._enabled_plugins.add(uuid)
        self._save_config()
        log.info('Plugin %s enabled (state: %s)', plugin.plugin_id, plugin.state.value)

    def disable_plugin(self, plugin: Plugin):
        """Disable a plugin and save to config."""
        uuid = self._get_plugin_uuid(plugin)
        log.debug('Disabling plugin %s (UUID %s, current state: %s)', plugin.plugin_id, uuid, plugin.state.value)

        # Only disable if not already disabled
        if plugin.state != PluginState.DISABLED:
            plugin.disable()

        self._enabled_plugins.discard(uuid)
        self._save_config()
        log.info('Plugin %s disabled (state: %s)', plugin.plugin_id, plugin.state.value)

    def _load_config(self):
        """Load enabled plugins list from config."""
        enabled = self._get_config_value('plugins3', 'enabled_plugins', default=[])
        self._enabled_plugins = set(enabled)
        log.debug('Loaded enabled plugins from config: %r', self._enabled_plugins)

    def _save_config(self):
        """Save enabled plugins list to config."""
        self._set_config_value('plugins3', 'enabled_plugins', value=list(self._enabled_plugins))
        log.debug('Saved enabled plugins to config: %r', self._enabled_plugins)

    def _load_plugin(self, plugin_dir: Path, plugin_name: str):
        """Load a plugin and check API version compatibility.

        Returns:
            Plugin object if compatible, None otherwise
        """
        plugin = Plugin(plugin_dir, plugin_name)
        try:
            plugin.read_manifest()
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

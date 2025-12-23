# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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

from enum import Enum
import importlib.util
from pathlib import Path
import re
import sys
import time
import types

from picard import log
from picard.extension_points import unregister_module_extensions
from picard.git.backend import GitBackendError, GitRefType
from picard.git.factory import git_backend
from picard.git.ref_utils import find_git_ref
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.version import Version


try:
    import hashlib

    HAS_HASHLIB = True
except ImportError:
    HAS_HASHLIB = False
    hashlib = None  # type: ignore[assignment]

# Retry configuration for git operations
GIT_OPERATION_MAX_RETRIES = 3
GIT_OPERATION_RETRY_DELAY_BASE = 2  # exponential backoff for retry delay


def short_commit_id(commit_id):
    """Return shortened commit ID for display.

    Uses first 7 characters by default. Can be adjusted for future
    git versions that use longer hashes (e.g., SHA-256).
    """
    if not commit_id:
        return ''
    return commit_id[:7]


def hash_string(text):
    """Generate SHA1 hash of a string for use in filenames.

    Args:
        text: String to hash

    Returns:
        str: Full SHA1 hash (40 characters)
    """

    return hashlib.sha1(text.encode()).hexdigest()


class PluginState(Enum):
    """Plugin lifecycle states."""

    DISCOVERED = 'discovered'  # Found on disk, not yet loaded
    LOADED = 'loaded'  # Module loaded, not enabled
    ENABLED = 'enabled'  # Enabled and active
    DISABLED = 'disabled'  # Explicitly disabled
    ERROR = 'error'  # Failed to load or enable


class PluginSourceSyncError(Exception):
    pass


class PluginAlreadyEnabledError(Exception):
    """Raised when trying to enable an already enabled plugin."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id} is already enabled")


class PluginAlreadyDisabledError(Exception):
    """Raised when trying to disable an already disabled plugin."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id} is already disabled")


class PluginSource:
    """Abstract class for plugin sources"""

    def sync(self, target_directory: Path):
        raise NotImplementedError


class PluginSourceGit(PluginSource):
    """Plugin is stored in a git repository, local or remote"""

    def __init__(self, url: str, ref: str | None = None):
        super().__init__()
        # Git backend will handle availability check
        # Note: url can be a local directory
        self.url = url
        self.ref = ref
        self.resolved_ref: str | None = None  # Will be set after sync
        self.resolved_ref_type: str | None = None  # 'tag' or 'branch', set after sync

    def _resolve_ref(self, repo, ref):
        """Resolve a ref to a commit, handling origin/ prefix automatically."""
        # Try direct resolution first
        normalized_ref = ref[7:] if ref.startswith('origin/') else ref

        for attempt_ref in [normalized_ref, f'origin/{normalized_ref}', ref]:
            try:
                return repo.revparse_to_commit(attempt_ref)
            except (KeyError, GitBackendError):
                continue

        # If all attempts fail, provide helpful error
        available_refs = self._list_available_refs(repo)
        raise KeyError(f"Could not find ref '{ref}'. Available refs: {available_refs}")

    def _is_relative_ref(self, ref):
        """Check if ref is a relative reference (contains git notation like ^, ~, @)."""
        return ref and any(char in ref for char in ['^', '~', '@', ':'])

    def _list_available_refs(self, repo, limit=20):
        """List available refs in repository.

        Args:
            repo: GitRepository instance
            limit: Maximum number of refs to return

        Returns:
            str: Comma-separated list of ref names
        """
        refs = []
        all_refs = repo.list_references()
        for ref in all_refs:
            if ref.ref_type == GitRefType.BRANCH:
                if ref.is_remote:
                    refs.append(ref.shortname)  # Already includes origin/ prefix
                else:
                    refs.append(ref.shortname)
            elif ref.ref_type == GitRefType.TAG:
                refs.append(ref.shortname)

        if not refs:
            return "none"

        refs = refs[:limit]
        if len(all_refs) > limit:
            refs.append(f"... ({len(all_refs) - limit} more)")

        return ", ".join(refs)

    def _retry_git_operation(self, operation, max_retries=GIT_OPERATION_MAX_RETRIES):
        """Execute git operation with retry logic for network errors."""
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                error_msg = str(e).lower()
                is_network_error = any(
                    keyword in error_msg
                    for keyword in [
                        'timeout',
                        'connection',
                        'network',
                        'resolve',
                        'failed to connect',
                        'could not resolve',
                    ]
                )
                if is_network_error and attempt < max_retries - 1:
                    wait = GIT_OPERATION_RETRY_DELAY_BASE**attempt
                    log.warning('Git operation failed (attempt %d/%d): %s', attempt + 1, max_retries, e)
                    log.info('Retrying in %d seconds...', wait)
                    time.sleep(wait)
                else:
                    raise

    def _is_tag_ref(self, repo):
        """Check if current ref is a tag using robust type detection."""
        if not self.ref:
            return False
        git_ref = find_git_ref(repo, self.ref)
        return git_ref and git_ref.ref_type == GitRefType.TAG

    def sync(self, target_directory: Path, shallow: bool = False, single_branch: bool = False, fetch_ref: bool = False):
        """Sync plugin from git repository.

        Args:
            target_directory: Path to clone/sync to
            shallow: If True, use depth=1 for clone
            single_branch: If True, only clone/fetch the specific branch
            fetch_ref: If True and repo exists, fetch the ref before checking out (for switch-ref)
        """
        backend = git_backend()

        if target_directory.is_dir():
            repo = backend.create_repository(target_directory.absolute())
            # If fetch_ref is True, fetch the specific ref we're switching to
            if fetch_ref and self.ref:
                callbacks = backend.create_remote_callbacks()
                try:
                    origin_remote = repo.get_remote('origin')
                    refspec = f'+refs/heads/{self.ref}:refs/remotes/origin/{self.ref}'
                    try:
                        self._retry_git_operation(
                            lambda: repo.fetch_remote(origin_remote, refspec, callbacks._callbacks)
                        )
                    except Exception:
                        # If specific refspec fails, try fetching all (might be a tag or commit)
                        self._retry_git_operation(
                            lambda: repo.fetch_remote_with_tags(origin_remote, None, callbacks._callbacks)
                        )
                except (KeyError, GitBackendError):
                    # No origin remote, skip fetch
                    pass
            else:
                callbacks = backend.create_remote_callbacks()
                try:
                    origin_remote = repo.get_remote('origin')
                    self._retry_git_operation(
                        lambda: repo.fetch_remote_with_tags(origin_remote, None, callbacks._callbacks)
                    )
                except (KeyError, GitBackendError):
                    # No origin remote, skip fetch
                    pass
        else:
            depth = 1 if shallow else 0
            # Strip origin/ prefix if present for checkout_branch
            checkout_branch = None
            if self.ref and single_branch and not self.ref.startswith('refs/'):
                checkout_branch = self.ref[7:] if self.ref.startswith('origin/') else self.ref

            def clone_operation():
                return backend.clone_repository(
                    self.url,
                    target_directory,
                    callbacks=backend.create_remote_callbacks(),
                    depth=depth,
                    checkout_branch=checkout_branch,
                )

            try:
                repo = self._retry_git_operation(clone_operation)
            except Exception as e:
                # Check if it's a repository-level 404/not found error (not branch-level)
                error_msg = str(e).lower()
                # Only catch repository not found, not branch/ref not found
                if (
                    '404' in error_msg or 'repository not found' in error_msg or 'does not exist' in error_msg
                ) and checkout_branch is None:
                    raise PluginSourceSyncError(f"Repository not found: {self.url}") from e
                elif 'authentication' in error_msg or 'credentials' in error_msg or 'forbidden' in error_msg:
                    raise PluginSourceSyncError(
                        f"Authentication failed for {self.url}. "
                        "For private repositories, use SSH URLs (git@github.com:user/repo.git) "
                        "or configure git credential helpers."
                    ) from e
                # checkout_branch failed (likely a tag or commit, not a branch)
                # Fall back to full clone without single-branch optimization
                elif checkout_branch:

                    def fallback_clone():
                        return backend.clone_repository(
                            self.url,
                            target_directory,
                            callbacks=backend.create_remote_callbacks(),
                            depth=depth,
                        )

                    repo = self._retry_git_operation(fallback_clone)
                else:
                    raise

            # If shallow clone and ref specified, fetch tags to ensure tags are available for updates
            if shallow and self.ref:
                callbacks = backend.create_remote_callbacks()
                try:
                    origin_remote = repo.get_remote('origin')
                    repo.fetch_remote(origin_remote, '+refs/tags/*:refs/tags/*', callbacks._callbacks)
                except Exception:
                    pass  # Tags might not exist or fetch might fail

        if self.ref:
            # Handle relative references (git notation like main^, HEAD~1)
            if self._is_relative_ref(self.ref):
                self.resolved_ref = self.ref  # Keep original for metadata
                commit = None  # Will be resolved after repo setup
            else:
                # Try to resolve the ref, handling origin/ prefix automatically
                commit = self._resolve_ref(repo, self.ref)
                self.resolved_ref = self.ref  # Keep original for metadata
        else:
            # Use repository's default branch (HEAD)
            try:
                commit = repo.revparse_to_commit('HEAD')
                # Get the branch name that HEAD points to
                if repo.is_head_detached():
                    self.resolved_ref = short_commit_id(commit.id)
                else:
                    # Get branch name from HEAD
                    head_ref = repo.get_head_name()
                    if head_ref.startswith('refs/heads/'):
                        self.resolved_ref = head_ref[11:]  # Remove 'refs/heads/' prefix
                    else:
                        self.resolved_ref = head_ref
            except (KeyError, GitBackendError):
                # HEAD not set, try 'main' or first available branch
                try:
                    commit = repo.revparse_to_commit('main')
                    self.resolved_ref = 'main'
                except (KeyError, GitBackendError):
                    # Find first available branch
                    branches = list(repo.branches.local)
                    if branches:
                        branch_name = branches[0]
                        commit = repo.revparse_to_commit(branch_name)
                        self.resolved_ref = branch_name
                    else:
                        # Last resort: find any reference
                        refs = repo.list_references()
                        for git_ref in refs:
                            if git_ref.ref_type == GitRefType.BRANCH and not git_ref.is_remote:
                                commit = repo.revparse_to_commit(git_ref.name)
                                # Strip origin/ prefix for consistency with display
                                if git_ref.is_remote and git_ref.shortname.startswith('origin/'):
                                    self.resolved_ref = git_ref.shortname[7:]  # Remove 'origin/' prefix
                                else:
                                    self.resolved_ref = git_ref.shortname
                                break
                        else:
                            # Try remote refs as absolute last resort
                            for git_ref in refs:
                                if (
                                    git_ref.ref_type == GitRefType.BRANCH
                                    and git_ref.is_remote
                                    and not git_ref.shortname.endswith('/HEAD')
                                ):
                                    commit = repo.revparse_to_commit(git_ref.name)
                                    self.resolved_ref = git_ref.shortname
                                    break
                            else:
                                raise PluginSourceSyncError('No branches found in repository') from None

        # Determine ref type for the resolved ref (non-relative refs only)
        if self.resolved_ref and not self._is_relative_ref(self.ref):
            from picard.git.ref_utils import find_git_ref

            git_ref = find_git_ref(repo, self.resolved_ref)
            if git_ref:
                self.resolved_ref_type = git_ref.ref_type.value  # 'tag' or 'branch'
            else:
                # If not found as branch or tag, assume it's a commit
                self.resolved_ref_type = 'commit'

        # hard reset to passed ref or HEAD
        # Use backend for reset operation
        from picard.git.backend import GitResetMode

        # Handle relative references that need to be resolved after repo setup
        if commit is None and self.resolved_ref and self._is_relative_ref(self.resolved_ref):
            try:
                commit = repo.revparse_to_commit(self.resolved_ref)
                self.resolved_ref = short_commit_id(commit.id)
                self.resolved_ref_type = 'commit'  # Set ref_type here after resolution
            except (KeyError, GitBackendError):
                available_refs = self._list_available_refs(repo)
                raise KeyError(
                    f"Could not resolve relative ref '{self.ref}' after repository setup. Available refs: {available_refs}"
                ) from None

        repo.reset(commit.id, GitResetMode.HARD)
        commit_id = commit.id
        repo.free()
        return commit_id

    def update(self, target_directory: Path, single_branch: bool = False):
        """Update plugin to latest version on current ref.

        Args:
            target_directory: Path to plugin directory
            single_branch: If True, only fetch the current ref
        """

        backend = git_backend()
        repo = backend.create_repository(target_directory.absolute())
        old_commit = repo.get_head_target()

        # Check if currently on a tag
        current_is_tag = False
        current_tag = None
        if self.ref:
            # Use robust reference type detection
            current_is_tag = self._is_tag_ref(repo)
            if current_is_tag:
                current_tag = self.ref

        callbacks = backend.create_remote_callbacks()
        try:
            origin_remote = repo.get_remote('origin')
            if single_branch and self.ref and not current_is_tag:
                # Fetch only the specific ref (branch)
                refspec = f'+refs/heads/{self.ref}:refs/remotes/origin/{self.ref}'
                repo.fetch_remote(origin_remote, refspec, callbacks._callbacks)
            else:
                # Fetch all refs including tags
                repo.fetch_remote_with_tags(origin_remote, None, callbacks._callbacks)
        except (KeyError, GitBackendError):
            # No origin remote, skip fetch
            pass

        # If on a tag, try to find latest tag
        if current_is_tag and current_tag:
            latest_tag = self._find_latest_tag(repo, current_tag)
            if latest_tag and latest_tag != current_tag:
                # Update to latest tag
                self.ref = latest_tag
                # Set resolved_ref_type to indicate this is a tag
                self.resolved_ref_type = 'tag'

        if self.ref:
            # For updates, prefer origin/ prefix for branches to get latest changes
            git_ref = find_git_ref(repo, self.ref)
            if git_ref and git_ref.ref_type == GitRefType.BRANCH and not git_ref.is_remote:
                # Try origin/ version first for updates
                try:
                    commit = repo.revparse_to_commit(f'origin/{self.ref}')
                except (KeyError, GitBackendError):
                    # Fall back to local branch
                    commit = repo.revparse_to_commit(git_ref.name)
            elif git_ref and git_ref.ref_type in (GitRefType.TAG, GitRefType.BRANCH):
                commit = repo.revparse_to_commit(git_ref.name)
            else:
                # For commits or unknown refs, try as-is
                commit = repo.revparse_to_commit(self.ref)
        else:
            # No specific ref, use HEAD
            commit = repo.revparse_to_commit('HEAD')

        from picard.git.backend import GitResetMode

        repo.reset(commit.id, GitResetMode.HARD)
        new_commit = commit.id
        repo.free()

        return old_commit, new_commit

    def _find_latest_tag(self, repo, current_tag: str):
        """Find the latest tag based on version sorting.

        Handles various tag naming conventions:
        - v1.0.0, v1.0, v1
        - 1.0.0, 1.0, 1
        - release-1.0.0, release/1.0.0
        - 2024.11.30 (date-based)
        """
        from picard import log

        log.debug("_find_latest_tag: checking for updates from current tag %s", current_tag)

        # Get all tags (use abstracted list_references)
        tags = []
        all_refs = repo.list_references()

        for ref in all_refs:
            if ref.ref_type == GitRefType.TAG:
                tags.append(ref.shortname)

        log.debug("_find_latest_tag: found %d tags: %s", len(tags), tags)

        if not tags:
            return None

        # Extract version from tag name
        def extract_version(tag):
            # Try common patterns
            patterns = [
                r'^v?(\d+\.\d+\.\d+)',  # v1.0.0 or 1.0.0
                r'^v?(\d+\.\d+)',  # v1.0 or 1.0
                r'^v?(\d+)',  # v1 or 1
                r'release[-/]v?(\d+\.\d+\.\d+)',  # release-1.0.0 or release/1.0.0
                r'(\d{4}\.\d{1,2}\.\d{1,2})',  # 2024.11.30 (date-based)
            ]

            for pattern in patterns:
                match = re.search(pattern, tag)
                if match:
                    return match.group(1)
            return None

        # Parse current tag version
        current_version_str = extract_version(current_tag)
        log.debug("_find_latest_tag: current tag %s -> version %s", current_tag, current_version_str)
        if not current_version_str:
            # Can't parse current tag, don't update
            return None

        try:
            current_version = Version.from_string(current_version_str)
            log.debug("_find_latest_tag: parsed current version: %s", current_version)
        except Exception as e:
            log.debug("_find_latest_tag: failed to parse current version %s: %s", current_version_str, e)
            return None

        # Find all tags with parseable versions
        versioned_tags = []
        for tag in tags:
            version_str = extract_version(tag)
            if version_str:
                try:
                    ver = Version.from_string(version_str)
                    versioned_tags.append((tag, ver))
                    log.debug("_find_latest_tag: tag %s -> version %s", tag, ver)
                except Exception as e:
                    log.debug("_find_latest_tag: failed to parse tag %s version %s: %s", tag, version_str, e)
                    continue

        if not versioned_tags:
            return None

        # Sort by version and get latest
        versioned_tags.sort(key=lambda x: x[1], reverse=True)
        latest_tag, latest_version = versioned_tags[0]
        log.debug("_find_latest_tag: latest tag %s with version %s", latest_tag, latest_version)

        # Only return if it's newer than current
        if latest_version > current_version:
            log.debug("_find_latest_tag: %s > %s, returning %s", latest_version, current_version, latest_tag)
            return latest_tag

        log.debug("_find_latest_tag: %s <= %s, no update needed", latest_version, current_version)
        return None


class PluginSourceLocal(PluginSource):
    """Plugin is stored in a local directory, but is not a git repo"""

    def sync(self, target_directory: Path):
        # TODO: copy tree to plugin directory (?)
        pass


class Plugin:
    local_path: Path | None = None
    remote_url: str | None = None
    ref: str | None = None
    module_name: str | None = None
    manifest: PluginManifest | None = None
    state: PluginState | None = None
    _module: types.ModuleType | None = None

    def __init__(self, plugins_dir: Path, plugin_id: str, uuid: str | None = None):
        assert plugin_id, "Plugin ID cannot be empty!"
        self.plugin_id = plugin_id
        self.module_name = f'picard.plugins.{self.plugin_id}'
        self.local_path = plugins_dir.joinpath(self.plugin_id)
        self.state = PluginState.DISCOVERED
        self.uuid = uuid

    def sync(self, plugin_source: PluginSource | None = None):
        """Sync plugin source"""
        if plugin_source:
            assert self.local_path is not None, "Plugin local_path must be set"
            try:
                plugin_source.sync(self.local_path)
            except Exception as e:
                raise PluginSourceSyncError(e) from e

    def read_manifest(self):
        """Reads metadata for the plugin from the plugin's MANIFEST.toml"""
        from picard.plugin3.manager import PluginManifestReadError

        self.uuid = None
        try:
            manifest_path = self.local_path.joinpath('MANIFEST.toml')
            with open(manifest_path, 'rb') as manifest_file:
                self.manifest = PluginManifest(self.plugin_id, manifest_file)
        except Exception as e:
            raise PluginManifestReadError(e, manifest_path) from e

        # Validate manifest
        errors = self.manifest.validate()
        if errors:
            from picard.plugin3.manager import PluginManifestInvalidError

            raise PluginManifestInvalidError(errors)

        # Add a shortcut
        self.uuid = self.manifest.uuid

    def has_versioning(self, registry=None, is_tag_installation=False):
        """Check if plugin supports version-based updates.

        Args:
            registry: PluginRegistry instance to check for versioning_scheme
            is_tag_installation: Whether plugin was installed from a tag

        Returns:
            bool: True if plugin supports versioning (has registry versioning_scheme
                  or is a local/URL plugin installed from tags)
        """
        if registry and self.uuid:
            registry_plugin = registry.find_plugin(uuid=self.uuid)
            if registry_plugin and registry_plugin.versioning_scheme:
                return True

        # Local/URL plugins installed from tags support versioning (assume semver)
        return is_tag_installation and not (registry and registry.find_plugin(uuid=self.uuid))

    def get_versioning_scheme(self, registry=None):
        """Get versioning scheme for this plugin.

        Args:
            registry: PluginRegistry instance to check for versioning_scheme

        Returns:
            str: Versioning scheme ('semver', 'calver', 'regex:pattern') or 'semver'
                 for local plugins, empty string if no versioning support
        """
        if registry and self.uuid:
            registry_plugin = registry.find_plugin(uuid=self.uuid)
            if registry_plugin and registry_plugin.versioning_scheme:
                return registry_plugin.versioning_scheme

        # Default to semver for local/URL plugins (when they have versioning support)
        return 'semver'

    def get_current_commit_id(self, short=False):
        """Get the current commit ID of the plugin if it's a git repository."""
        git_dir = self.local_path / '.git'
        if not git_dir.exists():
            return None

        try:
            backend = git_backend()
            repo = backend.create_repository(self.local_path)
            commit_id = repo.get_head_target()
            repo.free()
            return short_commit_id(commit_id) if short else commit_id
        except Exception:
            return None

    def load_module(self):
        """Load corresponding module from source path"""
        if self.state == PluginState.LOADED:
            return self._module
        if self.state == PluginState.ENABLED:
            raise PluginAlreadyEnabledError(self.plugin_id)

        module_file = self.local_path.joinpath('__init__.py')
        spec = importlib.util.spec_from_file_location(self.module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = module
        spec.loader.exec_module(module)
        self._module = module
        self.state = PluginState.LOADED

        return module

    def enable(self, tagger) -> None:
        """Enable the plugin"""
        if self.state == PluginState.ENABLED:
            raise PluginAlreadyEnabledError(self.plugin_id)

        assert self.manifest is not None, "Plugin manifest must be loaded before enabling"
        api = PluginApi(self.manifest, tagger)
        api._plugin_module = self._module
        api._plugin_dir = self.local_path
        api._load_translations()
        api._install_qt_translator()

        # Register API instance for get_api()
        module_name = getattr(self._module, '__name__', None)
        if module_name:
            # Check if there's an existing API instance (from UI components)
            # and reload its translations to reflect any updates
            existing_api = PluginApi._instances.get(module_name)
            if existing_api and existing_api._plugin_dir == self.local_path:
                existing_api._plugin_module = self._module
                existing_api.reload_translations()

            PluginApi._instances[module_name] = api

        # Log plugin info
        version = self.manifest.version if self.manifest else None
        commit_id = self.get_current_commit_id(short=True)
        version_str = f" v{version}" if version else ""
        if commit_id:
            api.logger.info(f"Enabling plugin {self.plugin_id}{version_str} (commit {commit_id})")
        else:
            api.logger.info(f"Enabling plugin {self.plugin_id}{version_str}")

        assert self._module is not None, "Plugin module must be loaded before enabling"
        self._module.enable(api)
        self.state = PluginState.ENABLED

    def disable(self) -> None:
        """Disable the plugin"""
        if self.state == PluginState.DISABLED:
            raise PluginAlreadyDisabledError(self.plugin_id)

        if self._module is not None and hasattr(self._module, 'disable'):
            self._module.disable()
        unregister_module_extensions(self.plugin_id)

        # Cleanup API instance registry - find and remove by module reference
        for name, api in list(PluginApi._instances.items()):
            if api._plugin_module is self._module:
                api._remove_qt_translator()
                del PluginApi._instances[name]
                # Remove from cache (entries for this module and submodules)
                for key in list(PluginApi._module_cache):
                    if key == name or key.startswith(name + '.'):
                        del PluginApi._module_cache[key]
                break

        # Clear module from sys.modules to force reload on next enable
        if self.module_name in sys.modules:
            del sys.modules[self.module_name]
        # Also clear any submodules
        module_prefix = self.module_name + '.'
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(module_prefix):
                del sys.modules[module_name]

        self.state = PluginState.DISABLED

    def name(self):
        """Returns translated plugin name if possible, else plugin_id"""
        try:
            return self.manifest.name_i18n()
        except Exception as e:
            log.error("Failed to get plugin %s's name: %s", self, e)
            return str(self)

    def __str__(self):
        """Returns plugin id"""
        return self.plugin_id

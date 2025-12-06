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

from picard import log
from picard.extension_points import (
    unregister_module_extensions,
    unset_plugin_uuid,
)
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest
from picard.version import Version


try:
    import pygit2

    HAS_PYGIT2 = True
except ImportError:
    HAS_PYGIT2 = False
    pygit2 = None

try:
    import hashlib

    HAS_HASHLIB = True
except ImportError:
    HAS_HASHLIB = False
    hashlib = None

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


if HAS_PYGIT2:

    class GitRemoteCallbacks(pygit2.RemoteCallbacks):
        def __init__(self):
            super().__init__()
            self._attempted = False

        def transfer_progress(self, stats):
            pass  # Suppress progress output

        def credentials(self, url, username_from_url, allowed_types):
            """Provide credentials for git operations.

            Supports SSH keys and username/password authentication.
            Falls back to system git credential helpers.
            """
            # Prevent infinite retry loops
            if self._attempted:
                return None
            self._attempted = True

            if allowed_types & pygit2.GIT_CREDENTIAL_SSH_KEY:
                # Try SSH key authentication with default key
                try:
                    return pygit2.Keypair('git', None, None, '')
                except Exception:
                    return None
            elif allowed_types & pygit2.GIT_CREDENTIAL_USERPASS_PLAINTEXT:
                # Try default credential helper
                try:
                    return pygit2.Username('git')
                except Exception:
                    return None
            return None
else:

    class GitRemoteCallbacks:
        pass


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

    def __init__(self, url: str, ref: str = None):
        super().__init__()
        if not HAS_PYGIT2:
            raise PluginSourceSyncError("pygit2 is not available. Install it to use git-based plugin sources.")
        # Note: url can be a local directory
        self.url = url
        self.ref = ref
        self.resolved_ref = None  # Will be set after sync

    def _list_available_refs(self, repo, limit=20):
        """List available refs in repository.

        Args:
            repo: pygit2.Repository instance
            limit: Maximum number of refs to return

        Returns:
            str: Comma-separated list of ref names
        """
        refs = []
        all_refs = list(repo.references)  # Convert References to list
        for ref in all_refs:
            if ref.startswith('refs/heads/'):
                refs.append(ref[11:])  # Remove 'refs/heads/' prefix
            elif ref.startswith('refs/remotes/origin/'):
                refs.append(f"origin/{ref[20:]}")  # Remove 'refs/remotes/origin/' prefix
            elif ref.startswith('refs/tags/'):
                refs.append(ref[10:])  # Remove 'refs/tags/' prefix

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
            except pygit2.GitError as e:
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

    def _resolve_to_commit(self, obj):
        """Resolve a git object to a commit, peeling tags if needed."""
        if hasattr(obj, 'type') and obj.type == pygit2.GIT_OBJECT_TAG:
            return obj.peel(pygit2.GIT_OBJECT_COMMIT)
        return obj

    def sync(self, target_directory: Path, shallow: bool = False, single_branch: bool = False, fetch_ref: bool = False):
        """Sync plugin from git repository.

        Args:
            target_directory: Path to clone/sync to
            shallow: If True, use depth=1 for clone
            single_branch: If True, only clone/fetch the specific branch
            fetch_ref: If True and repo exists, fetch the ref before checking out (for switch-ref)
        """
        if target_directory.is_dir():
            repo = pygit2.Repository(target_directory.absolute())
            # If fetch_ref is True, fetch the specific ref we're switching to
            if fetch_ref and self.ref:
                for remote in repo.remotes:
                    refspec = f'+refs/heads/{self.ref}:refs/remotes/origin/{self.ref}'
                    try:
                        self._retry_git_operation(lambda: remote.fetch([refspec], callbacks=GitRemoteCallbacks()))
                    except Exception:
                        # If specific refspec fails, try fetching all (might be a tag or commit)
                        self._retry_git_operation(lambda: remote.fetch(callbacks=GitRemoteCallbacks()))
            else:
                for remote in repo.remotes:
                    self._retry_git_operation(lambda: remote.fetch(callbacks=GitRemoteCallbacks()))
        else:
            depth = 1 if shallow else 0
            # Strip origin/ prefix if present for checkout_branch
            checkout_branch = None
            if self.ref and single_branch and not self.ref.startswith('refs/'):
                checkout_branch = self.ref[7:] if self.ref.startswith('origin/') else self.ref

            def clone_operation():
                return pygit2.clone_repository(
                    self.url,
                    target_directory.absolute(),
                    callbacks=GitRemoteCallbacks(),
                    depth=depth,
                    checkout_branch=checkout_branch,
                )

            try:
                repo = self._retry_git_operation(clone_operation)
            except (KeyError, pygit2.GitError) as e:
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
                        return pygit2.clone_repository(
                            self.url,
                            target_directory.absolute(),
                            callbacks=GitRemoteCallbacks(),
                            depth=depth,
                        )

                    repo = self._retry_git_operation(fallback_clone)
                else:
                    raise

            # If shallow clone and ref specified, fetch tags to ensure tags are available for updates
            if shallow and self.ref:
                for remote in repo.remotes:
                    try:
                        remote.fetch(['+refs/tags/*:refs/tags/*'], callbacks=GitRemoteCallbacks())
                    except Exception:
                        pass  # Tags might not exist or fetch might fail

        if self.ref:
            try:
                commit = repo.revparse_single(self.ref)
                self.resolved_ref = self.ref
            except KeyError:
                # If ref starts with 'origin/', try without it
                if self.ref.startswith('origin/'):
                    try:
                        ref_without_origin = self.ref[7:]  # Remove 'origin/' prefix
                        commit = repo.revparse_single(ref_without_origin)
                        self.resolved_ref = ref_without_origin
                    except KeyError:
                        available_refs = self._list_available_refs(repo)
                        raise KeyError(
                            f"Could not find ref '{self.ref}' or '{ref_without_origin}'. "
                            f"Available refs: {available_refs}"
                        ) from None
                else:
                    # Try with 'origin/' prefix for remote branches
                    try:
                        commit = repo.revparse_single(f'origin/{self.ref}')
                        self.resolved_ref = f'origin/{self.ref}'
                    except KeyError:
                        # Try as local branch refs/heads/
                        try:
                            commit = repo.revparse_single(f'refs/heads/{self.ref}')
                            self.resolved_ref = self.ref
                        except KeyError:
                            available_refs = self._list_available_refs(repo)
                            raise KeyError(
                                f"Could not find ref '{self.ref}'. "
                                f"Tried: '{self.ref}', 'origin/{self.ref}', 'refs/heads/{self.ref}'. "
                                f"Available refs: {available_refs}"
                            ) from None
        else:
            # Use repository's default branch (HEAD)
            try:
                commit = repo.revparse_single('HEAD')
                # Get the branch name that HEAD points to
                if repo.head_is_detached:
                    self.resolved_ref = short_commit_id(str(commit.id))
                else:
                    # Get branch name from HEAD
                    head_ref = repo.head.name
                    if head_ref.startswith('refs/heads/'):
                        self.resolved_ref = head_ref[11:]  # Remove 'refs/heads/' prefix
                    else:
                        self.resolved_ref = head_ref
            except KeyError:
                # HEAD not set, try 'main' or first available branch
                try:
                    commit = repo.revparse_single('main')
                    self.resolved_ref = 'main'
                except KeyError:
                    # Find first available branch
                    branches = list(repo.branches.local)
                    if branches:
                        branch_name = branches[0]
                        commit = repo.revparse_single(branch_name)
                        self.resolved_ref = branch_name
                    else:
                        # Last resort: find any reference
                        refs = repo.listall_references()
                        for ref in refs:
                            if ref.startswith('refs/heads/'):
                                branch_name = ref[11:]  # Remove 'refs/heads/' prefix
                                commit = repo.revparse_single(ref)
                                self.resolved_ref = branch_name
                                break
                        else:
                            # Try remote refs as absolute last resort
                            for ref in refs:
                                if ref.startswith('refs/remotes/origin/') and not ref.endswith('/HEAD'):
                                    branch_name = ref[20:]  # Remove 'refs/remotes/origin/' prefix
                                    commit = repo.revparse_single(ref)
                                    self.resolved_ref = f'origin/{branch_name}'
                                    break
                            else:
                                raise PluginSourceSyncError('No branches found in repository') from None

        # hard reset to passed ref or HEAD
        commit = self._resolve_to_commit(commit)
        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)
        commit_id = str(commit.id)
        repo.free()
        return commit_id

    def update(self, target_directory: Path, single_branch: bool = False):
        """Update plugin to latest version on current ref.

        Args:
            target_directory: Path to plugin directory
            single_branch: If True, only fetch the current ref
        """

        repo = pygit2.Repository(target_directory.absolute())
        old_commit = str(repo.head.target)

        # Check if currently on a tag
        current_is_tag = False
        current_tag = None
        if self.ref:
            try:
                # Check if ref is a tag
                repo.revparse_single(f'refs/tags/{self.ref}')
                current_is_tag = True
                current_tag = self.ref
            except KeyError:
                pass

        for remote in repo.remotes:
            if single_branch and self.ref and not current_is_tag:
                # Fetch only the specific ref (branch)
                refspec = f'+refs/heads/{self.ref}:refs/remotes/origin/{self.ref}'
                remote.fetch([refspec], callbacks=GitRemoteCallbacks())
            else:
                # Fetch all refs (including tags if on a tag)
                remote.fetch(callbacks=GitRemoteCallbacks())

        # If on a tag, try to find latest tag
        if current_is_tag and current_tag:
            latest_tag = self._find_latest_tag(repo, current_tag)
            if latest_tag and latest_tag != current_tag:
                # Update to latest tag
                self.ref = latest_tag

        if self.ref:
            # For branch names without origin/ prefix, try origin/ first
            ref_to_use = self.ref
            if not self.ref.startswith('origin/') and not self.ref.startswith('refs/'):
                # Try origin/ prefix first for branches
                try:
                    commit = repo.revparse_single(f'origin/{self.ref}')
                    ref_to_use = f'origin/{self.ref}'
                except KeyError:
                    # Fall back to original ref (might be tag or commit hash)
                    try:
                        commit = repo.revparse_single(f'refs/tags/{self.ref}')
                    except KeyError:
                        commit = repo.revparse_single(self.ref)
            else:
                commit = repo.revparse_single(ref_to_use)
        else:
            commit = repo.revparse_single('HEAD')

        commit = self._resolve_to_commit(commit)
        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)
        new_commit = str(commit.id)
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
        # Get all tags (use listall_references to include fetched tags)
        tags = []
        try:
            all_refs = repo.listall_references()
        except AttributeError:
            # Fallback for older pygit2
            all_refs = list(repo.references)

        for ref_name in all_refs:
            if ref_name.startswith('refs/tags/'):
                tag_name = ref_name[len('refs/tags/') :]
                tags.append(tag_name)

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
        if not current_version_str:
            # Can't parse current tag, don't update
            return None

        try:
            current_version = Version.from_string(current_version_str)
        except Exception:
            return None

        # Find all tags with parseable versions
        versioned_tags = []
        for tag in tags:
            version_str = extract_version(tag)
            if version_str:
                try:
                    ver = Version.from_string(version_str)
                    versioned_tags.append((tag, ver))
                except Exception:
                    continue

        if not versioned_tags:
            return None

        # Sort by version and get latest
        versioned_tags.sort(key=lambda x: x[1], reverse=True)
        latest_tag, latest_version = versioned_tags[0]

        # Only return if it's newer than current
        if latest_version > current_version:
            return latest_tag

        return None


class PluginSourceLocal(PluginSource):
    """Plugin is stored in a local directory, but is not a git repo"""

    def sync(self, target_directory: Path):
        # TODO: copy tree to plugin directory (?)
        pass


class Plugin:
    local_path: Path = None
    remote_url: str = None
    ref = None
    name: str = None
    module_name: str = None
    manifest: PluginManifest = None
    state: PluginState = None
    _module = None

    def __init__(self, plugins_dir: Path, plugin_name: str):
        self.plugin_id = plugin_name
        self.module_name = f'picard.plugins.{self.plugin_id}'
        self.local_path = plugins_dir.joinpath(self.plugin_id)
        self.state = PluginState.DISCOVERED

    def sync(self, plugin_source: PluginSource = None):
        """Sync plugin source"""
        if plugin_source:
            try:
                plugin_source.sync(self.local_path)
            except Exception as e:
                raise PluginSourceSyncError(e) from e

    def read_manifest(self):
        """Reads metadata for the plugin from the plugin's MANIFEST.toml"""
        manifest_path = self.local_path.joinpath('MANIFEST.toml')
        with open(manifest_path, 'rb') as manifest_file:
            self.manifest = PluginManifest(self.plugin_id, manifest_file)

        # Validate manifest
        errors = self.manifest.validate()
        if errors:
            from picard.plugin3.manager import PluginManifestInvalidError

            raise PluginManifestInvalidError(errors)

    def get_current_commit_id(self):
        """Get the current commit ID of the plugin if it's a git repository."""
        if not HAS_PYGIT2:
            return None

        git_dir = self.local_path / '.git'
        if not git_dir.exists():
            return None

        try:
            repo = pygit2.Repository(str(self.local_path))
            commit_id = str(repo.head.target)
            repo.free()
            return short_commit_id(commit_id)
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

        api = PluginApi(self.manifest, tagger)
        api._plugin_module = self._module
        api._plugin_dir = self.local_path
        api._load_translations()

        # Register API instance for get_api()
        module_name = getattr(self._module, '__name__', None)
        if module_name:
            PluginApi._instances[module_name] = api

        # Log plugin info
        version = self.manifest.version if self.manifest else 'unknown'
        commit_id = self.get_current_commit_id()
        if commit_id:
            api.logger.info(f"Enabling plugin {self.plugin_id} v{version} (commit {commit_id})")
        else:
            api.logger.info(f"Enabling plugin {self.plugin_id} v{version}")

        self._module.enable(api)
        self.state = PluginState.ENABLED

    def disable(self) -> None:
        """Disable the plugin"""
        if self.state == PluginState.DISABLED:
            raise PluginAlreadyDisabledError(self.plugin_id)

        if hasattr(self._module, 'disable'):
            self._module.disable()
        unregister_module_extensions(self.plugin_id)

        # Unregister UUID mapping
        if self.manifest and self.manifest.uuid:
            unset_plugin_uuid(self.manifest.uuid)

        # Cleanup API instance registry - find and remove by module reference
        for name, api in list(PluginApi._instances.items()):
            if api._plugin_module is self._module:
                del PluginApi._instances[name]
                # Remove from cache (entries for this module and submodules)
                for key in list(PluginApi._module_cache):
                    if key == name or key.startswith(name + '.'):
                        del PluginApi._module_cache[key]
                break

        self.state = PluginState.DISABLED

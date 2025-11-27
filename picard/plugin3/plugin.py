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
import sys

from picard.extension_points import unregister_module_extensions
from picard.plugin3.api import PluginApi
from picard.plugin3.manifest import PluginManifest


try:
    import pygit2

    HAS_PYGIT2 = True
except ImportError:
    HAS_PYGIT2 = False
    pygit2 = None


def short_commit_id(commit_id):
    """Return shortened commit ID for display.

    Uses first 7 characters by default. Can be adjusted for future
    git versions that use longer hashes (e.g., SHA-256).
    """
    if not commit_id:
        return ''
    return commit_id[:7]


class PluginState(Enum):
    """Plugin lifecycle states."""

    DISCOVERED = 'discovered'  # Found on disk, not yet loaded
    LOADED = 'loaded'  # Module loaded, not enabled
    ENABLED = 'enabled'  # Enabled and active
    DISABLED = 'disabled'  # Explicitly disabled
    ERROR = 'error'  # Failed to load or enable


if HAS_PYGIT2:

    class GitRemoteCallbacks(pygit2.RemoteCallbacks):
        def transfer_progress(self, stats):
            pass  # Suppress progress output
else:

    class GitRemoteCallbacks:
        pass


class PluginSourceSyncError(Exception):
    pass


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
                        remote.fetch([refspec], callbacks=GitRemoteCallbacks())
                    except Exception:
                        # If specific refspec fails, try fetching all (might be a tag or commit)
                        remote.fetch(callbacks=GitRemoteCallbacks())
            else:
                for remote in repo.remotes:
                    remote.fetch(callbacks=GitRemoteCallbacks())
        else:
            depth = 1 if shallow else 0
            checkout_branch = self.ref if (self.ref and single_branch and not self.ref.startswith('refs/')) else None

            try:
                repo = pygit2.clone_repository(
                    self.url,
                    target_directory.absolute(),
                    callbacks=GitRemoteCallbacks(),
                    depth=depth,
                    checkout_branch=checkout_branch,
                )
            except (KeyError, pygit2.GitError):
                # checkout_branch failed (likely a tag or commit, not a branch)
                # Fall back to full clone without single-branch optimization
                if checkout_branch:
                    repo = pygit2.clone_repository(
                        self.url,
                        target_directory.absolute(),
                        callbacks=GitRemoteCallbacks(),
                        depth=depth,
                    )
                else:
                    raise

        if self.ref:
            try:
                commit = repo.revparse_single(self.ref)
                self.resolved_ref = self.ref
            except KeyError:
                # If ref starts with 'origin/', try without it
                if self.ref.startswith('origin/'):
                    ref_without_origin = self.ref[7:]  # Remove 'origin/' prefix
                    commit = repo.revparse_single(ref_without_origin)
                    self.resolved_ref = ref_without_origin
                else:
                    # Try with 'origin/' prefix
                    commit = repo.revparse_single(f'origin/{self.ref}')
                    # Save the actual ref that worked
                    self.resolved_ref = f'origin/{self.ref}'
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

        for remote in repo.remotes:
            if single_branch and self.ref:
                # Fetch only the specific ref
                refspec = f'+refs/heads/{self.ref}:refs/remotes/origin/{self.ref}'
                remote.fetch([refspec], callbacks=GitRemoteCallbacks())
            else:
                # Fetch all refs
                remote.fetch(callbacks=GitRemoteCallbacks())

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
                    commit = repo.revparse_single(self.ref)
            else:
                commit = repo.revparse_single(ref_to_use)
        else:
            commit = repo.revparse_single('HEAD')

        repo.reset(commit.id, pygit2.enums.ResetMode.HARD)
        new_commit = str(commit.id)
        repo.free()

        return old_commit, new_commit


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
            error_list = '\n  '.join(errors)
            raise ValueError(f'Invalid MANIFEST.toml for {self.plugin_id}:\n  {error_list}')

    def load_module(self):
        """Load corresponding module from source path"""
        if self.state == PluginState.LOADED:
            return self._module
        if self.state == PluginState.ENABLED:
            raise ValueError(f'Plugin {self.plugin_id} is already enabled')

        module_file = self.local_path.joinpath('__init__.py')
        spec = importlib.util.spec_from_file_location(self.module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = module
        spec.loader.exec_module(module)
        self._module = module
        self.state = PluginState.LOADED

        # Register UUID mapping for extension points
        if self.manifest and self.manifest.uuid:
            from picard.extension_points import register_plugin_uuid

            register_plugin_uuid(self.manifest.uuid, self.plugin_id)

        return module

    def enable(self, tagger) -> None:
        """Enable the plugin"""
        if self.state == PluginState.ENABLED:
            raise ValueError(f'Plugin {self.plugin_id} is already enabled')

        api = PluginApi(self.manifest, tagger)
        self._module.enable(api)
        self.state = PluginState.ENABLED

    def disable(self) -> None:
        """Disable the plugin"""
        if self.state == PluginState.DISABLED:
            raise ValueError(f'Plugin {self.plugin_id} is already disabled')

        if hasattr(self._module, 'disable'):
            self._module.disable()
        unregister_module_extensions(self.plugin_id)

        # Unregister UUID mapping
        if self.manifest and self.manifest.uuid:
            from picard.extension_points import unregister_plugin_uuid

            unregister_plugin_uuid(self.manifest.uuid)

        self.state = PluginState.DISABLED

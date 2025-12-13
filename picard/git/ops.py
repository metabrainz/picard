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

"""Git operations for plugin management."""

import os
from pathlib import Path
import shutil

from picard import log
from picard.git.backend import (
    GitBackendError,
    GitObjectType,
    GitStatusFlag,
)
from picard.git.factory import git_backend


def clean_python_cache(directory):
    """Remove Python cache files and directories.

    Args:
        directory: Path to directory to clean
    """
    directory = Path(directory)
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            shutil.rmtree(Path(root) / '__pycache__', ignore_errors=True)
            dirs.remove('__pycache__')  # Don't walk into removed directory
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                (Path(root) / file).unlink(missing_ok=True)


class GitOperations:
    """Handles git operations for plugins."""

    @staticmethod
    def check_dirty_working_dir(path: Path):
        """Check if git working directory has uncommitted changes.

        Args:
            path: Path to git repository

        Returns:
            list: List of modified files, or empty list if clean

        Raises:
            Exception: If path is not a git repository
        """
        backend = git_backend()
        repo = backend.create_repository(path)
        status = repo.get_status()

        # Check for any changes (modified, added, deleted, renamed, etc.)
        modified_files = []
        for filepath, flag in status.items():
            if flag not in (GitStatusFlag.CURRENT, GitStatusFlag.IGNORED):
                # Ignore Python cache files
                if (
                    filepath.endswith(('.pyc', '.pyo'))
                    or '/__pycache__/' in filepath
                    or filepath.startswith('__pycache__/')
                ):
                    continue
                modified_files.append(filepath)

        return modified_files

    @staticmethod
    def fetch_remote_refs(url, use_callbacks=True):
        """Fetch remote refs from a git repository.

        Args:
            url: Git repository URL
            use_callbacks: Whether to use GitRemoteCallbacks for authentication

        Returns:
            list: Remote refs, or None on error
        """
        backend = git_backend()
        return backend.fetch_remote_refs(url, use_callbacks=use_callbacks)

    @staticmethod
    def validate_ref(url, ref, uuid=None, registry=None):
        """Validate that a ref exists in the repository.

        Args:
            url: Git repository URL
            ref: Git ref to validate
            uuid: Plugin UUID (for registry lookup)
            registry: PluginRegistry instance

        Returns:
            bool: True if ref is valid

        Raises:
            PluginRefNotFoundError: If ref doesn't exist
        """
        from picard.plugin3.manager import PluginRefNotFoundError

        # For registry plugins with versioning_scheme, validate against version tags
        if registry and uuid:
            registry_plugin = registry.find_plugin(uuid=uuid)
            if registry_plugin and registry_plugin.versioning_scheme:
                # Import here to avoid circular dependency
                from picard.plugin3.refs_cache import RefsCache

                refs_cache = RefsCache(registry)
                pattern = refs_cache.parse_versioning_scheme(registry_plugin.versioning_scheme)
                if pattern and pattern.match(ref):
                    # It's a version tag - fetch and check
                    version_tags = []
                    remote_refs = GitOperations.fetch_remote_refs(url, use_callbacks=False)
                    if remote_refs:
                        version_tags = refs_cache.filter_tags(remote_refs, pattern)

                    if ref not in version_tags:
                        raise PluginRefNotFoundError(uuid, ref)
                    return True

            # For registry plugins with explicit refs list
            if registry_plugin and registry_plugin.refs:
                ref_names = [r['name'] for r in registry_plugin.refs]
                if ref not in ref_names:
                    raise PluginRefNotFoundError(uuid, ref)
                return True

        # For non-registry plugins or no versioning, just check if ref exists remotely
        remote_refs = GitOperations.fetch_remote_refs(url, use_callbacks=True)
        if not remote_refs:
            # Can't validate - assume it's valid and let git fail later if not
            return True

        # Check if ref exists in remote
        ref_names = []
        for remote_ref in remote_refs:
            name = remote_ref.name if hasattr(remote_ref, 'name') else str(remote_ref)
            # Strip refs/heads/ and refs/tags/ prefixes
            if name.startswith('refs/heads/'):
                ref_names.append(name[11:])
            elif name.startswith('refs/tags/'):
                ref_names.append(name[10:])
            ref_names.append(name)  # Also add full name

        if ref not in ref_names:
            raise PluginRefNotFoundError(uuid or url, ref)

        return True

    @staticmethod
    def check_ref_type(repo_path, ref=None):
        """Check the type of a git ref by querying the repository.

        Args:
            repo_path: Path to git repository
            ref: Optional ref name to check (if None, checks current HEAD)

        Returns:
            tuple: (ref_type, ref_name) where ref_type is 'commit', 'tag', 'branch', or None
        """
        try:
            backend = git_backend()
            repo = backend.create_repository(repo_path)
            references = repo.get_references()

            if ref:
                # Check if ref exists in standard locations first
                if f'refs/tags/{ref}' in references:
                    return 'tag', ref
                if f'refs/heads/{ref}' in references:
                    return 'branch', ref
                if f'refs/remotes/origin/{ref}' in references:
                    return 'branch', ref

                # Not found in standard refs, try to resolve it
                try:
                    obj = repo.revparse_single(ref)
                    if obj.type == GitObjectType.COMMIT:
                        return 'commit', ref
                    elif obj.type == GitObjectType.TAG:
                        return 'tag', ref
                    else:
                        return None, ref
                except KeyError:
                    return None, ref
            else:
                # Check current HEAD state
                if repo.is_head_detached():
                    commit = repo.get_head_target()[:7]
                    return 'commit', commit
                else:
                    # HEAD points to a branch
                    branch_name = repo.get_head_shorthand()
                    return 'branch', branch_name

        except GitBackendError:
            return None, ref
        except Exception:
            return None, ref

    @staticmethod
    def switch_ref(plugin, ref, discard_changes=False):
        """Switch plugin to a different git ref (branch/tag/commit).

        Args:
            plugin: Plugin to switch
            ref: Git ref to switch to
            discard_changes: If True, discard uncommitted changes

        Returns:
            tuple: (old_ref, new_ref, old_commit, new_commit)

        Raises:
            PluginDirtyError: If plugin has uncommitted changes and discard_changes=False
        """
        from picard.plugin3.manager import PluginDirtyError

        # Clean Python cache files before checking for changes
        clean_python_cache(plugin.local_path)

        # Check for uncommitted changes
        if not discard_changes:
            changes = GitOperations.check_dirty_working_dir(plugin.local_path)
            if changes:
                raise PluginDirtyError(plugin.plugin_id, changes)

        # Use abstracted git operations for ref switching
        backend = git_backend()
        repo = backend.create_repository(plugin.local_path)

        # Get old ref and commit
        old_commit = repo.get_head_target()
        old_ref = repo.get_head_shorthand() if not repo.is_head_detached() else old_commit[:7]

        # Fetch latest from remote
        callbacks = backend.create_remote_callbacks()
        origin_remote = repo.get_remote('origin')
        repo.fetch_remote(origin_remote, None, callbacks._callbacks)

        # Find the ref
        try:
            references = repo.get_references()

            # Try as branch first
            branch_ref = f'refs/remotes/origin/{ref}'
            if branch_ref in references:
                commit_obj = repo.revparse_single(branch_ref)
                commit = repo.peel_to_commit(commit_obj)
                repo.checkout_tree(commit)
                # Detach HEAD first to avoid "cannot force update current branch" error
                repo.set_head(commit.id)
                # Set branch to track remote
                branches = repo.get_branches()
                # Convert GitObject back to pygit2 object for branch creation
                pygit_commit = repo._repo.get(commit_obj.id)
                branch = branches.local.create(ref, pygit_commit, force=True)
                branch.upstream = branches.remote[f'origin/{ref}']
                # Now point HEAD to the branch
                repo.set_head(f'refs/heads/{ref}')
                log.info('Switched plugin %s to branch %s', plugin.plugin_id, ref)
                return old_ref, ref, old_commit, commit.id

            # Try as tag
            tag_ref = f'refs/tags/{ref}'
            if tag_ref in references:
                commit_obj = repo.revparse_single(tag_ref)
                commit = repo.peel_to_commit(commit_obj)
                repo.checkout_tree(commit)
                repo.set_head(commit.id)
                log.info('Switched plugin %s to tag %s', plugin.plugin_id, ref)
                return old_ref, ref, old_commit, commit.id

            # Try as commit hash
            try:
                commit = repo.revparse_single(ref)
                repo.checkout_tree(commit)
                repo.set_head(commit.id)
                log.info('Switched plugin %s to commit %s', plugin.plugin_id, ref)
                return old_ref, ref[:7], old_commit, commit.id
            except KeyError:
                pass

            raise ValueError(f'Ref {ref} not found')

        except Exception as e:
            log.error('Failed to switch plugin %s to ref %s: %s', plugin.plugin_id, ref, e)
            raise

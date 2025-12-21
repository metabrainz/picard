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
    GitRef,
    GitReferenceError,
    GitRefType,
    GitStatusFlag,
)
from picard.git.factory import git_backend
from picard.git.ref_utils import find_git_ref
from picard.util import parse_versioning_scheme


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
        with backend.create_repository(path) as repo:
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
    def fetch_remote_refs(url, use_callbacks=True, repo_path=None):
        """Fetch remote refs from a git repository.

        Args:
            url: Git repository URL
            use_callbacks: Whether to use GitRemoteCallbacks for authentication
            repo_path: Optional path to existing repository to use instead of creating temporary one

        Returns:
            list: Remote refs, or None on error
        """
        backend = git_backend()
        return backend.fetch_remote_refs(url, use_callbacks=use_callbacks, repo_path=repo_path)

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
                # Parse versioning scheme
                compiled_pattern = parse_versioning_scheme(registry_plugin.versioning_scheme)
                if compiled_pattern and compiled_pattern.match(ref):
                    # It's a version tag - fetch and check
                    remote_refs = GitOperations.fetch_remote_refs(url, use_callbacks=False)
                    if remote_refs:
                        version_tags = []
                        for git_ref in remote_refs:
                            if git_ref.ref_type == GitRefType.TAG and compiled_pattern.match(git_ref.shortname):
                                version_tags.append(git_ref.shortname)

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
            ref_names.append(remote_ref.shortname)
            ref_names.append(remote_ref.name)  # Also add full name

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
            with backend.create_repository(repo_path) as repo:
                if ref:
                    # Use GitRef-based detection
                    git_ref = find_git_ref(repo, ref)
                    if git_ref:
                        if git_ref.ref_type == GitRefType.TAG:
                            return 'tag', ref
                        elif git_ref.ref_type == GitRefType.BRANCH:
                            return 'branch', ref
                    else:
                        # Try as commit hash
                        try:
                            repo.revparse_single(ref)
                            return 'commit', ref
                        except Exception:
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
            tuple: (old_git_ref, new_git_ref, old_commit, new_commit)

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

        try:
            with backend.create_repository(plugin.local_path) as repo:
                # Get old ref and commit
                old_commit = repo.get_head_target()
                old_ref_name = repo.get_head_shorthand() if not repo.is_head_detached() else old_commit[:7]

                # Create old GitRef object
                old_git_ref = GitOperations._create_git_ref_from_current_state(repo, old_ref_name, old_commit)

                # Fetch latest from remote
                GitOperations._fetch_remote_refs(repo, ref, backend)

                # Find the ref
                references = repo.list_references()

                # Try as branch first
                result = GitOperations._try_switch_to_branch(repo, plugin, ref, references, old_ref_name, old_commit)
                if result:
                    new_ref_name, new_commit = result
                    new_git_ref = GitRef(
                        name=f"refs/heads/{new_ref_name}", target=new_commit, ref_type=GitRefType.BRANCH
                    )
                    return old_git_ref, new_git_ref, old_commit, new_commit

                # Try as tag
                result = GitOperations._try_switch_to_tag(repo, plugin, ref, references, old_ref_name, old_commit)
                if result:
                    new_ref_name, new_commit = result
                    new_git_ref = GitRef(name=f"refs/tags/{new_ref_name}", target=new_commit, ref_type=GitRefType.TAG)
                    return old_git_ref, new_git_ref, old_commit, new_commit

                # Try as commit hash or git revision syntax
                result = GitOperations._try_switch_to_commit(repo, plugin, ref, old_ref_name, old_commit)
                if result:
                    new_ref_name, new_commit = result
                    new_git_ref = GitRef(name=new_commit, target=new_commit, ref_type=None)
                    return old_git_ref, new_git_ref, old_commit, new_commit

                raise ValueError(f'Ref {ref} not found')

        except Exception as e:
            log.error('Failed to switch plugin %s to ref %s: %s', plugin.plugin_id, ref, e)
            raise

    @staticmethod
    def _create_git_ref_from_current_state(repo, ref_name, commit):
        """Create GitRef from current repository state."""
        if repo.is_head_detached():
            # Detached HEAD - just a commit
            return GitRef(name=commit[:7], target=commit, ref_type=None)

        # HEAD points to a branch - find the actual GitRef
        git_ref = find_git_ref(repo, ref_name)
        if git_ref:
            return git_ref

        # Fallback: create a basic GitRef
        return GitRef(name=f"refs/heads/{ref_name}", target=commit, ref_type=GitRefType.BRANCH)

    @staticmethod
    def _fetch_remote_refs(repo, ref, backend):
        """Fetch remote refs and optionally specific tag."""
        callbacks = backend.create_remote_callbacks()
        origin_remote = repo.get_remote('origin')
        repo.fetch_remote(origin_remote, None, callbacks._callbacks)

        # If the ref is not found locally, try fetching it specifically
        references = repo.list_references()
        tag_exists = any(r.ref_type == GitRefType.TAG and r.shortname == ref for r in references)
        if not tag_exists and not any(char in ref for char in ['^', '~', ':', '@']):
            try:
                # Fetch the specific tag (only for simple ref names)
                repo.fetch_remote(origin_remote, f'+refs/tags/{ref}:refs/tags/{ref}', callbacks._callbacks)
            except Exception as e:
                # If specific fetch fails, continue with what we have
                log.debug('Failed to fetch specific tag %s: %s', ref, e)

    @staticmethod
    def _try_switch_to_branch(repo, plugin, ref, references, old_ref, old_commit):
        """Try to switch to a branch. Returns tuple or None if not a branch."""
        # Normalize ref (strip origin/ prefix if present)
        local_ref = ref[7:] if ref.startswith('origin/') else ref

        # Find branch reference (local or remote)
        branch_ref = None
        for git_ref in references:
            if git_ref.ref_type == GitRefType.BRANCH and (
                (not git_ref.is_remote and git_ref.shortname == local_ref)
                or (git_ref.is_remote and git_ref.shortname == f'origin/{local_ref}')
            ):
                branch_ref = git_ref.name
                break

        if not branch_ref:
            return None

        commit = repo.revparse_to_commit(branch_ref)
        repo.checkout_tree(commit)

        # Check if we're switching to a remote branch
        is_remote_branch = any(
            git_ref.ref_type == GitRefType.BRANCH and git_ref.is_remote and git_ref.shortname == f'origin/{local_ref}'
            for git_ref in references
        )

        if is_remote_branch:
            # Create local tracking branch
            repo.set_head(commit.id)
            branches = repo.get_branches()
            pygit_commit = repo._repo.get(commit.id)
            branch = branches.local.create(local_ref, pygit_commit, force=True)
            branch.upstream = branches.remote[f'origin/{local_ref}']
            repo.set_head(f'refs/heads/{local_ref}')
        else:
            # Switch to existing local branch
            repo.set_head(branch_ref)

        log.info('Switched plugin %s to branch %s', plugin.plugin_id, local_ref)
        return local_ref, commit.id

    @staticmethod
    def _try_switch_to_tag(repo, plugin, ref, references, old_ref, old_commit):
        """Try to switch to a tag. Returns tuple or None if not a tag."""
        # Find tag reference
        tag_ref = None
        for git_ref in references:
            if git_ref.ref_type == GitRefType.TAG and git_ref.shortname == ref:
                tag_ref = git_ref.name
                break

        if tag_ref:
            commit = repo.revparse_to_commit(tag_ref)
            repo.checkout_tree(commit)
            repo.set_head(commit.id)
            log.info('Switched plugin %s to tag %s', plugin.plugin_id, ref)
            return ref, commit.id

        return None

    @staticmethod
    def _try_switch_to_commit(repo, plugin, ref, old_ref, old_commit):
        """Try to switch to a commit hash or git revision syntax. Returns tuple or None."""
        try:
            commit = repo.revparse_single(ref)
            repo.checkout_tree(commit)
            repo.set_head(commit.id)
            log.info('Switched plugin %s to commit %s', plugin.plugin_id, ref)
            return commit.id[:7], commit.id
        except GitReferenceError:
            # For git revision syntax, provide helpful error message
            if any(char in ref for char in ['^', '~', ':', '@']):
                base_ref = ref.split('^')[0].split('~')[0].split(':')[0].split('@')[0]
                try:
                    origin_ref = f'origin/{base_ref}'
                    repo.revparse_single(origin_ref)
                    raise ValueError(f"Ref '{ref}' not found. Did you mean '{origin_ref}{ref[len(base_ref) :]}'?")
                except GitReferenceError:
                    pass
            return None

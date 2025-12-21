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

"""Pygit2 backend implementation."""

from pathlib import Path
import tempfile
from typing import (
    Any,
    Optional,
)


try:
    import pygit2

    HAS_PYGIT2 = True
except ImportError:
    HAS_PYGIT2 = False
    pygit2 = None

from picard import log
from picard.git.backend import (
    GitBackend,
    GitCommitError,
    GitObject,
    GitObjectType,
    GitRef,
    GitReferenceError,
    GitRefType,
    GitRemoteCallbacks,
    GitRepository,
    GitRepositoryError,
    GitResetMode,
    GitStatusFlag,
    _log_git_call,
)


class Pygit2RemoteCallbacks(GitRemoteCallbacks):
    def __init__(self):
        if not HAS_PYGIT2:
            return
        self._callbacks = pygit2.RemoteCallbacks()
        self._callbacks.transfer_progress = self._transfer_progress
        self._callbacks.credentials = self._credentials
        self._attempted = False

    def _transfer_progress(self, stats):
        pass  # Silent progress

    def _credentials(self, url, username_from_url, allowed_types):
        if self._attempted:
            return None
        self._attempted = True

        if allowed_types & pygit2.GIT_CREDENTIAL_SSH_KEY:
            try:
                return pygit2.Keypair('git', None, None, '')
            except (pygit2.GitError, OSError):
                return None
        elif allowed_types & pygit2.GIT_CREDENTIAL_USERPASS_PLAINTEXT:
            try:
                return pygit2.Username('git')
            except (pygit2.GitError, OSError):
                return None
        return None


class Pygit2Repository(GitRepository):
    def __init__(self, repo):
        self._repo = repo

    def get_status(self) -> dict[str, GitStatusFlag]:
        status = self._repo.status()
        result = {}
        for filepath, flags in status.items():
            if flags == pygit2.GIT_STATUS_CURRENT:
                result[filepath] = GitStatusFlag.CURRENT
            elif flags == pygit2.GIT_STATUS_IGNORED:
                result[filepath] = GitStatusFlag.IGNORED
            else:
                # Any other status means the file is modified/added/deleted/untracked
                result[filepath] = GitStatusFlag.MODIFIED
        _log_git_call("get_status", retval=result)
        return result

    def get_head_target(self) -> str:
        ret = str(self._repo.head.target)
        _log_git_call("get_head_target", retval=ret)
        return ret

    def is_head_detached(self) -> bool:
        ret = self._repo.head_is_detached
        _log_git_call("is_head_detached", retval=ret)
        return ret

    def get_head_shorthand(self) -> str:
        ret = self._repo.head.shorthand
        _log_git_call("get_head_shorthand", retval=ret)
        return ret

    def revparse_single(self, ref: str) -> GitObject:
        try:
            obj = self._repo.revparse_single(ref)
            obj_type = GitObjectType.COMMIT if obj.type == pygit2.GIT_OBJECT_COMMIT else GitObjectType.TAG
            ret = GitObject(str(obj.id), obj_type)
            _log_git_call("revparse_single", ref, retval=ret)
            return ret
        except (pygit2.GitError, KeyError) as e:
            raise GitReferenceError(f"Failed to resolve reference '{ref}': {e}") from e

    def get_head_name(self) -> str:
        _log_git_call("get_head_name")
        return self._repo.head.name

    def peel_to_commit(self, obj: GitObject) -> GitObject:
        pygit_obj = self._repo.get(obj.id)
        if pygit_obj.type == pygit2.GIT_OBJECT_TAG:
            commit = pygit_obj.peel(pygit2.GIT_OBJECT_COMMIT)
            ret = GitObject(str(commit.id), GitObjectType.COMMIT)
        else:
            ret = obj
        _log_git_call("peel_to_commit", obj, retval=ret)
        return ret

    def reset(self, commit_id: str, mode: GitResetMode):
        _log_git_call("reset", commit_id, mode.value)
        self._repo.reset(commit_id, pygit2.enums.ResetMode.HARD)

    def checkout_tree(self, obj: GitObject):
        _log_git_call("checkout_tree", obj)
        pygit_obj = self._repo.get(obj.id)
        self._repo.checkout_tree(pygit_obj)

    def set_head(self, target: str):
        _log_git_call("set_head", target)
        # Try as reference name first, then as commit ID
        try:
            self._repo.set_head(target)
        except (pygit2.GitError, ValueError):
            # If it fails as reference, try as commit ID
            try:
                oid = pygit2.Oid(hex=target)
                self._repo.set_head(oid)
            except (pygit2.GitError, ValueError):
                # Re-raise original error
                self._repo.set_head(target)

    def list_references(self) -> list[GitRef]:
        # Get actual reference objects instead of just names
        ref_objects = []
        for ref_name in self._repo.references:
            ref_objects.append(self._repo.references[ref_name])

        ret = self._create_git_refs(ref_objects, is_remote=False, repo=self._repo)
        _log_git_call("list_references", retval=ret)
        return ret

    @staticmethod
    def _create_git_refs_from_raw_repo(repo, remote_refs, is_remote=True):
        """Helper to create GitRef objects from a raw pygit2.Repository."""
        temp_repo_wrapper = Pygit2Repository(repo)
        return temp_repo_wrapper._create_git_refs(remote_refs, is_remote=is_remote, repo=repo)

    def _create_git_refs(self, refs, is_remote=False, repo=None):
        """Create GitRef objects from pygit2 reference objects"""
        git_refs = []

        # For remote refs, collect all refs first to handle ^{} pairs
        if is_remote:
            ref_dict = {}
            for ref in refs:
                ref_dict[ref.name] = ref

            # Process refs, preferring ^{} versions for tags
            processed_refs = set()
            for ref in refs:
                ref_name = ref.name
                if ref_name in processed_refs:
                    continue

                if ref_name.startswith('refs/tags/') and ref_name.endswith('^{}'):
                    # This is a dereferenced tag - use it and mark the base tag as processed
                    base_name = ref_name[:-3]  # Remove '^{}'
                    processed_refs.add(base_name)
                    processed_refs.add(ref_name)

                    # Create GitRef with clean name but dereferenced target
                    target = str(ref.oid) if hasattr(ref, 'oid') else str(ref.target)
                    git_refs.append(GitRef(base_name, target, GitRefType.TAG, is_remote, True))

                elif ref_name.startswith('refs/tags/'):
                    # Check if there's a ^{} version
                    deref_name = ref_name + '^{}'
                    if deref_name in ref_dict:
                        # Skip this one, the ^{} version will be processed
                        continue
                    else:
                        # No ^{} version, process this tag normally
                        processed_refs.add(ref_name)
                        target = str(ref.oid) if hasattr(ref, 'oid') else str(ref.target)
                        git_refs.append(GitRef(ref_name, target, GitRefType.TAG, is_remote, False))

                else:
                    # Non-tag ref, process normally
                    processed_refs.add(ref_name)
                    self._process_single_ref(ref, git_refs, is_remote, repo)
        else:
            # Local refs - process normally with dereferencing
            for ref in refs:
                self._process_single_ref(ref, git_refs, is_remote, repo)

        return git_refs

    def _process_single_ref(self, ref, git_refs, is_remote, repo):
        """Process a single reference"""
        try:
            ref_name = ref.name

            # Extract target based on object type
            if hasattr(ref, 'target'):
                # Local Reference object
                target = str(ref.target)
            elif hasattr(ref, 'oid'):
                # Remote reference object (from list_heads)
                target = str(ref.oid)
            else:
                # Unknown object type, skip
                return

            # Determine ref type and flags
            if ref_name.startswith('refs/heads/'):
                ref_type = GitRefType.BRANCH
                is_annotated = False
                ref_is_remote = False
            elif ref_name.startswith('refs/remotes/'):
                if ref_name.endswith('/HEAD'):
                    ref_type = GitRefType.HEAD
                    is_annotated = False
                    ref_is_remote = True
                else:
                    ref_type = GitRefType.BRANCH
                    is_annotated = False
                    ref_is_remote = True
            elif ref_name.startswith('refs/tags/'):
                ref_type = GitRefType.TAG
                ref_is_remote = is_remote  # Tags use the method parameter
                # Check if it's an annotated tag and dereference to commit
                try:
                    if hasattr(ref, 'target'):
                        # Local reference
                        obj = repo.get(ref.target)
                    else:
                        # Remote reference
                        obj = repo.get(ref.oid)
                    is_annotated = obj.type == pygit2.GIT_OBJECT_TAG

                    # For annotated tags, dereference to get the commit ID
                    if is_annotated:
                        commit = obj.peel(pygit2.GIT_OBJECT_COMMIT)
                        target = str(commit.id)
                    # For lightweight tags, target is already the commit ID
                except Exception:
                    is_annotated = False
            else:
                ref_type = GitRefType.HEAD
                is_annotated = False
                ref_is_remote = is_remote

            git_refs.append(GitRef(ref_name, target, ref_type, ref_is_remote, is_annotated))
        except Exception:
            # Skip refs that can't be resolved
            pass

    def get_remotes(self) -> list[Any]:
        ret = self._repo.remotes
        _log_git_call("get_remotes", retval=[name for name in self._repo.remotes.names()])
        return ret

    def get_remote(self, name: str) -> Any:
        ret = self._repo.remotes[name]
        _log_git_call("get_remote", name, retval=ret)
        return ret

    def create_remote(self, name: str, url: str) -> Any:
        ret = self._repo.remotes.create(name, url)
        _log_git_call("create_remote", name, url, retval=ret)
        return ret

    def get_branches(self) -> Any:
        ret = self._repo.branches
        _log_git_call("get_branches", retval=ret)
        return ret

    def get_commit_date(self, commit_id: str) -> int:
        commit = self._repo.get(commit_id)
        _log_git_call("get_commit_date", commit_id, retval=commit.commit_time)
        return commit.commit_time

    def fetch_remote(self, remote, refspec: str = None, callbacks=None):
        _log_git_call("fetch_remote", str(remote.name), refspec)
        if refspec:
            remote.fetch([refspec], callbacks=callbacks)
        else:
            remote.fetch(callbacks=callbacks)

    def fetch_remote_with_tags(self, remote, refspec: str = None, callbacks=None):
        """Fetch from remote including tags."""
        _log_git_call("fetch_remote_with_tags", str(remote.name), refspec)
        if refspec:
            # Combine provided refspec with tag refspec
            refspecs = [refspec, '+refs/tags/*:refs/tags/*']
        else:
            # Combine default fetch refspecs with tag refspec
            refspecs = list(remote.fetch_refspecs) + ['+refs/tags/*:refs/tags/*']
        remote.fetch(refspecs, callbacks=callbacks)

    def free(self):
        _log_git_call("free")
        self._repo.free()


class Pygit2Backend(GitBackend):
    def __init__(self):
        if not HAS_PYGIT2:
            raise ImportError("pygit2 not available")

    def create_repository(self, path: Path) -> GitRepository:
        _log_git_call("create_repository", str(path))
        try:
            repo = pygit2.Repository(str(path))
            return Pygit2Repository(repo)
        except pygit2.GitError as e:
            raise GitRepositoryError(f"Failed to open repository at '{path}': {e}") from e

    def init_repository(self, path: Path, bare: bool = False) -> GitRepository:
        _log_git_call("init_repository", str(path), bare)
        repo = pygit2.init_repository(str(path), bare=bare)
        return Pygit2Repository(repo)

    def create_commit(
        self, repo: GitRepository, message: str, author_name: str = "Test", author_email: str = "test@example.com"
    ) -> str:
        pygit_repo = repo._repo
        index = pygit_repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        author = pygit2.Signature(author_name, author_email)
        commit_id = pygit_repo.create_commit('refs/heads/main', author, author, message, tree, [])
        pygit_repo.set_head('refs/heads/main')
        ret = str(commit_id)
        _log_git_call("create_commit", message, author_name, author_email, retval=ret)
        return ret

    def create_tag(
        self,
        repo: GitRepository,
        tag_name: str,
        commit_id: str,
        message: str = "",
        author_name: str = "Test",
        author_email: str = "test@example.com",
    ):
        _log_git_call("create_tag", tag_name, commit_id, message)
        pygit_repo = repo._repo
        author = pygit2.Signature(author_name, author_email)
        pygit_repo.create_tag(tag_name, commit_id, pygit2.GIT_OBJECT_COMMIT, author, message)

    def create_branch(self, repo: GitRepository, branch_name: str, commit_id: str):
        _log_git_call("create_branch", branch_name, commit_id)
        pygit_repo = repo._repo
        # Create branch reference pointing to the commit
        pygit_repo.create_reference(f'refs/heads/{branch_name}', commit_id)

    def add_and_commit_files(
        self, repo: GitRepository, message: str, author_name: str = "Test", author_email: str = "test@example.com"
    ) -> str:
        try:
            pygit_repo = repo._repo
            index = pygit_repo.index
            index.add_all()
            index.write()
            tree = index.write_tree()
            author = pygit2.Signature(author_name, author_email)

            # Get current HEAD as parent, or empty list if no commits yet
            try:
                parent = [pygit_repo.head.target]
            except pygit2.GitError:
                parent = []

            commit_id = pygit_repo.create_commit('refs/heads/main', author, author, message, tree, parent)
            if not parent:  # First commit, set HEAD
                pygit_repo.set_head('refs/heads/main')
            ret = str(commit_id)
            _log_git_call("add_and_commit_files", message, author_name, author_email, retval=ret)
            return ret
        except pygit2.GitError as e:
            raise GitCommitError(f"Failed to create commit: {e}") from e

    def reset_hard(self, repo: GitRepository, commit_id: str):
        _log_git_call("reset_hard", commit_id)
        pygit_repo = repo._repo
        pygit_repo.reset(commit_id, pygit2.enums.ResetMode.HARD)

    def create_reference(self, repo: GitRepository, ref_name: str, commit_id: str):
        _log_git_call("create_reference", ref_name, commit_id)
        pygit_repo = repo._repo
        pygit_repo.create_reference(ref_name, commit_id)

    def set_head_detached(self, repo: GitRepository, commit_id: str):
        _log_git_call("set_head_detached", commit_id)
        pygit_repo = repo._repo

        # To create a true detached HEAD, we need to make HEAD point directly to a commit
        # rather than to a branch reference
        oid = pygit2.Oid(hex=commit_id)

        # Delete the HEAD symbolic reference and create a direct reference
        try:
            # Remove the symbolic HEAD reference
            head_ref = pygit_repo.references['HEAD']
            head_ref.delete()
        except (KeyError, pygit2.GitError):
            # HEAD reference may not exist or may not be deletable
            pass

        # Create a new HEAD that points directly to the commit
        pygit_repo.references.create('HEAD', oid, force=True)
        pygit_repo.checkout_head()

    def clone_repository(self, url: str, path: Path, **options) -> GitRepository:
        _log_git_call("clone_repository", url, str(path), **options)
        callbacks = options.pop('callbacks', None)
        if callbacks and isinstance(callbacks, Pygit2RemoteCallbacks):
            options['callbacks'] = callbacks._callbacks
        elif callbacks:
            # Handle backend callbacks
            options['callbacks'] = callbacks._callbacks
        repo = pygit2.clone_repository(url, str(path.absolute()), **options)
        return Pygit2Repository(repo)

    def fetch_remote_refs(self, url: str, **options) -> Optional[list[GitRef]]:
        _log_git_call("fetch_remote_refs", url, **options)

        # Check if we can use an existing repository
        repo_path = options.get('repo_path')
        if repo_path and Path(repo_path).exists() and (Path(repo_path) / '.git').exists():
            try:
                repo = pygit2.Repository(str(repo_path))

                # Get all references and filter to show clean branch names
                all_refs = [repo.references[name] for name in repo.references]
                git_refs = Pygit2Repository._create_git_refs_from_raw_repo(repo, all_refs, is_remote=False)

                return self._filter_refs_for_display(git_refs)
            except Exception as e:
                log.debug('Failed to use existing repo at %s: %s', repo_path, e)
                # Fall through to temporary repository method

        # Fallback to temporary bare repository
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = pygit2.init_repository(tmpdir, bare=True)
                remote = repo.remotes.create('origin', url)

                use_callbacks = options.get('use_callbacks', True)
                if use_callbacks:
                    callbacks = self.create_remote_callbacks()
                    remote_refs = remote.list_heads(callbacks=callbacks._callbacks)
                else:
                    remote_refs = remote.list_heads()

                return Pygit2Repository._create_git_refs_from_raw_repo(repo, remote_refs, is_remote=True)
        except Exception as e:
            log.warning('Failed to fetch remote refs from %s: %s', url, e)
            return None

    def _filter_refs_for_display(self, git_refs):
        """Filter refs to show clean branch names (local over remote)."""
        local_branches = {r.shortname for r in git_refs if r.ref_type == GitRefType.BRANCH and not r.is_remote}

        filtered = []
        for ref in git_refs:
            # Skip remote branches if local equivalent exists
            if (
                ref.ref_type == GitRefType.BRANCH
                and ref.is_remote
                and ref.shortname.startswith('origin/')
                and ref.shortname[7:] in local_branches
            ):
                continue
            # Skip remote HEAD references
            if ref.ref_type == GitRefType.HEAD and ref.is_remote:
                continue
            filtered.append(ref)

        return filtered

    def create_remote_callbacks(self) -> GitRemoteCallbacks:
        _log_git_call("create_remote_callbacks")
        return Pygit2RemoteCallbacks()

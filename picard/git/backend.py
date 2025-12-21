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

"""Git backend abstraction layer."""

from abc import (
    ABC,
    abstractmethod,
)
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Optional,
)

from picard import log
from picard.debug_opts import DebugOpt


class GitBackendError(Exception):
    """Base exception for git backend operations"""


class GitRepositoryError(GitBackendError):
    """Exception for repository-related errors"""


class GitReferenceError(GitBackendError):
    """Exception for reference-related errors"""


class GitCommitError(GitBackendError):
    """Exception for commit-related errors"""


class GitObjectType(Enum):
    COMMIT = "commit"
    TAG = "tag"


class GitStatusFlag(Enum):
    CURRENT = 0
    IGNORED = 1
    MODIFIED = 2


class GitResetMode(Enum):
    HARD = "hard"


class GitCredentialType(Enum):
    SSH_KEY = 1
    USERPASS = 2


class GitRefType(Enum):
    BRANCH = "branch"
    TAG = "tag"
    HEAD = "head"


class GitRef:
    def __init__(
        self,
        name: str,
        target: str = None,
        ref_type: GitRefType = None,
        is_remote: bool = False,
        is_annotated: bool = False,
    ):
        self.name = name
        self.target = target
        self.ref_type = ref_type
        self.is_remote = is_remote
        self.is_annotated = is_annotated
        self.shortname = self._extract_shortname()

    def _extract_shortname(self) -> str:
        """Extract short name from full ref name"""
        if self.name.startswith('refs/heads/'):
            return self.name[11:]  # len('refs/heads/')
        elif self.name.startswith('refs/tags/'):
            return self.name[10:]  # len('refs/tags/')
        elif self.name.startswith('refs/remotes/'):
            return self.name[13:]  # len('refs/remotes/')
        else:
            return self.name  # HEAD, etc.

    def to_tuple(self):
        """Serialize GitRef to tuple for storage."""
        return (
            self.name,
            self.target,
            self.ref_type.value if self.ref_type else None,
            self.is_remote,
            self.is_annotated,
        )

    @classmethod
    def from_tuple(cls, data):
        """Deserialize GitRef from tuple."""
        if not data or len(data) < 3:
            return cls(name='', target='')

        name, target, ref_type_str = data[:3]
        is_remote = data[3] if len(data) > 3 else False
        is_annotated = data[4] if len(data) > 4 else False

        ref_type = None
        if ref_type_str:
            try:
                ref_type = GitRefType(ref_type_str)
            except ValueError:
                pass  # Invalid ref_type, keep as None

        return cls(
            name=name or '',
            target=target or '',
            ref_type=ref_type,
            is_remote=is_remote,
            is_annotated=is_annotated,
        )

    def __repr__(self):
        parts = [f"name='{self.name}'", f"target='{self.target}'"]
        if self.ref_type:
            parts.append(f"type={self.ref_type.value}")
        if self.is_remote:
            parts.append("remote=True")
        if self.is_annotated:
            parts.append("annotated=True")
        return f"GitRef({', '.join(parts)})"


class GitObject:
    def __init__(self, id: str, obj_type: GitObjectType):
        self.id = id
        self.type = obj_type

    def __repr__(self):
        return 'GitObject(%r, %r)' % (self.id, self.type)


class GitRemoteCallbacks:
    """Abstract remote callbacks for authentication"""


def _log_git_call(method_name: str, *args, **kwargs):
    """Log git backend method calls if debug option enabled"""
    if DebugOpt.GIT_BACKEND.enabled:
        has_retval = 'retval' in kwargs
        if has_retval:
            retval = kwargs.pop('retval')
        args_str = ', '.join(str(arg)[:100] for arg in args)  # Truncate long args
        kwargs_str = ', '.join(f'{k}={str(v)[:50]}' for k, v in kwargs.items())
        all_args = ', '.join(filter(None, [args_str, kwargs_str]))
        msg = "Git backend call: %s(%s)" % (method_name, all_args)
        if has_retval:
            msg += ' => %r' % retval
        log.debug(msg)


class GitRepository(ABC):
    """Abstract interface for repository operations"""

    @abstractmethod
    def get_status(self) -> dict[str, GitStatusFlag]:
        """Get working directory status"""

    @abstractmethod
    def get_head_target(self) -> str:
        """Get HEAD commit ID"""

    @abstractmethod
    def is_head_detached(self) -> bool:
        """Check if HEAD is detached"""

    @abstractmethod
    def get_head_shorthand(self) -> str:
        """Get current branch name or short commit"""

    @abstractmethod
    def get_head_name(self) -> str:
        """Get HEAD reference name"""

    @abstractmethod
    def revparse_single(self, ref: str) -> GitObject:
        """Resolve reference to object"""

    @abstractmethod
    def peel_to_commit(self, obj: GitObject) -> GitObject:
        """Peel tag to underlying commit"""

    def revparse_to_commit(self, ref: str) -> GitObject:
        """Resolve reference to commit, peeling tags if necessary"""
        obj = self.revparse_single(ref)
        return self.peel_to_commit(obj)

    @abstractmethod
    def reset(self, commit_id: str, mode: GitResetMode):
        """Reset repository to commit"""

    def reset_to_commit(self, commit_id: str, hard: bool = False):
        """Reset repository to commit with simplified API"""
        mode = GitResetMode.HARD if hard else GitResetMode.HARD  # Only HARD mode is defined
        self.reset(commit_id, mode)

    @abstractmethod
    def checkout_tree(self, obj: GitObject):
        """Checkout tree object"""

    @abstractmethod
    def set_head(self, target: str):
        """Set HEAD to target"""

    @abstractmethod
    def list_references(self) -> list[GitRef]:
        """List all references"""

    @abstractmethod
    def get_remotes(self) -> list[Any]:
        """Get remotes list"""

    @abstractmethod
    def get_remote(self, name: str) -> Any:
        """Get specific remote by name"""

    @abstractmethod
    def create_remote(self, name: str, url: str) -> Any:
        """Create remote"""

    @abstractmethod
    def get_branches(self) -> Any:
        """Get branches object"""

    @abstractmethod
    def get_commit_date(self, commit_id: str) -> int:
        """Get commit timestamp for given commit ID"""

    @abstractmethod
    def fetch_remote(self, remote, refspec: str = None, callbacks=None):
        """Fetch from remote with optional refspec"""

    @abstractmethod
    def fetch_remote_with_tags(self, remote, refspec: str = None, callbacks=None):
        """Fetch from remote including tags"""

    @abstractmethod
    def free(self):
        """Free repository resources"""

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - always free resources"""
        self.free()
        return False


class GitBackend(ABC):
    """Abstract interface for git operations"""

    @abstractmethod
    def create_repository(self, path: Path) -> GitRepository:
        """Open existing repository"""

    @abstractmethod
    def init_repository(self, path: Path, bare: bool = False) -> GitRepository:
        """Initialize new repository"""

    @abstractmethod
    def create_commit(
        self, repo: GitRepository, message: str, author_name: str = "Test", author_email: str = "test@example.com"
    ) -> str:
        """Create a commit with all staged files"""

    @abstractmethod
    def create_tag(
        self,
        repo: GitRepository,
        tag_name: str,
        commit_id: str,
        message: str = "",
        author_name: str = "Test",
        author_email: str = "test@example.com",
    ):
        """Create a tag pointing to a commit"""

    @abstractmethod
    def create_branch(self, repo: GitRepository, branch_name: str, commit_id: str):
        """Create a branch pointing to a commit"""

    @abstractmethod
    def add_and_commit_files(
        self, repo: GitRepository, message: str, author_name: str = "Test", author_email: str = "test@example.com"
    ) -> str:
        """Add all files and create commit"""

    @abstractmethod
    def reset_hard(self, repo: GitRepository, commit_id: str):
        """Reset repository to commit (hard reset)"""

    @abstractmethod
    def create_reference(self, repo: GitRepository, ref_name: str, commit_id: str):
        """Create a reference pointing to commit"""

    @abstractmethod
    def set_head_detached(self, repo: GitRepository, commit_id: str):
        """Set HEAD to detached state at commit"""

    @abstractmethod
    def clone_repository(self, url: str, path: Path, **options) -> GitRepository:
        """Clone repository from URL"""

    @abstractmethod
    def fetch_remote_refs(self, url: str, **options) -> Optional[list[GitRef]]:
        """Fetch remote refs without cloning

        Args:
            url: Git repository URL
            **options: Additional options including:
                - repo_path: Optional Path to existing repository to use instead of creating temporary one
        """

    @abstractmethod
    def create_remote_callbacks(self) -> GitRemoteCallbacks:
        """Create remote callbacks for authentication"""

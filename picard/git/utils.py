# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
# Copyright (C) 2024 Laurent Monin
# Copyright (C) 2025 Laurent Monin
# Copyright (C) 2025 Philipp Wolfer
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

"""Git URL and path utility functions."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Optional

from picard.i18n import gettext as _


@lru_cache(maxsize=256)
def normalize_git_url(url):
    """Normalize git URL for comparison (expand local paths to absolute).

    Args:
        url: Git URL or local path

    Returns:
        str: Normalized URL
    """
    if not url:
        return url
    # Check if it's a local path (not a remote protocol)
    # Git supports many protocols: http://, https://, git://, ssh://, ftp://, ftps://, etc.
    # If it doesn't contain :// or starts with file://, treat as local path
    if '://' not in url or url.startswith('file://'):
        # Strip file:// prefix if present
        if url.startswith('file://'):
            url = url[7:]
        # Expand ~ and make absolute
        expanded = os.path.expanduser(url)
        return os.path.abspath(expanded)
    return url


def is_local_path(url):
    """Check if URL is a local path (not a remote git URL).

    Args:
        url: Git URL or local path

    Returns:
        bool: True if local path, False if remote URL

    Git supports several URL formats:
    - scheme://... (http, https, git, ssh, ftp, ftps, file, etc.)
    - user@host:path (scp-like syntax)
    - /absolute/path or ~/path or relative/path (local paths)
    """
    if not url:
        return False

    # If it has ://, it's a URL with a scheme (unless file://)
    if '://' in url:
        return url.startswith('file://')

    # Check for scp-like syntax: user@host:path
    # This has a colon but not :// and has @ before the colon
    if ':' in url and '@' in url:
        at_pos = url.find('@')
        colon_pos = url.find(':')
        # If @ comes before : and there's no /, it's scp-like syntax
        if at_pos < colon_pos and '/' not in url[:colon_pos]:
            return False

    # Everything else is a local path
    return True


def get_local_path(url):
    """Get normalized local path if URL is local, None otherwise.

    Args:
        url: Git URL or local path

    Returns:
        Path: Normalized local path if URL is local, None if remote
    """
    if not is_local_path(url):
        return None
    # Strip file:// prefix if present
    if url.startswith('file://'):
        url = url[7:]
    # Expand ~ and make absolute
    expanded = os.path.expanduser(url)
    return Path(os.path.abspath(expanded))


def get_local_repository_path(url):
    """Get local repository path if URL is local git directory, None otherwise.

    Args:
        url: Git URL or local path

    Returns:
        Path: Normalized local git directory path if exists, None otherwise
    """
    local_path = get_local_path(url)
    if local_path and local_path.is_dir() and (local_path / '.git').exists():
        return local_path
    return None


def check_local_repo_dirty(url):
    """Check if URL points to local git repo with uncommitted changes.

    Args:
        url: Git URL or local path

    Returns:
        bool: True if local repo has uncommitted changes, False otherwise
    """
    local_path = get_local_repository_path(url)
    if not local_path:
        return False

    try:
        from picard.git.factory import git_backend

        backend = git_backend()
        repo = backend.create_repository(local_path)
        status = repo.get_status()
        return bool(status)
    except Exception:
        return False


@dataclass
class RefItem:
    """Represents a git reference with display formatting."""

    name: str
    commit: Optional[str] = None
    is_current: bool = False
    is_tag: bool = False
    is_branch: bool = False

    def __eq__(self, other):
        """Check equality based on name and commit."""
        if not isinstance(other, RefItem):
            return False
        return self.name == other.name and self.commit == other.commit

    def __hash__(self):
        """Make RefItem hashable for use in sets and dicts."""
        return hash((self.name, self.commit))

    def __lt__(self, other):
        """Enable sorting of RefItems (tags first, then branches, then by name)."""
        if not isinstance(other, RefItem):
            return NotImplemented

        # Tags come before branches
        if self.is_tag and not other.is_tag:
            return True
        if not self.is_tag and other.is_tag:
            return False

        # Within same type, sort by name
        return self.name < other.name

    def format(self, ref_formatter=None, commit_formatter=None, current_formatter=None) -> str:
        """Format ref and commit for display."""
        from picard.plugin3.plugin import short_commit_id

        # Shorten commit for display
        short_commit = short_commit_id(self.commit) if self.commit else ""

        # Apply formatters if provided
        formatted_ref = ref_formatter(self.name) if ref_formatter and self.name else self.name
        formatted_commit = commit_formatter(short_commit) if commit_formatter and short_commit else short_commit

        if self.name and short_commit:
            # If ref is the same as commit (commit hash used as ref), just show @commit
            if self.name == self.commit or self.name == short_commit:
                base = f"@{formatted_commit}"
            else:
                base = f"{formatted_ref} @{formatted_commit}"
        elif self.name:
            base = formatted_ref
        elif short_commit:
            base = f"@{formatted_commit}"
        else:
            base = ""

        # Apply current formatter if this is the current ref
        if self.is_current and current_formatter:
            return current_formatter(base)
        elif self.is_current:
            return _("{base} (current)").format(base=base)
        else:
            return base

    def is_valid(self) -> bool:
        """Check if RefItem has valid data."""
        return bool(self.name or self.commit)

    def is_commit_only(self) -> bool:
        """Check if this RefItem represents a commit without a named ref."""
        return bool(self.commit and (not self.name or self.name == self.commit or self.name == self.commit[:7]))

    def get_ref_type(self) -> str:
        """Get the type of reference as a string."""
        if self.is_tag:
            return "tag"
        elif self.is_branch:
            return "branch"
        elif self.is_commit_only():
            return "commit"
        else:
            return "unknown"

    def copy(self, **kwargs):
        """Create a copy of this RefItem with optional field overrides."""
        return RefItem(
            name=kwargs.get('name', self.name),
            commit=kwargs.get('commit', self.commit),
            is_current=kwargs.get('is_current', self.is_current),
            is_tag=kwargs.get('is_tag', self.is_tag),
            is_branch=kwargs.get('is_branch', self.is_branch),
        )

    def to_dict(self):
        """Serialize RefItem to dictionary for caching."""
        return {
            'name': self.name,
            'commit': self.commit,
            'is_tag': self.is_tag,
            'is_branch': self.is_branch,
            'is_current': self.is_current,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize RefItem from dictionary with validation."""
        if not isinstance(data, dict):
            raise ValueError("RefItem data must be a dictionary")

        # Validate required fields
        name = data.get('name', '')
        commit = data.get('commit', '')

        if not name and not commit:
            raise ValueError("RefItem must have either name or commit")

        return cls(
            name=name,
            commit=commit,
            is_tag=data.get('is_tag', False),
            is_branch=data.get('is_branch', False),
            is_current=data.get('is_current', False),
        )

    @classmethod
    def create_from_ref_name(cls, ref_name: str, commit: str = '', is_current: bool = False):
        """Create RefItem from ref name with automatic type detection."""
        if not ref_name:
            return cls(name='', commit=commit, is_current=is_current)

        # Detect ref type from name
        is_tag = ref_name.startswith('refs/tags/') or not ref_name.startswith('refs/')
        is_branch = ref_name.startswith('refs/heads/') or ref_name.startswith('refs/remotes/')

        # Clean up ref name for display
        display_name = ref_name
        if ref_name.startswith('refs/tags/'):
            display_name = ref_name[10:]  # Remove 'refs/tags/'
        elif ref_name.startswith('refs/heads/'):
            display_name = ref_name[11:]  # Remove 'refs/heads/'
        elif ref_name.startswith('refs/remotes/origin/'):
            display_name = ref_name[20:]  # Remove 'refs/remotes/origin/'

        return cls(
            name=display_name,
            commit=commit,
            is_current=is_current,
            is_tag=is_tag,
            is_branch=is_branch,
        )

    @classmethod
    def for_logging(cls, name: str = '', commit: str = ''):
        """Create minimal RefItem for logging purposes only."""
        if not name and not commit:
            return None
        return cls(name=name, commit=commit)

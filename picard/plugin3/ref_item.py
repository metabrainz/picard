# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Philipp Wolfer
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

from picard.git.backend import GitRef, GitRefType


class RefItem:
    """Plugin-specific reference item that stores shortnames and converts to GitRef for git operations."""

    class Type(Enum):
        BRANCH = "branch"
        TAG = "tag"
        HEAD = "head"
        COMMIT = "commit"

    def __init__(self, shortname: str, ref_type: 'RefItem.Type | None' = None, commit: str = None):
        self.shortname = shortname
        self.ref_type = ref_type if ref_type is not None else RefItem.Type.COMMIT
        self.commit = commit

    def to_git_ref(self) -> GitRef:
        """Convert to GitRef for git operations."""
        if self.ref_type == RefItem.Type.BRANCH:
            git_ref_type = GitRefType.BRANCH
            full_name = f"refs/heads/{self.shortname}"
        elif self.ref_type == RefItem.Type.TAG:
            git_ref_type = GitRefType.TAG
            full_name = f"refs/tags/{self.shortname}"
        elif self.ref_type == RefItem.Type.HEAD:
            git_ref_type = GitRefType.HEAD
            full_name = "HEAD"
        else:  # COMMIT
            git_ref_type = None
            full_name = self.shortname  # commit hash as-is

        return GitRef(name=full_name, target=self.commit, ref_type=git_ref_type)

    @classmethod
    def from_git_ref(cls, git_ref: GitRef) -> 'RefItem':
        """Convert from GitRef."""
        if git_ref.ref_type == GitRefType.BRANCH:
            ref_type = RefItem.Type.BRANCH
        elif git_ref.ref_type == GitRefType.TAG:
            ref_type = RefItem.Type.TAG
        elif git_ref.ref_type == GitRefType.HEAD:
            ref_type = RefItem.Type.HEAD
        else:
            ref_type = RefItem.Type.COMMIT

        return cls(git_ref.shortname, ref_type, git_ref.target)

    def format(self, is_current=False, ref_formatter=None, commit_formatter=None, current_formatter=None) -> str:
        """Format ref and commit for display."""
        from picard.i18n import _
        from picard.plugin3.plugin import short_commit_id

        # Shorten commit for display
        short_commit = short_commit_id(self.commit) if self.commit else ""

        # Apply formatters if provided
        formatted_ref = ref_formatter(self.shortname) if ref_formatter and self.shortname else self.shortname
        formatted_commit = commit_formatter(short_commit) if commit_formatter and short_commit else short_commit

        if self.shortname and short_commit:
            # If ref is the same as commit (commit hash used as ref), just show @commit
            if self.shortname == self.commit or self.shortname == short_commit:
                base = f"@{formatted_commit}"
            else:
                base = f"{formatted_ref} @{formatted_commit}"
        elif self.shortname:
            base = formatted_ref
        elif short_commit:
            base = f"@{formatted_commit}"
        else:
            base = ""

        # Apply current formatter if this is the current ref
        if is_current and current_formatter:
            return current_formatter(base)
        elif is_current:
            return _("{base} (current)").format(base=base)
        else:
            return base

    def to_tuple(self):
        """Serialize RefItem to tuple for storage."""
        return (
            self.shortname,
            self.commit,
            self.ref_type.value,
        )

    @classmethod
    def from_tuple(cls, data):
        """Deserialize RefItem from tuple."""
        if not data or len(data) < 3:
            return cls('')

        shortname, commit, ref_type_str = data[:3]

        ref_type = None
        if ref_type_str:
            try:
                ref_type = RefItem.Type(ref_type_str)
            except ValueError:
                pass  # Invalid ref_type, will default to COMMIT

        return cls(
            shortname=shortname or '',
            ref_type=ref_type,
            commit=commit or '',
        )

    def __repr__(self):
        parts = [f"shortname='{self.shortname}'", f"commit='{self.commit}'"]
        if self.ref_type:
            parts.append(f"type={self.ref_type.value}")
        return f"RefItem({', '.join(parts)})"

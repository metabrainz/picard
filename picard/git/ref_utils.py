# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Laurent Monin
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

"""Git reference utilities for robust reference type detection."""


def get_ref_type(repo, ref):
    """Determine the type of a git reference.

    Args:
        repo: Git repository object
        ref: Reference name to check

    Returns:
        tuple: (ref_type, resolved_ref) where ref_type is one of:
               'tag', 'local_branch', 'remote_branch', 'commit', 'unknown'
    """
    if not ref:
        return 'unknown', ref

    try:
        # Get all references from the repository
        references = repo.get_references()

        # Check exact matches first
        if f'refs/tags/{ref}' in references:
            return 'tag', f'refs/tags/{ref}'
        if f'refs/heads/{ref}' in references:
            return 'local_branch', f'refs/heads/{ref}'
        if f'refs/remotes/{ref}' in references:
            return 'remote_branch', f'refs/remotes/{ref}'
        if f'refs/remotes/origin/{ref}' in references:
            return 'remote_branch', f'refs/remotes/origin/{ref}'

        # Check if ref is already a full reference
        if ref in references:
            if ref.startswith('refs/tags/'):
                return 'tag', ref
            elif ref.startswith('refs/heads/'):
                return 'local_branch', ref
            elif ref.startswith('refs/remotes/'):
                return 'remote_branch', ref

        # Try to resolve as commit hash
        try:
            repo.revparse_single(ref)
            return 'commit', ref
        except KeyError:
            pass

    except Exception:
        # If we can't get references, fall back to string analysis
        if ref.startswith('refs/tags/'):
            return 'tag', ref
        elif ref.startswith('refs/heads/'):
            return 'local_branch', ref
        elif ref.startswith('refs/remotes/') or ref.startswith('origin/'):
            return 'remote_branch', ref

    return 'unknown', ref

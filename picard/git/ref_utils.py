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

"""Minimal git reference utilities."""


def resolve_ref(repo, ref):
    """Resolve a reference to its full path and type.

    Args:
        repo: Git repository object
        ref: Reference name to resolve

    Returns:
        tuple: (resolved_ref_path, is_tag, is_branch)
    """
    if not ref:
        return ref, False, False

    try:
        references = repo.get_references()

        # Check for tag
        tag_ref = f'refs/tags/{ref}'
        if tag_ref in references:
            return tag_ref, True, False

        # Check for local branch
        branch_ref = f'refs/heads/{ref}'
        if branch_ref in references:
            return branch_ref, False, True

        # Check for remote branch
        remote_ref = f'refs/remotes/origin/{ref}'
        if remote_ref in references:
            return remote_ref, False, True

        # Check if already full reference
        if ref in references:
            is_tag = ref.startswith('refs/tags/')
            is_branch = ref.startswith(('refs/heads/', 'refs/remotes/'))
            return ref, is_tag, is_branch

        # Not a named reference, assume commit
        return ref, False, False

    except Exception:
        return ref, False, False

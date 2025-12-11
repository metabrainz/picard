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

"""Git backend factory."""

from picard.git.backend import GitBackend


def get_git_backend() -> GitBackend:
    """Get the configured git backend.

    Currently only supports pygit2 backend.
    Future backends (CLI, dulwich) can be added here.
    """
    from picard.plugin3.pygit2_backend import Pygit2Backend

    return Pygit2Backend()


def has_git_backend() -> bool:
    """Check if a git backend is available."""
    from picard.plugin3.pygit2_backend import HAS_PYGIT2

    return HAS_PYGIT2


# Global backend instance
_git_backend = None


def git_backend() -> GitBackend:
    """Get singleton git backend instance"""
    global _git_backend
    if _git_backend is None:
        _git_backend = get_git_backend()
    return _git_backend


def _reset_git_backend():
    """Reset the global git backend instance. Used for testing."""
    global _git_backend
    _git_backend = None

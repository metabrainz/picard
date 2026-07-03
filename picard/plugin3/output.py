# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2026 Laurent Monin
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

"""Plugin CLI output with git/plugin-specific display methods."""

from picard.cli.output import CliOutput


class PluginOutput(CliOutput):
    """Output wrapper for plugin CLI commands.

    Extends CliOutput with display methods specific to plugin management
    (git commits, UUIDs, etc.).
    """

    def d_git_info(self, info):
        """Display git info (branch/commit)."""
        return self._colorize(info, self.DIM)

    def d_commit_old(self, commit):
        """Display old/current commit hash."""
        return self._colorize(commit, self.DIM)

    def d_commit_new(self, commit):
        """Display new/updated commit hash."""
        return self._colorize(commit, self.GREEN)

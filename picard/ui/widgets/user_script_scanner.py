# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""User script scanner for completion system.

This module provides functionality to scan all user tagging scripts
for variable definitions to enhance autocompletion.
"""

import contextlib

from picard.script import iter_active_tagging_scripts

from picard.ui.widgets.variable_extractor import VariableExtractor


class UserScriptScanner:
    """Scans all user tagging scripts for variable definitions.

    This class handles scanning of user tagging scripts to extract
    variable names defined via $set() functions, providing them
    for autocompletion across all user scripts.

    Parameters
    ----------
    variable_extractor : VariableExtractor
        The variable extractor to use for parsing script content.
    """

    def __init__(self, variable_extractor: VariableExtractor):
        """Initialize the user script scanner.

        Parameters
        ----------
        variable_extractor : VariableExtractor
            The variable extractor to use for parsing script content.
        """
        self._variable_extractor = variable_extractor
        self._cached_variables: set[str] = set()
        self._last_scan_hash: int | None = None

    def _calculate_scripts_hash(self, scripts) -> int:
        """Calculate hash for a list of scripts.

        Parameters
        ----------
        scripts : list
            List of script objects with name and content attributes.

        Returns
        -------
        int
            Hash value for the scripts.
        """
        return hash(tuple((s.name, s.content) for s in scripts))

    def scan_all_user_scripts(self) -> set[str]:
        """Scan all enabled user tagging scripts for variable definitions.

        Returns
        -------
        set[str]
            Set of variable names found in all user scripts.
        """
        all_variables = set()

        with contextlib.suppress(AttributeError, TypeError, ValueError):
            current_scripts = list(iter_active_tagging_scripts())
            current_hash = self._calculate_scripts_hash(current_scripts)

            for script in current_scripts:
                if script.content:
                    variables = self._variable_extractor.extract_variables(script.content)
                    all_variables.update(variables)

            # Update the hash after successful scan
            self._last_scan_hash = current_hash

        self._cached_variables = all_variables
        return all_variables

    def get_cached_variables(self) -> set[str]:
        """Get cached variables from last scan.

        Returns
        -------
        set[str]
            Set of variable names from the last successful scan.
        """
        return self._cached_variables.copy()

    def should_rescan(self) -> bool:
        """Check if user scripts have changed since last scan.

        Returns
        -------
        bool
            True if scripts have changed and need rescanning.
        """
        with contextlib.suppress(AttributeError, TypeError, ValueError):
            current_scripts = list(iter_active_tagging_scripts())
            current_hash = self._calculate_scripts_hash(current_scripts)

            if current_hash != self._last_scan_hash:
                self._last_scan_hash = current_hash
                return True
            return False

        # If we can't determine if scripts changed, assume they did
        return True

    def force_rescan(self) -> set[str]:
        """Force a rescan of all user scripts.

        Returns
        -------
        set[str]
            Set of variable names found in all user scripts.
        """
        self._last_scan_hash = None
        return self.scan_all_user_scripts()

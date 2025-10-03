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

"""Completion choices provider for script completion."""

from collections.abc import Callable, Iterable, Iterator

from picard.script import script_function_names

from picard.ui.widgets.context_detector import CompletionMode


class CompletionChoicesProvider:
    """Build completion choices given variables, usage, and context.

    This class provides completion choices for different completion modes
    by combining builtin variables, user-defined variables, and plugin
    variables with usage-based sorting.

    Parameters
    ----------
    get_plugin_variable_names : Callable[[], set[str]]
        Function that returns a set of plugin variable names.

    Attributes
    ----------
    _get_plugin_variable_names : Callable[[], set[str]]
        Function that returns a set of plugin variable names.
    """

    def __init__(self, get_plugin_variable_names: Callable[[], set[str]]):
        """Initialize the completion choices provider.

        Parameters
        ----------
        get_plugin_variable_names : Callable[[], set[str]]
            Function that returns a set of plugin variable names.
        """
        self._get_plugin_variable_names = get_plugin_variable_names

    def build_choices(
        self,
        mode: CompletionMode,
        user_defined_variables: set[str],
        builtin_variables: Iterable[str],
        usage_counts: dict[str, int],
    ) -> Iterator[str]:
        """Build completion choices given variables, usage, and context.

        Parameters
        ----------
        mode : CompletionMode
            The completion mode that determines what type of choices to return.
        user_defined_variables : set[str]
            Set of user-defined variable names.
        builtin_variables : Iterable[str]
            Iterable of builtin variable names.
        usage_counts : dict[str, int]
            Dictionary mapping variable names to their usage counts.

        Yields
        ------
        str
            Completion choice strings, formatted according to the mode.

        Notes
        -----
        The method sorts variables by usage count (descending) and then
        alphabetically. Different completion modes return different formats:
        - DEFAULT/FUNCTION_NAME: Returns function names with $ prefix
        - TAG_NAME_ARG: Returns variable names without formatting
        - DEFAULT/VARIABLE: Returns variable names with % prefix and suffix
        """
        plugin_variables = self._get_plugin_variable_names()
        builtin_variables = set(builtin_variables)
        user_variables = set(
            v for v in user_defined_variables if v not in builtin_variables and v not in plugin_variables
        )
        all_variables = list(builtin_variables | user_variables | plugin_variables)
        all_variables.sort(key=lambda x: (-usage_counts.get(x, 0), x))

        if mode in (CompletionMode.DEFAULT, CompletionMode.FUNCTION_NAME):
            for name in sorted(script_function_names()):
                yield f'${name}'

        if mode == CompletionMode.TAG_NAME_ARG:
            for name in all_variables:
                yield name
            return

        if mode in (CompletionMode.DEFAULT, CompletionMode.VARIABLE):
            for name in all_variables:
                yield f'%{name}%'

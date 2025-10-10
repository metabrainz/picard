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


from picard.plugin import ExtensionPoint
from picard.script.variable_pattern import VARIABLE_NAME_FULLMATCH_RE


ext_point_script_variables = ExtensionPoint(label='script_variables')


def _is_valid_plugin_variable_name(name: str | None) -> bool:
    """Check if a name is a valid plugin variable name."""
    if not isinstance(name, str):
        return False
    if not name:
        return False
    return bool(VARIABLE_NAME_FULLMATCH_RE.match(name))


def register_script_variable(name: str, documentation: str | None = None) -> None:
    """Register a variable that plugins can provide for script completion.

    Parameters
    ----------
    name : str
        The variable name (without % symbols)
    documentation : str, optional
        Optional documentation for the variable

    Examples
    --------
    >>> register_script_variable("my_plugin_var", "A custom variable from my plugin")
    """
    import inspect

    if not _is_valid_plugin_variable_name(name):
        msg = "Invalid script variable name; use letters, digits, underscores."
        raise ValueError(msg)

    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        module_name = frame.f_back.f_globals['__name__']
    else:
        module_name = 'unknown'
    ext_point_script_variables.register(module_name, (name, documentation))


def get_plugin_variable_names():
    """Get all plugin-provided variable names.

    Returns
    -------
    set[str]
        Set of variable names provided by plugins
    """
    return {name for name, __unused in ext_point_script_variables}


def get_plugin_variable_documentation(name):
    """Get documentation for a plugin-provided variable.

    Parameters
    ----------
    name : str
        The variable name

    Returns
    -------
    str or None
        Documentation string if available, None otherwise
    """
    for var_name, documentation in ext_point_script_variables:
        if var_name == name:
            return documentation
    return None

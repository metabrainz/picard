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


ext_point_script_variables = ExtensionPoint(label='script_variables')


def register_script_variable(name, documentation=None):
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

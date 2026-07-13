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

from dataclasses import dataclass

from picard.i18n import _
from picard.plugin import ExtensionPoint
from picard.script.variable_pattern import VARIABLE_NAME_FULLMATCH_RE
from picard.tags import script_variable_tag_names


ext_point_script_variables = ExtensionPoint(label='script_variables')


@dataclass(frozen=True)
class PluginVariable:
    name: str
    documentation: str
    plugin_name: str
    title: str | None = None


def _check_if_duplicate_variable_name(name: str) -> str | None:
    sources = []
    if name in set(script_variable_tag_names()):
        sources.append("System Variables")

    for var in ext_point_script_variables:
        if name == var.name:
            sources.append(f'"{var.plugin_name}"')

    return ', '.join(sources) if sources else None


def _is_valid_plugin_variable_name(name: str | None) -> bool:
    """Check if a name is a valid plugin variable name."""
    if not isinstance(name, str):
        return False
    if not name:
        return False
    return bool(VARIABLE_NAME_FULLMATCH_RE.match(name))


def register_script_variable(name: str, documentation: str | None = None, api=None, title: str | None = None) -> None:
    """Register a variable that plugins can provide for script completion.

    Parameters
    ----------
    name : str
        The variable name (without % symbols)
    documentation : str, optional
        Optional documentation for the variable
    title : str, optional
        Display title for the metadata box (e.g., "Pinned Tags").
        If provided, the tag will show this title instead of the raw name.

    Examples
    --------
    >>> register_script_variable("my_plugin_var", "A custom variable from my plugin", title="My Variable")
    """
    if not _is_valid_plugin_variable_name(name):
        msg = "Invalid script variable name; use letters, digits, underscores."
        raise ValueError(msg)

    duplicate = _check_if_duplicate_variable_name(name)
    if api and duplicate:
        api.logger.warning("Tag '%s' also found in %s.", name, duplicate)

    if api and api._plugin_module:
        module_name = api._plugin_module.__name__
    else:
        module_name = 'unknown'

    plugin_name = api.manifest.name_i18n() if api else _("Unknown Plugin")
    plugin_documentation = documentation or ""
    if plugin_documentation and plugin_name:
        plugin_documentation += "\n\n"
    if plugin_name:
        plugin_documentation += _("Plugin: %s") % plugin_name

    ext_point_script_variables.register(
        module_name,
        PluginVariable(
            name=name,
            documentation=plugin_documentation,
            plugin_name=plugin_name,
            title=title,
        ),
    )


def get_plugin_variable_names() -> set[str]:
    """Get all plugin-provided variable names.

    Returns
    -------
    set[str]
        Set of variable names provided by plugins
    """
    return {var.name for var in ext_point_script_variables}


def get_plugin_variable_documentation(name: str) -> str | None:
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
    for var in ext_point_script_variables:
        if var.name == name:
            return var.documentation
    return None


def get_plugin_variable_title(name: str) -> str | None:
    """Get display title for a plugin-provided variable.

    Parameters
    ----------
    name : str
        The variable name

    Returns
    -------
    str or None
        Display title if available, None otherwise
    """
    for var in ext_point_script_variables:
        if var.name == name:
            return var.title
    return None

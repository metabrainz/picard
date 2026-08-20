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

from typing import TYPE_CHECKING

from picard.const.tags import ALL_TAGS
from picard.plugin import ExtensionPoint
from picard.script.variable_pattern import VARIABLE_NAME_FULLMATCH_RE
from picard.tags.tagvar import TagVar


if TYPE_CHECKING:
    from picard.plugin3.api_impl import PluginApi


ext_point_script_variables = ExtensionPoint[TagVar](label='script_variables')


def _check_if_duplicate_variable_name(name: str) -> str | None:
    sources = []
    # Check against built-in system variables only (not plugin-registered ones)
    builtin_names = {tagvar.script_name() for tagvar in ALL_TAGS if tagvar.is_script_variable}
    if name in builtin_names:
        sources.append("System Variables")

    for var in ext_point_script_variables:
        if name == var.name:
            if var.plugin_id:
                sources.append(f'"{var.plugin_id}"')
            else:
                sources.append('"Unknown"')

    return ', '.join(sources) if sources else None


def _is_valid_plugin_variable_name(name: str | None) -> bool:
    """Check if a name is a valid plugin variable name."""
    if not isinstance(name, str):
        return False
    if not name:
        return False
    return bool(VARIABLE_NAME_FULLMATCH_RE.match(name))


def register_script_variable(
    name: str,
    documentation: str | None = None,
    api: 'PluginApi | None' = None,
    title: str | None = None,
    is_multi_value: bool = False,
) -> None:
    """Register a variable that plugins can provide for script completion.

    If the same variable name has already been registered by the same plugin,
    the existing entry is replaced (no duplicate is created).

    Parameters
    ----------
    name : str
        The variable name as it appears between percent signs in scripts.
        Names starting with ``_`` are treated as hidden variables (they won't
        appear in tag dropdowns but are available in scripts).
    documentation : str, optional
        Optional documentation for the variable
    api : PluginApi, optional
        The plugin API instance
    title : str, optional
        Display title for the metadata box (e.g., "Caller").
        If provided, the tag will show this title instead of the raw name.
    is_multi_value : bool, optional
        Whether this variable can hold multiple values. Default: False.

    Examples
    --------
    >>> register_script_variable("my_plugin_var", "A custom variable from my plugin", title="My Variable")
    >>> register_script_variable("_my_hidden_var", "A hidden variable only for scripts")
    """
    # Determine hidden status from name prefix: names starting with _ are hidden.
    is_hidden = False
    if name.startswith('_'):
        name = name[1:]
        is_hidden = True

    if not _is_valid_plugin_variable_name(name):
        msg = "Invalid script variable name; use letters, digits, underscores."
        raise ValueError(msg)

    duplicate = _check_if_duplicate_variable_name(name)
    if api and duplicate:
        api.logger.warning("Tag '%s' also found in %s.", name, duplicate)

    if api:
        module_name = api.module_path
        plugin_id = api.plugin_id
        plugin_name = api.manifest.name_i18n()
    else:
        module_name = 'unknown'
        plugin_id = None
        plugin_name = None

    # Reject registering the same base name with a different is_hidden status.
    # A plugin cannot register both 'foo' and '_foo' — the base name must be unique.
    for var in ext_point_script_variables:
        if var.name == name and var.is_hidden != is_hidden:
            prefix = '_' if is_hidden else ''
            existing_prefix = '_' if var.is_hidden else ''
            msg = (
                f"Cannot register '{prefix}{name}': "
                f"'{existing_prefix}{name}' is already registered "
                f"with different hidden status."
            )
            raise ValueError(msg)

    # Remove any existing entry with the same name from this plugin to avoid duplicates
    ext_point_script_variables.unregister(module_name, lambda item: item.name == name)
    ext_point_script_variables.register(
        module_name,
        TagVar(
            name=name,
            shortdesc=title,
            longdesc=documentation,
            is_hidden=is_hidden,
            is_multi_value=is_multi_value,
            # Locked attributes for plugin-registered variables
            is_preserved=False,
            is_script_variable=True,
            is_tag=not is_hidden,
            is_calculated=False,
            is_file_info=False,
            is_from_mb=False,
            is_populated_by_picard=False,
            plugin_id=plugin_id,
            plugin_name=plugin_name,
        ),
    )


def unregister_script_variable(name: str, api: 'PluginApi') -> None:
    """Unregister a single script variable previously registered by this plugin.

    Parameters
    ----------
    name : str
        The variable name to unregister
    api : PluginApi
        The plugin API instance (identifies which plugin's registration to remove)
    """
    ext_point_script_variables.unregister(api.module_path, lambda item: item.name == name)


def unregister_all_script_variables(api: 'PluginApi') -> None:
    """Unregister all script variables registered by this plugin.

    Parameters
    ----------
    api : PluginApi
        The plugin API instance (identifies which plugin's registrations to remove)
    """
    ext_point_script_variables.unregister(api.module_path, lambda item: True)


def get_plugin_variable_title(name: str) -> str | None:
    """Get display title for a plugin-provided variable.

    Parameters
    ----------
    name : str
        The variable name (bare name without prefix)

    Returns
    -------
    str or None
        Display title if available, None otherwise
    """
    for var in ext_point_script_variables:
        if var.script_name() == name:
            return var._shortdesc
    return None

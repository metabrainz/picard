# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Bob Swift
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2025 The MusicBrainz Team
# Copyright (C) 2025-2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from typing import (
    TYPE_CHECKING,
    NamedTuple,
)

from picard.const.tags import ALL_TAGS
from picard.plugin import ExtensionPoint
from picard.script.variable_pattern import VARIABLE_NAME_FULLMATCH_RE
from picard.tags.tagvar import TagVar


if TYPE_CHECKING:
    from picard.plugin3.api_impl import PluginApi


ext_point_script_variables = ExtensionPoint[TagVar](label='script_variables')


class VariableIdentity(NamedTuple):
    bare_name: str
    hidden: bool


def variable_identity(name: str) -> VariableIdentity:
    """Resolve a variable name spelling into its identity.

    A variable's identity is its **bare name**. A leading ``_`` is an input
    spelling that marks the variable as hidden; a given bare name is therefore
    either hidden or visible, not both. Identity comparisons must use the bare
    name, never the prefixed/script form.
    """
    if name.startswith('_'):
        return VariableIdentity(name[1:], True)
    return VariableIdentity(name, False)


def _check_if_duplicate_variable_name(name: str) -> str | None:
    sources = []
    # Check against built-in system variables only (not plugin-registered ones)
    # Compare on the bare name so hidden status does not affect identity.
    builtin_names = {tagvar.name for tagvar in ALL_TAGS if tagvar.is_script_variable}
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
    is_from_mb: bool = False,
) -> None:
    """Register a variable that plugins can provide for script completion.

    See :func:`variable_identity` for how the ``_`` hidden-variable
    prefix is interpreted. Re-registering the same bare name replaces the
    existing entry when the hidden status matches; registering it with a
    *different* hidden status raises :class:`ValueError`.

    Parameters
    ----------
    name : str
        The variable name as it appears between percent signs in scripts.
        A leading ``_`` marks the variable as hidden: it still appears in
        script autocomplete and the scripting documentation, but not in the
        tag dropdowns and tag list editor.
    documentation : str, optional
        Optional documentation for the variable
    api : PluginApi, optional
        The plugin API instance
    title : str, optional
        Display title for the metadata box (e.g., "Caller").
        If provided, the tag will show this title instead of the raw name.
    is_multi_value : bool, optional
        Whether this variable can hold multiple values. Default: False.
    is_from_mb : bool, optional
        Whether the tag information is provided from the MusicBrainz database. Default: False.

    Examples
    --------
    >>> register_script_variable("my_plugin_var", "A custom variable from my plugin", title="My Variable")
    >>> register_script_variable("_my_hidden_var", "A hidden variable only for scripts")
    """
    identity = variable_identity(name)

    if not _is_valid_plugin_variable_name(identity.bare_name):
        msg = "Invalid script variable name; use letters, digits, underscores."
        raise ValueError(msg)

    duplicate = _check_if_duplicate_variable_name(identity.bare_name)
    if api and duplicate:
        api.logger.warning("Tag '%s' also found in %s.", identity.bare_name, duplicate)

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
        if var.name == identity.bare_name and var.is_hidden != identity.hidden:
            prefix = '_' if identity.hidden else ''
            existing_prefix = '_' if var.is_hidden else ''
            msg = (
                f"Cannot register '{prefix}{identity.bare_name}': "
                f"'{existing_prefix}{identity.bare_name}' is already registered "
                f"with different hidden status."
            )
            raise ValueError(msg)

    # Remove any existing entry with the same name from this plugin to avoid duplicates
    ext_point_script_variables.unregister(module_name, lambda item: item.name == identity.bare_name)
    ext_point_script_variables.register(
        module_name,
        TagVar(
            name=identity.bare_name,
            shortdesc=title,
            longdesc=documentation,
            is_hidden=identity.hidden,
            is_multi_value=is_multi_value,
            is_from_mb=is_from_mb,
            # Locked attributes for plugin-registered variables
            is_preserved=False,
            is_script_variable=True,
            is_tag=not identity.hidden,
            is_calculated=False,
            is_file_info=False,
            is_populated_by_picard=False,
            plugin_id=plugin_id,
            plugin_name=plugin_name,
        ),
    )


def unregister_script_variable(name: str, api: 'PluginApi') -> None:
    """Unregister a single script variable previously registered by this plugin.

    The spelling must match the variable's hidden status: a bare name removes a
    visible variable, a ``_``-prefixed name removes a hidden one. A mismatch
    raises :class:`ValueError`; an unknown name is a no-op. See
    :func:`variable_identity`.

    Parameters
    ----------
    name : str
        The variable name to unregister. Prefix with ``_`` if (and only if)
        the variable is hidden.
    api : PluginApi
        The plugin API instance (identifies which plugin's registration to remove)
    """
    identity = variable_identity(name)

    for item in ext_point_script_variables:
        if item.name == identity.bare_name and item.is_hidden != identity.hidden:
            registered = ('_' if item.is_hidden else '') + identity.bare_name
            msg = f"Cannot unregister '{name}': the registered variable is '{registered}'."
            raise ValueError(msg)

    ext_point_script_variables.unregister(
        api.module_path,
        lambda item: item.name == identity.bare_name and item.is_hidden == identity.hidden,
    )


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
        The variable name, with or without a leading ``_`` prefix

    Returns
    -------
    str or None
        Display title if available, None otherwise
    """
    identity = variable_identity(name)
    for var in ext_point_script_variables:
        if var.name == identity.bare_name:
            return var._shortdesc
    return None

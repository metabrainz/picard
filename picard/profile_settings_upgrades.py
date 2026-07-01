# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
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

"""Settings upgrade registry for profile import.

When importing a profile exported from an older Picard version, the settings
may use old option names or value formats. This module provides a registry of
version-keyed transforms that can be applied to a settings dict to bring it
up to date with the current version.

The transforms use _rename_option_in_settings and _upgrade_option_value_in_settings
from picard.config_upgrade, which operate on plain dicts without requiring the
full Config machinery.

Usage:
    Register new upgrades with the @_register decorator when an in_profile
    option is renamed or its value format changes. Only upgrades for versions
    *after* the profile export feature was introduced are needed — nobody will
    have exports from older versions.
"""

from picard.config_upgrade import (  # noqa: F401 - used by upgrade hooks
    _rename_option_in_settings,
    _upgrade_option_value_in_settings,
)
from picard.version import Version


# Registry of settings upgrades, keyed by the version that introduced the change.
# Each entry is a callable that takes a settings dict and modifies it in place.
# Only includes changes to in_profile=True options.
#
# When importing a profile with picard_version < current, all transforms with
# version > picard_version are applied in order.

_SETTINGS_UPGRADES: list[tuple[Version, callable]] = []


def _register(version_str: str):
    """Decorator to register a settings upgrade function.

    Example:
        @_register('3.1.0')
        def _upgrade_3_1_0(settings: dict) -> None:
            '''Rename foo_bar to baz_qux.'''
            _rename_option_in_settings(settings, 'foo_bar', 'baz_qux')
    """

    def decorator(func):
        version = Version.from_string(version_str)
        _SETTINGS_UPGRADES.append((version, func))
        # Keep sorted after each registration
        _SETTINGS_UPGRADES.sort(key=lambda x: x[0])
        return func

    return decorator


# Register upgrades below as needed. Example:
#
# @_register('3.1.0')
# def _upgrade_3_1_0(settings: dict) -> None:
#     """Rename old_option to new_option."""
#     _rename_option_in_settings(settings, 'old_option', 'new_option')


def upgrade_settings_for_import(settings: dict, from_version_str: str) -> list[str]:
    """Apply all settings upgrades applicable between from_version and current.

    Args:
        settings: The settings dict to upgrade in place.
        from_version_str: The picard_version from the exported profile.

    Returns:
        List of descriptions of upgrades that were applied.
    """
    from picard.version import VersionError

    try:
        from_version = Version.from_string(from_version_str)
    except VersionError:
        return []

    applied = []
    for version, upgrade_func in _SETTINGS_UPGRADES:
        if version > from_version:
            upgrade_func(settings)
            if upgrade_func.__doc__:
                applied.append(upgrade_func.__doc__.strip())

    return applied

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014 Michael Wiencek
# Copyright (C) 2013-2016, 2018-2026 Laurent Monin
# Copyright (C) 2014, 2017 Lukáš Lalinský
# Copyright (C) 2014, 2018-2026 Philipp Wolfer
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Suhas
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021, 2023 Bob Swift
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

from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
from typing import (
    Any,
    NamedTuple,
)

from picard import log
from picard.config import (
    Config,
    ConfigValueType,
    Option,
    SettingConfigSection,
)
from picard.version import (
    Version,
    VersionError,
)


# Type alias for the polymorphic settings parameter accepted by upgrade functions.
# Either a plain dict (profile overrides, imported settings) or a SettingConfigSection
# (base config at startup).
Settings = dict | SettingConfigSection


# TO ADD AN UPGRADE HOOK:
# See config_upgrade_hooks.py


# ---------------------------------------------------------------------------
# New-style decorator-based upgrade system
# ---------------------------------------------------------------------------
# Two decorators:
#   @upgrade_settings(version_str) — settings transforms (dict or SettingConfigSection)
#   @upgrade_config(version_str) — full config operations (startup only)
#
# Both register into a single list (_UPGRADES_REGISTRY) in declaration order.
# See docs/UnifiedConfigUpgrades.md for design rationale.
# ---------------------------------------------------------------------------


class _UpgradeType(Enum):
    """Type tag for upgrade registry entries."""

    SETTINGS = 'settings'
    CONFIG = 'config'


class _UpgradeEntry(NamedTuple):
    """A single entry in the upgrades registry."""

    version: Version
    upgrade_type: _UpgradeType
    func: Callable


# Single registry populated by both decorators. Entries are stored in
# declaration order.
_UPGRADES_REGISTRY: list[_UpgradeEntry] = []


def upgrade_settings(version_str: str):
    """Decorator to register a settings upgrade function.

    The decorated function receives a single argument: either a plain dict
    (profile override, imported settings) or a SettingConfigSection (base config).
    Use the polymorphic helpers (rename_option_in_settings,
    upgrade_option_value_in_settings) which handle both cases.

    Multiple functions can share the same version — they execute in
    definition order.

    Example:
        @upgrade_settings('3.0.0dev3')
        def rename_toolbar_multiselect(settings):
            '''Option "toolbar_multiselect" was renamed to "allow_multi_dirs_selection".'''
            rename_option_in_settings(settings, 'toolbar_multiselect',
                                      'allow_multi_dirs_selection', BoolOption, False)
    """

    def decorator(func):
        version = Version.from_string(version_str)
        _UPGRADES_REGISTRY.append(_UpgradeEntry(version, _UpgradeType.SETTINGS, func))
        return func

    return decorator


def upgrade_config(version_str: str):
    """Decorator to register a config upgrade function (non-settings operations).

    The decorated function receives the full Config object. Use this for
    operations that need persist, allKeys(), interactive dialogs, or other
    non-settings Config access.

    WARNING: These functions do NOT run on profile override dicts or imported
    profile data. If you need to transform a settings key, use
    @upgrade_settings instead.

    Example:
        @upgrade_config('3.0.0dev1')
        def clear_qt5_state(config):
            '''Clear Qt5 state config.'''
            for key in config.allKeys():
                if key.startswith('persist/'):
                    config.remove(key)
    """

    def decorator(func):
        version = Version.from_string(version_str)
        _UPGRADES_REGISTRY.append(_UpgradeEntry(version, _UpgradeType.CONFIG, func))
        return func

    return decorator


def _get_sorted_upgrades(
    registry: list[_UpgradeEntry],
) -> list[_UpgradeEntry]:
    """Return upgrades sorted by version, preserving declaration order within same version."""
    return sorted(registry, key=lambda x: x.version)


# ---------------------------------------------------------------------------
# Polymorphic helpers — work on both plain dicts and ConfigSection objects
# ---------------------------------------------------------------------------


def rename_option_in_settings(
    settings: Settings,
    old_name: str,
    new_name: str,
    option_type: type[Option] | None = None,
    default: ConfigValueType | None = None,
    reverse: bool = False,
) -> None:
    """Rename an option key in settings.

    Polymorphic: works on both plain dicts (profile overrides, imported
    settings) and ConfigSection objects (base config at startup).

    Args:
        settings: A plain dict or a ConfigSection instance.
        old_name: The old option key name.
        new_name: The new option key name.
        option_type: Option class (e.g., BoolOption). Required for ConfigSection,
                     ignored for plain dicts.
        default: Default value for the option. Required for ConfigSection,
                 ignored for plain dicts.
        reverse: If True, invert the boolean value during rename.
    """
    if isinstance(settings, dict):
        # Plain dict path (profile overrides, imported data)
        if old_name in settings:
            value = settings[old_name]
            if reverse and value is not None:
                value = not value
            settings[new_name] = value
            del settings[old_name]
    else:
        # ConfigSection path (base config at startup)
        assert option_type is not None
        assert default is not None
        if old_name in settings:
            with temp_option(option_type, settings.section_name, old_name, default) as opt:
                settings[new_name] = settings.value(opt, default)
            if reverse:
                settings[new_name] = not settings[new_name]
            settings.remove(old_name)


def upgrade_option_value_in_settings(
    settings: Settings,
    name: str,
    transform: Callable,
) -> None:
    """Apply a value transform to an option in settings.

    Polymorphic: works on both plain dicts (profile overrides, imported
    settings) and ConfigSection objects (base config at startup).

    The transform function receives the current value and must return the
    new value. Settings with None value (tracked but not overridden in
    profile dicts) are left unchanged.

    Args:
        settings: A plain dict or a ConfigSection instance.
        name: The option key name.
        transform: Function that takes the current value and returns the new value.
    """
    if isinstance(settings, dict):
        # Plain dict path
        if name in settings and settings[name] is not None:
            settings[name] = transform(settings[name])
    else:
        # ConfigSection path
        if name in settings:
            value = settings.raw_value(name)
            if value is not None:
                with settings.no_profile():
                    settings[name] = transform(value)


def get_option(
    settings: Settings,
    name: str,
    option_type: type[Option] | None = None,
    default: ConfigValueType | None = None,
) -> Any:
    """Read an option value from settings without removing it.

    Polymorphic: works on both plain dicts and ConfigSection objects.

    For plain dicts, the value is already a Python object (bool, int, str, etc.)
    and is returned directly.

    For ConfigSection, the option_type is needed to deserialize the raw value
    from QSettings (via a temporarily registered Option).

    Args:
        settings: A plain dict or a ConfigSection instance.
        name: The option key name to read.
        option_type: Option class (e.g., BoolOption). Required for ConfigSection,
                     ignored for plain dicts.
        default: Default value if the key is missing. Required for ConfigSection,
                 ignored for plain dicts (returns None if missing and no default).

    Returns:
        The option value (deserialized), or default if the key is not present.
    """
    if isinstance(settings, dict):
        return settings.get(name, default)
    else:
        assert option_type is not None
        assert default is not None
        if name not in settings:
            return default
        with temp_option(option_type, settings.section_name, name, default) as opt:
            return settings.value(opt, default)


def remove_option(
    settings: Settings,
    name: str,
) -> None:
    """Remove an option key from settings.

    Polymorphic: works on both plain dicts and ConfigSection objects.
    No-op if the key is not present.

    Args:
        settings: A plain dict or a ConfigSection instance.
        name: The option key name to remove.
    """
    if isinstance(settings, dict):
        settings.pop(name, None)
    else:
        settings.remove(name)


def write_option(
    settings: Settings,
    name: str,
    value: Any,
) -> None:
    """Write an option value to settings.

    Polymorphic: works on both plain dicts and ConfigSection objects.
    Handles Enum serialization: for plain dicts, enums are stored as their
    .value (matching how profile overrides persist enum options). For
    ConfigSection, enums are passed directly (ConfigSection.__setitem__
    handles serialization).

    Args:
        settings: A plain dict or a ConfigSection instance.
        name: The option key name.
        value: The value to write. Enums are auto-serialized for dicts.
    """
    if isinstance(settings, dict):
        settings[name] = value.value if isinstance(value, Enum) else value
    else:
        settings[name] = value


@contextmanager
def temp_option(option_type: type[Option], section: str, name: str, default: ConfigValueType):
    opt = option_type(section, name, default)
    yield opt
    opt.unregister()


def rename_option(
    config: Config,
    old_opt: str,
    new_opt: str,
    option_type: type[Option],
    default: ConfigValueType,
    reverse: bool = False,
):
    _s = config.setting
    if old_opt in _s:
        rename_option_in_settings(_s, old_opt, new_opt, option_type, default, reverse)

        _p = config.profiles
        _s.init_profile_options()
        all_settings = _p['user_profile_settings']
        for profile in _p['user_profiles']:
            id = profile['id']
            if id in all_settings:
                rename_option_in_settings(all_settings[id], old_opt, new_opt, reverse=reverse)
        _p['user_profile_settings'] = all_settings


def upgrade_option_value(
    config: Config,
    name: str,
    transform: Callable,
) -> None:
    """Apply a value transform to an option in base config and all profile overrides.

    Use this in upgrade hooks when an option's value format changes but the key
    stays the same. The transform function receives the current raw value and
    must return the new value. Reads bypass profile overrides and Option.convert()
    to access the actual stored value.
    """
    _s = config.setting
    upgrade_option_value_in_settings(_s, name, transform)

    _p = config.profiles
    _s.init_profile_options()
    all_settings = _p['user_profile_settings']
    for profile in _p['user_profiles']:
        id = profile['id']
        if id in all_settings:
            upgrade_option_value_in_settings(all_settings[id], name, transform)
    _p['user_profile_settings'] = all_settings


def run_config_upgrades(config: Config) -> None:
    """Execute all registered upgrade hooks."""
    # Ensure hooks module is imported so decorators have populated the registry
    import picard.config_upgrade_hooks  # noqa: F401

    sorted_upgrades = _get_sorted_upgrades(_UPGRADES_REGISTRY)

    # Build a version-ordered execution plan for Config.run_upgrade_hooks()
    all_versions = sorted({e.version for e in sorted_upgrades})

    hooks: dict[Version, Callable[[Config], None]] = {}
    for version in all_versions:
        version_entries = [e for e in sorted_upgrades if e.version == version]

        def make_hook(entries):
            def hook(config):
                for entry in entries:
                    if entry.upgrade_type == _UpgradeType.SETTINGS:
                        _run_settings_upgrade_on_config(config, entry.func)
                    else:
                        if entry.func.__doc__:
                            log.debug("Config upgrade: %s", entry.func.__doc__.strip())
                        entry.func(config)

            docs = [entry.func.__doc__.strip() for entry in entries if entry.func.__doc__]
            hook.__doc__ = '; '.join(docs) if docs else None
            hook.__name__ = f'upgrade_{version}'
            return hook

        hooks[version] = make_hook(version_entries)

    config.run_upgrade_hooks(hooks)


def _run_settings_upgrade_on_config(
    config: Config,
    func: Callable,
) -> None:
    """Run a single @upgrade_settings function on base config and all profile overrides."""
    _s = config.setting

    # Apply to base config (SettingConfigSection path)
    if func.__doc__:
        log.debug("Settings upgrade: %s", func.__doc__.strip())
    func(_s)

    # Apply to all profile override dicts (plain dict path)
    _s.init_profile_options()
    _p = config.profiles
    all_settings = _p['user_profile_settings']
    modified = False
    for profile in _p['user_profiles']:
        profile_id = profile['id']
        if profile_id in all_settings:
            func(all_settings[profile_id])
            modified = True
    if modified:
        _p['user_profile_settings'] = all_settings


def get_upgrades(
    from_version_str: str,
    upgrade_types: set[_UpgradeType] | None = None,
) -> list[_UpgradeEntry]:
    """Return registered upgrades matching the given types and version range.

    Args:
        from_version_str: Only return upgrades with version > this version.
        upgrade_types: Set of _UpgradeType to include. None means all types.

    Returns:
        List of _UpgradeEntry sorted by version (declaration order preserved
        within same version).
    """
    # Ensure hooks module is imported so decorators have populated the registry
    import picard.config_upgrade_hooks  # noqa: F401

    try:
        from_version = Version.from_string(from_version_str)
    except VersionError:
        return []

    sorted_upgrades = _get_sorted_upgrades(_UPGRADES_REGISTRY)
    return [
        e
        for e in sorted_upgrades
        if e.version > from_version and (upgrade_types is None or e.upgrade_type in upgrade_types)
    ]


def get_applicable_settings_upgrades(from_version_str: str) -> list[_UpgradeEntry]:
    """Return settings upgrades applicable for a given source version.

    Used by profile import to upgrade settings from an older Picard version.
    """
    return get_upgrades(from_version_str, {_UpgradeType.SETTINGS})


def apply_settings_upgrades_for_import(settings: dict, from_version_str: str) -> list[str]:
    """Apply all settings upgrades applicable between from_version and current.

    Used by profile import. Modifies the settings dict in place.

    Args:
        settings: The settings dict to upgrade in place.
        from_version_str: The picard_version from the exported profile.

    Returns:
        List of descriptions of upgrades that were applied.
    """
    applicable = get_applicable_settings_upgrades(from_version_str)
    applied = []
    for entry in applicable:
        entry.func(settings)
        if entry.func.__doc__:
            applied.append(entry.func.__doc__.strip())
    return applied

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

TODO: This module duplicates knowledge from picard.config_upgrade_hooks (which
renames/transforms are needed per version). A future refactoring could unify
both systems — e.g., by having config_upgrade_hooks use a decorator-based
registry that also captures the settings-level transforms, eliminating the
need to maintain this parallel registry. See also autodetect_upgrade_hooks()
in picard.config_upgrade which uses a naming convention for hook discovery.
"""

import re

from picard.config_upgrade import (
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
    """Decorator to register a settings upgrade function."""

    def decorator(func):
        version = Version.from_string(version_str)
        _SETTINGS_UPGRADES.append((version, func))
        return func

    return decorator


@_register('1.3.0dev1')
def _upgrade_1_3_0dev1(settings: dict) -> None:
    """Rename windows_compatible_filenames to windows_compatibility."""
    _rename_option_in_settings(settings, 'windows_compatible_filenames', 'windows_compatibility')


@_register('1.4.0dev7')
def _upgrade_1_4_0dev7(settings: dict) -> None:
    """Rename save_only_front_images_to_tags to embed_only_one_front_image."""
    _rename_option_in_settings(settings, 'save_only_front_images_to_tags', 'embed_only_one_front_image')


@_register('2.1.0dev1')
def _upgrade_2_1_0dev1(settings: dict) -> None:
    """Rename genre-related options."""
    _rename_option_in_settings(settings, 'max_tags', 'max_genres')
    _rename_option_in_settings(settings, 'min_tag_usage', 'min_genre_usage')
    _rename_option_in_settings(settings, 'only_my_tags', 'only_my_genres')
    _rename_option_in_settings(settings, 'artists_tags', 'artists_genres')


@_register('2.5.0dev1')
def _upgrade_2_5_0dev1(settings: dict) -> None:
    """Rename Whitelist to UrlRelationships in ca_providers."""
    _upgrade_option_value_in_settings(
        settings,
        'ca_providers',
        lambda providers: [('UrlRelationships' if n == 'Whitelist' else n, s) for n, s in providers],
    )


@_register('2.6.0beta2')
def _upgrade_2_6_0beta2(settings: dict) -> None:
    """Rename cover art options."""
    _rename_option_in_settings(settings, 'caa_image_type_as_filename', 'image_type_as_filename')
    _rename_option_in_settings(settings, 'caa_save_single_front_image', 'save_only_one_front_image')


@_register('3.0.0dev3')
def _upgrade_3_0_0dev3(settings: dict) -> None:
    """Rename toolbar_multiselect to allow_multi_dirs_selection."""
    _rename_option_in_settings(settings, 'toolbar_multiselect', 'allow_multi_dirs_selection')


@_register('3.0.0dev8')
def _upgrade_3_0_0dev8(settings: dict) -> None:
    """Rename dont_write_tags to enable_tag_saving (reversed boolean)."""
    _rename_option_in_settings(settings, 'dont_write_tags', 'enable_tag_saving', reverse=True)


@_register('3.0.0dev10')
def _upgrade_3_0_0dev10(settings: dict) -> None:
    """Lowercase cover art format options."""
    for key in ('cover_tags_convert_to_format', 'cover_file_convert_to_format'):
        _upgrade_option_value_in_settings(
            settings,
            key,
            lambda value: value.lower() if isinstance(value, str) else value,
        )


@_register('3.0.0a2')
def _upgrade_3_0_0a2(settings: dict) -> None:
    """Fix $matchedtracks() usage in tagger scripts."""
    matched_tracks_regex = re.compile(r'\$matchedtracks\([^)$]+\)')

    def fix_tagger_scripts(scripts):
        return [
            (pos, name, enabled, matched_tracks_regex.sub('$matchedtracks()', script))
            for pos, name, enabled, script in scripts
        ]

    _upgrade_option_value_in_settings(settings, 'list_of_scripts', fix_tagger_scripts)


@_register('3.0.0b2')
def _upgrade_3_0_0b2(settings: dict) -> None:
    """Rename artist_locales to translation_locales."""
    _rename_option_in_settings(settings, 'artist_locales', 'translation_locales')


@_register('3.0.0b5')
def _upgrade_3_0_0b5(settings: dict) -> None:
    """Rename selected_file_naming_script_id to active_file_naming_script_id."""
    _rename_option_in_settings(settings, 'selected_file_naming_script_id', 'active_file_naming_script_id')


# Sort the registry by version (should already be in order, but ensure it)
_SETTINGS_UPGRADES.sort(key=lambda x: x[0])


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

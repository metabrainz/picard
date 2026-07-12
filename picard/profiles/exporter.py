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

"""Profile export to TOML format.

Exports a user profile as a self-contained, human-readable TOML file that
can be shared on forums, attached to issues, or used as a personal backup.
"""

from datetime import date
from enum import Enum

from picard import PICARD_VERSION_STR
from picard.config import (
    Config,
    Option,
)
from picard.profile import is_plugin_profile_key
from picard.profiles import PROFILE_FORMAT_VERSION
from picard.script import get_file_naming_script_presets

import tomlkit


# Options that are represented as scripts in the TOML format
# rather than plain settings values.
_SCRIPT_OPTIONS = frozenset(
    {
        'active_file_naming_script_id',
        'list_of_scripts',
        'enable_tagger_scripts',
    }
)


def export_profile(
    config: Config,
    profile_id: str,
    title: str,
    mode: str = 'share',
    description: str = '',
    author: str = '',
) -> str:
    """Export a profile as a TOML string.

    Args:
        config: The application Config object.
        profile_id: UUID of the profile to export.
        title: Profile title for the [profile] section.
        mode: 'share' (excludes non-shareable options) or 'backup' (includes all).
        description: Optional profile description.
        author: Optional profile author.

    Returns:
        A TOML-formatted string representing the exported profile.
    """
    all_settings = config.profiles['user_profile_settings']
    profile_settings = all_settings.get(profile_id, {})

    doc = tomlkit.document()
    doc.add(tomlkit.comment("Picard Profile"))
    doc.add(tomlkit.comment("https://picard.musicbrainz.org/"))
    doc.add(tomlkit.nl())

    # [profile] section
    profile_table = tomlkit.table()
    profile_table.add('title', title)
    if mode == 'backup':
        profile_table.add('id', profile_id)
    if description:
        profile_table.add('description', description)
    if author:
        profile_table.add('author', author)
    profile_table.add('format_version', PROFILE_FORMAT_VERSION)
    profile_table.add('picard_version', PICARD_VERSION_STR)
    profile_table.add('created', date.today().isoformat())
    doc.add('profile', profile_table)

    # Collect settings, filtering by mode and excluding script-related options
    settings_to_export = {}

    for key, value in profile_settings.items():
        # Skip None values (tracked but not overridden)
        if value is None:
            continue

        # Skip script-related options (handled separately)
        if key in _SCRIPT_OPTIONS:
            continue

        # Plugin settings are not yet supported for export.
        # A future version may add opt-in per-plugin export support.
        if is_plugin_profile_key(key):
            continue

        # Look up the Option to check shareable flag
        opt = Option.get('setting', key)
        if opt is None:
            continue

        # In share mode, skip non-shareable options
        if mode == 'share' and not opt.shareable:
            continue

        settings_to_export[key] = _export_value(value)

    # [settings] section
    if settings_to_export:
        doc.add(tomlkit.nl())
        settings_table = tomlkit.table()
        for key, value in sorted(settings_to_export.items()):
            settings_table.add(key, value)
        doc.add('settings', settings_table)

    # [scripts] section
    _export_scripts(doc, config, profile_settings, mode)

    return tomlkit.dumps(doc)


def _export_value(value):
    """Convert an option value to a TOML-compatible type."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        table = tomlkit.inline_table()
        table.update(value)
        return table
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return [_export_value(item) for item in value]
    return value


def _export_scripts(doc, config, profile_settings, mode):
    """Export naming and tagger scripts into the TOML document."""
    scripts_added = False

    # File naming script
    active_script_id = profile_settings.get('active_file_naming_script_id')
    if active_script_id is not None:
        script_data, is_preset = _resolve_naming_script(config, active_script_id)
        if script_data:
            doc.add(tomlkit.nl())
            naming_table = tomlkit.table()
            naming_table.add('id', script_data['id'])
            naming_table.add('title', script_data['title'])
            if is_preset:
                naming_table.add('preset', True)
            # Include all metadata fields if present
            for field in ('author', 'description', 'license', 'version', 'last_updated', 'script_language_version'):
                value = script_data.get(field, '')
                if value:
                    naming_table.add(field, value)
            naming_table.add('script', _multiline_string(script_data['script']))
            # Use dotted key path: [scripts.naming]
            if 'scripts' not in doc:
                scripts_container = tomlkit.table(is_super_table=True)
                doc.add('scripts', scripts_container)
            doc['scripts'].add('naming', naming_table)
            scripts_added = True

    # Tagger scripts
    list_of_scripts = profile_settings.get('list_of_scripts')
    if list_of_scripts is not None:
        tagging_array = tomlkit.aot()
        for _pos, name, enabled, content in list_of_scripts:
            # In share mode, skip disabled scripts
            if mode == 'share' and not enabled:
                continue
            script_table = tomlkit.table()
            script_table.add('title', name)
            if mode == 'backup':
                script_table.add('enabled', enabled)
            script_table.add('script', _multiline_string(content))
            tagging_array.append(script_table)

        if tagging_array:
            if not scripts_added:
                doc.add(tomlkit.nl())
                if 'scripts' not in doc:
                    scripts_container = tomlkit.table(is_super_table=True)
                    doc.add('scripts', scripts_container)
            doc['scripts'].add('tagging', tagging_array)


def _resolve_naming_script(config, script_id: str) -> tuple[dict | None, bool]:
    """Resolve a naming script ID to its content dict.

    Returns:
        A tuple of (script_data, is_preset). script_data is None if not found.
    """
    scripts = config.setting.raw_value('file_renaming_scripts') or {}
    if script_id in scripts:
        return scripts[script_id], False

    # Check presets
    for preset in get_file_naming_script_presets():
        if preset['id'] == script_id:
            return {
                'id': preset['id'],
                'title': str(preset['title']),
                'script': str(preset['script']),
            }, True
    return None, False
    return False


def _multiline_string(text: str) -> tomlkit.items.String:
    """Create a TOML multiline literal string for script content."""
    return tomlkit.string(text, multiline=True, literal=True)

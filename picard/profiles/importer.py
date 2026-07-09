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

"""Profile import from TOML format.

Imports a profile from a TOML string, creating a new profile with the
settings, file naming script, and tagger scripts defined in the file.
"""

import sys
import uuid


if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from picard.config import (
    Config,
    Option,
)
from picard.profiles import PROFILE_FORMAT_VERSION


class ProfileImportError(Exception):
    """Raised when profile import fails due to invalid data."""


class ProfileImportResult:
    """Result of a profile import operation.

    Attributes:
        profile_id: UUID of the created profile.
        title: Title of the imported profile.
        skipped_options: List of option names that were not recognized.
        warnings: List of warning messages for the user.
    """

    def __init__(self, profile_id: str, title: str):
        self.profile_id = profile_id
        self.title = title
        self.skipped_options: list[str] = []
        self.warnings: list[str] = []


def import_profile(
    config: Config,
    toml_string: str,
    enabled: bool = False,
    replace_id: str | None = None,
) -> ProfileImportResult:
    """Import a profile from a TOML string.

    Args:
        config: The application Config object.
        toml_string: The TOML content to import.
        enabled: Whether to create the profile as enabled.
        replace_id: If set, replace the existing profile with this UUID
                    instead of creating a new one.

    Returns:
        ProfileImportResult with details about the import.

    Raises:
        ProfileImportError: If the TOML is invalid or missing required fields.
    """
    try:
        data = tomllib.loads(toml_string)
    except tomllib.TOMLDecodeError as e:
        raise ProfileImportError(f"Invalid TOML: {e}") from e

    # Validate [profile] section
    profile_section = data.get('profile')
    if not profile_section:
        raise ProfileImportError("Missing required [profile] section")

    title = profile_section.get('title')
    if not title:
        raise ProfileImportError("Missing required 'title' in [profile] section")

    # Check format version compatibility
    format_version = profile_section.get('format_version', 1)
    if not isinstance(format_version, int) or format_version > PROFILE_FORMAT_VERSION:
        raise ProfileImportError(
            f"Unsupported profile format version {format_version} "
            f"(this version of Picard supports format version {PROFILE_FORMAT_VERSION}). "
            f"Please upgrade Picard to import this profile."
        )

    # Determine profile ID and whether we're replacing
    if replace_id:
        # Replace an existing profile
        profiles_list = config.profiles['user_profiles']
        existing = [p for p in profiles_list if p['id'] == replace_id]
        if not existing:
            raise ProfileImportError(f"No existing profile with id '{replace_id}' to replace")
        profile_id = replace_id
        unique_title = title
    else:
        # Create a new profile
        profile_id = profile_section.get('id') or str(uuid.uuid4())
        # If the file has a UUID and it already exists, generate a new one
        profiles_list = config.profiles['user_profiles']
        if any(p['id'] == profile_id for p in profiles_list):
            profile_id = str(uuid.uuid4())
        unique_title = _make_unique_title(config, title)

    result = ProfileImportResult(profile_id, unique_title)

    # Build profile settings dict
    profile_settings = {}

    settings_section = data.get('settings', {})

    # Process [settings] section
    for key, value in settings_section.items():
        opt = Option.get('setting', key)
        if opt is None:
            result.skipped_options.append(key)
            continue
        if not opt.in_profile:
            result.skipped_options.append(key)
            continue
        profile_settings[key] = _import_value(value, opt)

    # Process [scripts.naming] section
    scripts_section = data.get('scripts', {})
    naming_section = scripts_section.get('naming')
    if naming_section:
        script_id = _import_naming_script(config, naming_section, result)
        if script_id:
            profile_settings['active_file_naming_script_id'] = script_id

    # Process [[scripts.tagging]] section
    tagging_section = scripts_section.get('tagging', [])
    if tagging_section:
        _import_tagger_scripts(config, profile_settings, tagging_section, result)

    # Register the profile
    _register_profile(config, profile_id, unique_title, enabled, profile_settings, replace=bool(replace_id))

    # Report skipped options
    if result.skipped_options:
        result.warnings.append(
            f"{len(result.skipped_options)} settings were not recognized and were skipped: "
            f"{', '.join(result.skipped_options)}"
        )

    return result


def _make_unique_title(config: Config, title: str) -> str:
    """Ensure the profile title is unique, appending (copy) if needed."""
    existing_titles = {p['title'] for p in config.profiles['user_profiles']}
    if title not in existing_titles:
        return title
    candidate = f"{title} (copy)"
    counter = 2
    while candidate in existing_titles:
        candidate = f"{title} (copy {counter})"
        counter += 1
    return candidate


def _import_value(value, opt: Option):
    """Convert a TOML value back to the internal representation expected by an option."""
    # TOML arrays become lists; if the option default is a list of tuples,
    # convert inner lists to tuples
    if isinstance(value, list) and isinstance(opt.default, (list, tuple)):
        if opt.default and isinstance(opt.default[0] if opt.default else None, tuple):
            return [tuple(item) if isinstance(item, list) else item for item in value]
        return value
    return value


def _import_naming_script(config: Config, naming_section: dict, result: ProfileImportResult) -> str | None:
    """Import a naming script and return its ID."""
    script_content = naming_section.get('script')
    title = naming_section.get('title')
    if not script_content or not title:
        result.warnings.append("Naming script section missing 'script' or 'title' field, skipped.")
        return None

    script_id = naming_section.get('id') or str(uuid.uuid4())
    is_preset = naming_section.get('preset', False)

    # If it's a preset, just reference it by ID (don't register a new script)
    if is_preset:
        return script_id

    # Check for ID collision
    scripts = config.setting.raw_value('file_renaming_scripts') or {}
    if script_id in scripts:
        # Collision: generate a new ID (UI layer can offer more options later)
        script_id = str(uuid.uuid4())

    # Register the script in the global file_renaming_scripts dict
    scripts[script_id] = {
        'id': script_id,
        'title': title,
        'script': script_content,
        'description': naming_section.get('description', ''),
        'author': naming_section.get('author', ''),
        'license': naming_section.get('license', ''),
        'version': naming_section.get('version', ''),
        'last_updated': naming_section.get('last_updated', ''),
        'script_language_version': naming_section.get('script_language_version', ''),
    }
    config.setting['file_renaming_scripts'] = scripts

    return script_id


def _import_tagger_scripts(
    config: Config,
    profile_settings: dict,
    tagging_section: list,
    result: ProfileImportResult,
):
    """Import tagger scripts into the profile settings."""
    # Get existing scripts from the profile (if any) or start fresh
    existing_scripts = profile_settings.get('list_of_scripts', [])

    # Track existing scripts for deduplication (title + content)
    existing_set = {(name, content) for _pos, name, _enabled, content in existing_scripts}

    next_pos = len(existing_scripts)
    imported_count = 0
    duplicate_count = 0

    for entry in tagging_section:
        title = entry.get('title', '')
        script = entry.get('script', '')
        enabled = entry.get('enabled', True)

        if not title or not script:
            continue

        # Deduplicate: skip if exact same title + content exists
        if (title, script) in existing_set:
            duplicate_count += 1
            continue

        existing_scripts.append((next_pos, title, enabled, script))
        existing_set.add((title, script))
        next_pos += 1
        imported_count += 1

    if duplicate_count:
        result.warnings.append(f"{duplicate_count} duplicate script(s) skipped (same title and content already exist).")

    if existing_scripts:
        profile_settings['list_of_scripts'] = existing_scripts
        profile_settings['enable_tagger_scripts'] = True


def _register_profile(
    config: Config,
    profile_id: str,
    title: str,
    enabled: bool,
    settings: dict,
    replace: bool = False,
):
    """Register or replace a profile in config."""
    profiles_list = config.profiles['user_profiles']

    if replace:
        # Update existing profile entry (keeps its position)
        for profile in profiles_list:
            if profile['id'] == profile_id:
                profile['title'] = title
                break
    else:
        # Insert new profile at the top (highest priority)
        profiles_list.insert(
            0,
            {
                'id': profile_id,
                'title': title,
                'enabled': enabled,
                'position': 0,
            },
        )
        # Update positions for all profiles
        for i, profile in enumerate(profiles_list):
            profile['position'] = i

    config.profiles['user_profiles'] = profiles_list

    all_settings = config.profiles['user_profile_settings']
    all_settings[profile_id] = settings
    config.profiles['user_profile_settings'] = all_settings

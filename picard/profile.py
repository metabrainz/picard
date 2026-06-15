# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2021-2023 Bob Swift
# Copyright (C) 2021-2023 Philipp Wolfer
# Copyright (C) 2021-2024 Laurent Monin
# Copyright (C) 2022 Marcin Szalowicz
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


from collections import (
    defaultdict,
    namedtuple,
)
from collections.abc import Iterator
from typing import TYPE_CHECKING

from picard.i18n import N_


if TYPE_CHECKING:
    from picard.ui.options import OptionsPage


SettingDesc = namedtuple('SettingDesc', ('name', 'highlights', 'section'), defaults=('setting',))


def setting_profile_key(name: str, section: str = 'setting') -> str:
    """Return the key used for an option in profile settings storage.

    Core options use bare name. Non-core options (plugins) use 'section/name'
    to avoid collisions.
    """
    if section == 'setting':
        return name
    return f'{section}/{name}'


_PLUGIN_PROFILE_KEY_PREFIX = 'plugin.'


def is_plugin_profile_key(key: str) -> bool:
    """Return True if the key is a plugin profile setting key."""
    return key.startswith(_PLUGIN_PROFILE_KEY_PREFIX)


_settings_groups: dict = {}
_groups_order: dict[str, int] = defaultdict(lambda: -1)
_groups_count: int = 0
_known_settings: set[str] = set()


def profile_groups_order(group: str) -> None:
    global _groups_count
    if _groups_order[group] == -1:
        _groups_order[group] = _groups_count
        _groups_count += 1


_PLUGINS_GROUP = 'plugins'


def profile_groups_add_setting(
    group: str,
    option_name: str,
    highlights: list[str],
    title: str | None = None,
    parent: str | None = None,
    section: str = 'setting',
) -> None:
    # Auto-create the "Plugins" parent group if needed
    if parent == _PLUGINS_GROUP and _PLUGINS_GROUP not in _settings_groups:
        _settings_groups[_PLUGINS_GROUP] = {
            'title': N_("Plugins"),
            'parent': '',
            'name': _PLUGINS_GROUP,
            'settings': [],
        }
    if group not in _settings_groups:
        _settings_groups[group] = {'title': title or group}
        _settings_groups[group]['parent'] = parent or ''
        _settings_groups[group]['name'] = group
    if 'settings' not in _settings_groups[group]:
        _settings_groups[group]['settings'] = []
    _settings_groups[group]['settings'].append(SettingDesc(option_name, highlights, section))
    _known_settings.add(setting_profile_key(option_name, section))


def profile_groups_all_settings() -> set[str]:
    return _known_settings


def profile_groups_settings(group: str) -> Iterator[SettingDesc]:
    if group in _settings_groups:
        if 'settings' in _settings_groups[group]:
            yield from _settings_groups[group]['settings']


def profile_groups_keys() -> Iterator[str]:
    """Iterable of all setting groups keys.

    Yields:
        str: Key
    """
    yield from _settings_groups.keys()


def profile_groups_group_from_page(page: 'OptionsPage') -> dict | None:
    try:
        return _settings_groups[page.NAME]
    except (AttributeError, KeyError):
        pass
    # For plugin pages, the group may be keyed by OPTION_SECTION
    try:
        section = getattr(page, 'OPTION_SECTION', None)
        if section and section in _settings_groups:
            return _settings_groups[section]
    except (AttributeError, KeyError):
        pass
    return None


def profile_groups_remove_group(group: str) -> None:
    """Remove a settings group (e.g. when a plugin is disabled)."""
    if group in _settings_groups:
        removed_keys = {setting_profile_key(s.name, s.section) for s in _settings_groups[group].get('settings', [])}
        del _settings_groups[group]
        # Only discard keys not still referenced by another group
        still_used = set()
        for other_group in _settings_groups.values():
            for s in other_group.get('settings', []):
                key = setting_profile_key(s.name, s.section)
                if key in removed_keys:
                    still_used.add(key)
        _known_settings.difference_update(removed_keys - still_used)


def profile_groups_update_highlights(option_name: str, highlights: tuple) -> None:
    """Update highlights for an already-registered setting."""
    for group in _settings_groups.values():
        for i, setting in enumerate(group.get('settings', [])):
            if setting.name == option_name:
                group['settings'][i] = SettingDesc(setting.name, highlights, setting.section)
                return


def profile_groups_values() -> Iterator[dict]:
    """Returns values sorted by (groups_order, group name)"""
    # Yield top level groups first to ensure that they are created in the
    # QTreeWidget before adding their children.
    for k in sorted(_settings_groups, key=lambda k: (_settings_groups[k]['parent'], _groups_order[k], k)):
        yield _settings_groups[k]


def profile_groups_reset() -> None:
    """Used when testing"""
    global _settings_groups, _groups_order, _groups_count, _known_settings
    _settings_groups = {}
    _groups_order = defaultdict(lambda: -1)
    _groups_count = 0
    _known_settings = set()

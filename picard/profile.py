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


SettingDesc = namedtuple('SettingDesc', ('name', 'highlights'))

_settings_groups = {}
_groups_order = defaultdict(lambda: -1)
_groups_count = 0
_known_settings = set()


def profile_groups_order(group):
    global _groups_count
    if _groups_order[group] == -1:
        _groups_order[group] = _groups_count
        _groups_count += 1


def profile_groups_add_setting(group, option_name, highlights, title=None):
    if group not in _settings_groups:
        _settings_groups[group] = {'title': title or group}
    if 'settings' not in _settings_groups[group]:
        _settings_groups[group]['settings'] = []
    _settings_groups[group]['settings'].append(SettingDesc(option_name, highlights))
    _known_settings.add(option_name)


def profile_groups_all_settings():
    return _known_settings


def profile_groups_settings(group):
    if group in _settings_groups:
        if 'settings' in _settings_groups[group]:
            yield from _settings_groups[group]['settings']


def profile_groups_keys():
    """Iterable of all setting groups keys.

    Yields:
        str: Key
    """
    yield from _settings_groups.keys()


def profile_groups_group_from_page(page):
    try:
        return _settings_groups[page.NAME]
    except (AttributeError, KeyError):
        return None


def profile_groups_values():
    """Returns values sorted by (groups_order, group name)"""
    for k in sorted(_settings_groups, key=lambda k: (_groups_order[k], k)):
        yield _settings_groups[k]


def profile_groups_reset():
    """Used when testing"""
    global _settings_groups, _groups_order, _groups_count, _known_settings
    _settings_groups = {}
    _groups_order = defaultdict(lambda: -1)
    _groups_count = 0
    _known_settings = set()

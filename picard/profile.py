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


SettingDesc = namedtuple('SettingDesc', ('name', 'fields'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    _settings_groups = {}

    _groups_order = defaultdict(lambda: -1)
    _groups_count = 0

    @classmethod
    def order(cls, group):
        if cls._groups_order[group] == -1:
            cls._groups_order[group] = cls._groups_count
            cls._groups_count += 1

    @classmethod
    def append_to_group(cls, group, option, highlights, title=None):
        if group not in cls._settings_groups:
            cls._settings_groups[group] = {'title': title or group}
        if 'settings' not in cls._settings_groups[group]:
            cls._settings_groups[group]['settings'] = []
        cls._settings_groups[group]['settings'].append(SettingDesc(option, highlights))

    @classmethod
    def all_settings(cls):
        for value in cls._settings_groups.values():
            if 'settings' in value:
                for s in value['settings']:
                    yield s.name

    @classmethod
    def settings(cls, group):
        if group in cls._settings_groups:
            if 'settings' in cls._settings_groups[group]:
                yield from cls._settings_groups[group]['settings']

    @classmethod
    def keys(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls._settings_groups.keys()

    @classmethod
    def group_from_page(cls, page):
        try:
            return cls._settings_groups[page.NAME]
        except (AttributeError, KeyError):
            pass
        return None

    @classmethod
    def values(cls):
        """Returns values sorted by (groups_order, group name)"""
        for k in sorted(cls._settings_groups, key=lambda k: (cls._groups_order[k], k)):
            yield cls._settings_groups[k]

    @classmethod
    def reset(cls):
        """Used when testing"""
        cls._settings_groups = {}
        cls._groups_order = defaultdict(lambda: -1)
        cls._groups_count = 0

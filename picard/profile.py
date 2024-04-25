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
    OrderedDict,
    namedtuple,
)

from picard.i18n import N_


SettingDesc = namedtuple('SettingDesc', ('name', 'fields'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    # Each item in "settings" is a tuple of the setting key, the display title, and a list of the names of the widgets to highlight
    SETTINGS_GROUPS['general'] = {
        'title': N_("General"),
        'settings': [],
    }

    SETTINGS_GROUPS['metadata'] = {
        'title': N_("Metadata"),
        'settings': [],
    }

    SETTINGS_GROUPS['tags'] = {
        'title': N_("Tags"),
        'settings': [],
    }

    SETTINGS_GROUPS['cover'] = {
        'title': N_("Cover Art"),
        'settings': [],
    }

    SETTINGS_GROUPS['filerenaming'] = {
        'title': N_("File Naming"),
        'settings': [],
    }

    SETTINGS_GROUPS['scripting'] = {
        'title': N_("Scripting"),
        'settings': [],
    }

    SETTINGS_GROUPS['interface'] = {
        'title': N_("User Interface"),
        'settings': [],
    }

    SETTINGS_GROUPS['advanced'] = {
        'title': N_("Advanced"),
        'settings': [],
    }

    ALL_SETTINGS = set(
        s.name for group in SETTINGS_GROUPS.values()
        for s in group['settings']
    )

    @classmethod
    def get_setting_groups_list(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls.SETTINGS_GROUPS


def register_profile_highlights(group, option, higlights):
    UserProfileGroups.SETTINGS_GROUPS[group]['settings'].append(SettingDesc(option, higlights))

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

# Imported to trigger inclusion of N_() in builtins
from picard import i18n  # noqa: F401,E402 # pylint: disable=unused-import


SettingDesc = namedtuple('SettingDesc', ('name', 'fields'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    ALL_SETTINGS = set()

    @classmethod
    def get_setting_groups_list(cls):
        """Iterable of all setting groups keys.

        Yields:
            str: Key
        """
        yield from cls.SETTINGS_GROUPS

    @classmethod
    def initialize(cls):
        from picard.ui.options import _pages as page_classes

        def _all_pages(parent=None):
            pages = [p for p in page_classes if p.PARENT == parent]
            for page in sorted(pages, key=lambda p: (p.SORT_ORDER, p.NAME)):
                yield page
                yield from _all_pages(page.NAME)

        for page in _all_pages():
            settings = []
            for opt in page.options:
                if opt.title is not None:
                    settings.append(SettingDesc(opt.name, opt.highlight))
            if settings:
                cls.SETTINGS_GROUPS[page.NAME] = {
                    'title': page.TITLE,
                    'settings': settings,
                }

        cls.ALL_SETTINGS = set(
            s.name for group in cls.SETTINGS_GROUPS.values()
            for s in group['settings']
        )

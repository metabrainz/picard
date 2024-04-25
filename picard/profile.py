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
        'settings': [
            SettingDesc('enable_tagger_scripts', ['enable_tagger_scripts']),
            SettingDesc('list_of_scripts', ['script_list']),
        ],
    }

    SETTINGS_GROUPS['interface'] = {
        'title': N_("User Interface"),
        'settings': [
            # Main User Interface Page
            SettingDesc('toolbar_show_labels', ['toolbar_show_labels']),
            SettingDesc('show_menu_icons', ['show_menu_icons']),
            SettingDesc('ui_language', ['ui_language', 'label']),
            SettingDesc('ui_theme', ['ui_theme', 'label_theme']),
            SettingDesc('allow_multi_dirs_selection', ['allow_multi_dirs_selection']),
            SettingDesc('builtin_search', ['builtin_search']),
            SettingDesc('use_adv_search_syntax', ['use_adv_search_syntax']),
            SettingDesc('show_new_user_dialog', ['new_user_dialog']),
            SettingDesc('quit_confirmation', ['quit_confirmation']),
            SettingDesc('file_save_warning', ['file_save_warning']),
            SettingDesc('filebrowser_horizontal_autoscroll', ['filebrowser_horizontal_autoscroll']),
            SettingDesc('starting_directory', ['starting_directory']),
            SettingDesc('starting_directory_path', ['starting_directory_path']),

            # User Interface Colors Page
            SettingDesc('interface_colors', ['colors']),
            SettingDesc('interface_colors_dark', ['colors']),

            # User Interface Top Tags Page
            SettingDesc('metadatabox_top_tags', ['top_tags_groupBox']),

            # User Interface Action Toolbar Page
            SettingDesc('toolbar_layout', ['toolbar_layout_list']),
        ],
    }

    SETTINGS_GROUPS['advanced'] = {
        'title': N_("Advanced"),
        'settings': [
            # Main Advanced Options Page
            SettingDesc('ignore_regex', ['ignore_regex']),
            SettingDesc('ignore_hidden_files', ['ignore_hidden_files']),
            SettingDesc('recursively_add_files', ['recursively_add_files']),
            SettingDesc(
                'ignore_track_duration_difference_under',
                ['ignore_track_duration_difference_under', 'label_track_duration_diff']
            ),
            SettingDesc(
                'query_limit',
                ['query_limit', 'label_query_limit']
            ),
            SettingDesc('completeness_ignore_videos', ['completeness_ignore_videos']),
            SettingDesc('completeness_ignore_pregap', ['completeness_ignore_pregap']),
            SettingDesc('completeness_ignore_data', ['completeness_ignore_data']),
            SettingDesc('completeness_ignore_silence', ['completeness_ignore_silence']),
            SettingDesc('compare_ignore_tags', ['groupBox_ignore_tags']),

            # Network Options Page
            SettingDesc('use_proxy', []),   # No highlight specified because the 'use_proxy'
                                            # object is a QGroupBox and it highlights all sub
                                            # options, even if the sub options are not selected.
            SettingDesc('proxy_type', ['proxy_type_socks', 'proxy_type_http']),
            SettingDesc('proxy_server_host', ['server_host']),
            SettingDesc('proxy_server_port', ['server_port']),
            SettingDesc('proxy_username', ['username']),
            SettingDesc('proxy_password', ['password']),
            SettingDesc('network_transfer_timeout_seconds', ['transfer_timeout']),
            SettingDesc('network_cache_size_bytes', ['network_cache_size']),
            SettingDesc('browser_integration', []),  # No highlight specified because the 'browser_integration'
                                                     # object is a QGroupBox and it highlights all sub options,
                                                     # even if the sub options are not selected.
            SettingDesc('browser_integration_port', ['browser_integration_port']),
            SettingDesc('browser_integration_localhost_only', ['browser_integration_localhost_only']),

            # Matching Options Page
            SettingDesc('file_lookup_threshold', ['file_lookup_threshold']),
            SettingDesc('cluster_lookup_threshold', ['cluster_lookup_threshold']),
            SettingDesc('track_matching_threshold', ['track_matching_threshold']),

            # Maintenance Options Page
            SettingDesc('autobackup_directory', ['autobackup_dir']),
        ],
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

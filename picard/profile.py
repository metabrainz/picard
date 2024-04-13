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

    # Each item in "settings" is a tuple of the setting key, the display title, and a list of the names of the widgets to highlight
    SETTINGS_GROUPS['general'] = {
        'title': N_("General"),
        'settings': [
            SettingDesc('server_host', ['server_host']),
            SettingDesc('server_port', ['server_port']),
            SettingDesc('analyze_new_files', ['analyze_new_files']),
            SettingDesc('cluster_new_files', ['cluster_new_files']),
            SettingDesc('ignore_file_mbids', ['ignore_file_mbids']),
            SettingDesc('check_for_plugin_updates', ['check_for_plugin_updates']),
            SettingDesc('check_for_updates', ['check_for_updates']),
            SettingDesc('update_check_days', ['update_check_days']),
            SettingDesc('update_level', ['update_level']),
        ],
    }

    SETTINGS_GROUPS['metadata'] = {
        'title': N_("Metadata"),
        'settings': [
            # Main Metadata Page
            SettingDesc('translate_artist_names', ['translate_artist_names']),
            SettingDesc('artist_locales', ['selected_locales']),
            SettingDesc('translate_artist_names_script_exception', ['translate_artist_names_script_exception']),
            SettingDesc('script_exceptions', ['selected_scripts']),
            SettingDesc('standardize_artists', ['standardize_artists']),
            SettingDesc('standardize_instruments', ['standardize_instruments']),
            SettingDesc('convert_punctuation', ['convert_punctuation']),
            SettingDesc('release_ars', ['release_ars']),
            SettingDesc('track_ars', ['track_ars']),
            SettingDesc('guess_tracknumber_and_title', ['guess_tracknumber_and_title']),
            SettingDesc('va_name', ['va_name']),
            SettingDesc('nat_name', ['nat_name']),

            # Preferred Releases Page
            SettingDesc('release_type_scores', ['type_group']),
            SettingDesc('preferred_release_countries', ['country_group']),
            SettingDesc('preferred_release_formats', ['format_group']),

            # Genres Page
            SettingDesc('use_genres', []),  # No highlight specified because the 'use_genres'
                                            # object is a QGroupBox and it highlights all sub
                                            # options, even if the sub options are not selected.
            SettingDesc('only_my_genres', ['only_my_genres']),
            SettingDesc('artists_genres', ['artists_genres']),
            SettingDesc('folksonomy_tags', ['folksonomy_tags']),
            SettingDesc('min_genre_usage', ['min_genre_usage']),
            SettingDesc('max_genres', ['max_genres']),
            SettingDesc('join_genres', ['join_genres']),
            SettingDesc('genres_filter', ['genres_filter']),

            # Ratings Page
            SettingDesc('enable_ratings', []),  # No highlight specified because the 'enable_ratings'
                                                # object is a QGroupBox and it highlights all sub options,
                                                # even if the sub options are not selected.
            SettingDesc('rating_user_email', ['rating_user_email']),
            SettingDesc('submit_ratings', ['submit_ratings']),
        ],
    }

    SETTINGS_GROUPS['tags'] = {
        'title': N_("Tags"),
        'settings': [
            # Main Tags Page
            SettingDesc('dont_write_tags', ['write_tags']),
            SettingDesc('preserve_timestamps', ['preserve_timestamps']),
            SettingDesc('clear_existing_tags', ['clear_existing_tags']),
            SettingDesc('preserve_images', ['preserve_images']),
            SettingDesc('remove_id3_from_flac', ['remove_id3_from_flac']),
            SettingDesc('remove_ape_from_mp3', ['remove_ape_from_mp3']),
            SettingDesc('fix_missing_seekpoints_flac', ['fix_missing_seekpoints_flac']),
            SettingDesc('preserved_tags', ['preserved_tags']),

            # ID3 Tags Page
            SettingDesc('write_id3v23', ['write_id3v23', 'write_id3v24']),
            SettingDesc('id3v2_encoding', ['enc_utf8', 'enc_utf16', 'enc_iso88591']),
            SettingDesc('id3v23_join_with', ['id3v23_join_with']),
            SettingDesc('itunes_compatible_grouping', ['itunes_compatible_grouping']),
            SettingDesc('write_id3v1', ['write_id3v1']),

            # AAC Tags Page
            SettingDesc('aac_save_ape', ['aac_save_ape', 'aac_no_tags']),
            SettingDesc('remove_ape_from_aac', ['remove_ape_from_aac']),

            # AC3 Tags Page
            SettingDesc('ac3_save_ape', ['ac3_save_ape', 'ac3_no_tags']),
            SettingDesc('remove_ape_from_ac3', ['remove_ape_from_ac3']),

            # WAVE Tags Page
            SettingDesc('write_wave_riff_info', ['write_wave_riff_info']),
            SettingDesc('remove_wave_riff_info', ['remove_wave_riff_info']),
            SettingDesc('wave_riff_info_encoding', ['wave_riff_info_enc_cp1252', 'wave_riff_info_enc_utf8']),
        ],
    }

    SETTINGS_GROUPS['cover'] = {
        'title': N_("Cover Art"),
        'settings': [
            SettingDesc('save_images_to_tags', ['save_images_to_tags']),
            SettingDesc('embed_only_one_front_image', ['cb_embed_front_only']),
            SettingDesc('save_images_to_files', ['save_images_to_files']),
            SettingDesc('cover_image_filename', ['cover_image_filename']),
            SettingDesc('save_images_overwrite', ['save_images_overwrite']),
            SettingDesc('save_only_one_front_image', ['save_only_one_front_image']),
            SettingDesc('image_type_as_filename', ['image_type_as_filename']),
            SettingDesc('ca_providers', ['ca_providers_list']),
        ],
    }

    SETTINGS_GROUPS['filerenaming'] = {
        'title': N_("File Naming"),
        'settings': [
            # Main File Naming Page
            SettingDesc('move_files', ['move_files']),
            SettingDesc('move_files_to', ['move_files_to']),
            SettingDesc('move_additional_files', ['move_additional_files']),
            SettingDesc('move_additional_files_pattern', ['move_additional_files_pattern']),
            SettingDesc('delete_empty_dirs', ['delete_empty_dirs']),
            SettingDesc('rename_files', ['rename_files']),
            SettingDesc('selected_file_naming_script_id', ['naming_script_selector']),

            # File Naming Compatibility Page
            SettingDesc('ascii_filenames', ['ascii_filenames']),
            SettingDesc('windows_compatibility', ['windows_compatibility']),
            SettingDesc('win_compat_replacements', ['win_compat_replacements']),
            SettingDesc('windows_long_paths', ['windows_long_paths']),
            SettingDesc('replace_spaces_with_underscores', ['replace_spaces_with_underscores']),
            SettingDesc('replace_dir_separator', ['replace_dir_separator']),
        ],
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

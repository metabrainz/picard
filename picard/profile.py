# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2021-2022 Bob Swift
# Copyright (C) 2021-2022 Laurent Monin
# Copyright (C) 2021-2022 Philipp Wolfer
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


SettingDesc = namedtuple('SettingDesc', ('name', 'title', 'fields'))


class UserProfileGroups():
    """Provides information about the profile groups available for selecting in a user profile,
    and the title and settings that apply to each profile group.
    """
    SETTINGS_GROUPS = OrderedDict()  # Add groups in the order they should be displayed

    # Each item in "settings" is a tuple of the setting key, the display title, and a list of the names of the widgets to highlight
    SETTINGS_GROUPS['general'] = {
        'title': N_("General"),
        'settings': [
            SettingDesc('server_host', N_("Server address"), ['server_host']),
            SettingDesc('server_port', N_("Port"), ['server_port']),
            SettingDesc('analyze_new_files', N_("Automatically scan all new files"), ['analyze_new_files']),
            SettingDesc('cluster_new_files', N_("Automatically cluster all new files"), ['cluster_new_files']),
            SettingDesc('ignore_file_mbids', N_("Ignore MBIDs when loading new files"), ['ignore_file_mbids']),
            SettingDesc('check_for_plugin_updates', N_("Check for plugin updates during startup"), ['check_for_plugin_updates']),
            SettingDesc('check_for_updates', N_("Check for program updates during startup"), ['check_for_updates']),
            SettingDesc('update_check_days', N_("Days between update checks"), ['update_check_days']),
            SettingDesc('update_level', N_("Updates to check"), ['update_level']),
        ],
    }

    SETTINGS_GROUPS['metadata'] = {
        'title': N_("Metadata"),
        'settings': [
            # Main Metadata Page
            SettingDesc('translate_artist_names', N_("Translate artist names"), ['translate_artist_names']),
            SettingDesc('artist_locales', N_("Translation locales"), ['selected_locales']),
            SettingDesc('translate_artist_names_script_exception', N_("Translate artist names exception"), ['translate_artist_names_script_exception']),
            SettingDesc('script_exceptions', N_("Translation script exceptions"), ['selected_scripts']),
            SettingDesc('standardize_artists', N_("Use standardized artist names"), ['standardize_artists']),
            SettingDesc('standardize_instruments', N_("Use standardized instrument and vocal credits"), ['standardize_instruments']),
            SettingDesc('convert_punctuation', N_("Convert Unicode punctuation characters to ASCII"), ['convert_punctuation']),
            SettingDesc('release_ars', N_("Use release relationships"), ['release_ars']),
            SettingDesc('track_ars', N_("Use track relationships"), ['track_ars']),
            SettingDesc('guess_tracknumber_and_title', N_("Guess track number and title from filename if empty"), ['guess_tracknumber_and_title']),
            SettingDesc('va_name', N_("Various Artists name"), ['va_name']),
            SettingDesc('nat_name', N_("Standalone recordings name"), ['nat_name']),

            # Preferred Releases Page
            SettingDesc('release_type_scores', N_("Preferred release types"), ['type_group']),
            SettingDesc('preferred_release_countries', N_("Preferred release countries"), ['country_group']),
            SettingDesc('preferred_release_formats', N_("Preferred medium formats"), ['format_group']),

            # Genres Page
            SettingDesc('use_genres', N_("Use genres from MusicBrainz"), []),   # No highlight specified because the 'use_genres'
                                                                                # object is a QGroupBox and it highlights all sub
                                                                                # options, even if the sub options are not selected.
            SettingDesc('only_my_genres', N_("Use only my genres"), ['only_my_genres']),
            SettingDesc('artists_genres', N_("Use album artist genres"), ['artists_genres']),
            SettingDesc('folksonomy_tags', N_("Use folksonomy tags as genre"), ['folksonomy_tags']),
            SettingDesc('min_genre_usage', N_("Minimal genre usage"), ['min_genre_usage']),
            SettingDesc('max_genres', N_("Maximum number of genres"), ['max_genres']),
            SettingDesc('join_genres', N_("Join multiple genres with"), ['join_genres']),
            SettingDesc('genres_filter', N_("Genres to include or exclude"), ['genres_filter']),

            # Ratings Page
            SettingDesc('enable_ratings', N_("Enable track ratings"), []),  # No highlight specified because the 'enable_ratings'
                                                                            # object is a QGroupBox and it highlights all sub options,
                                                                            # even if the sub options are not selected.
            SettingDesc('rating_user_email', N_("Email to use when saving ratings"), ['rating_user_email']),
            SettingDesc('submit_ratings', N_("Submit ratings to MusicBrainz"), ['submit_ratings']),
        ],
    }

    SETTINGS_GROUPS['tags'] = {
        'title': N_("Tags"),
        'settings': [
            # Main Tags Page
            SettingDesc('dont_write_tags', N_("Don't write tags"), ['write_tags']),
            SettingDesc('preserve_timestamps', N_("Preserve timestamps of tagged files"), ['preserve_timestamps']),
            SettingDesc('clear_existing_tags', N_("Clear existing tags"), ['clear_existing_tags']),
            SettingDesc('preserve_images', N_("Keep embedded images when clearing tags"), ['preserve_images']),
            SettingDesc('remove_id3_from_flac', N_("Remove ID3 tags from FLAC files"), ['remove_id3_from_flac']),
            SettingDesc('remove_ape_from_mp3', N_("Remove APEv2 tags from MP3 files"), ['remove_ape_from_mp3']),
            SettingDesc('fix_missing_seekpoints_flac', N_("Fix missing seekpoints for FLAC files"), ['fix_missing_seekpoints_flac']),
            SettingDesc('preserved_tags', N_("Preserved tags list"), ['preserved_tags']),

            # ID3 Tags Page
            SettingDesc('write_id3v23', N_("ID3v2 version to write"), ['write_id3v23', 'write_id3v24']),
            SettingDesc('id3v2_encoding', N_("ID3v2 text encoding"), ['enc_utf8', 'enc_utf16', 'enc_iso88591']),
            SettingDesc('id3v23_join_with', N_("ID3v2.3 join character"), ['id3v23_join_with']),
            SettingDesc('itunes_compatible_grouping', N_("Save iTunes compatible grouping and work"), ['itunes_compatible_grouping']),
            SettingDesc('write_id3v1', N_("Write ID3v1 tags"), ['write_id3v1']),

            # AAC Tags Page
            SettingDesc('aac_save_ape', N_("Save APEv2 tags to AAC"), ['aac_save_ape', 'aac_no_tags']),
            SettingDesc('remove_ape_from_aac', N_("Remove APEv2 tags from AAC files"), ['remove_ape_from_aac']),

            # AC3 Tags Page
            SettingDesc('ac3_save_ape', N_("Save APEv2 tags to AC3"), ['ac3_save_ape', 'ac3_no_tags']),
            SettingDesc('remove_ape_from_ac3', N_("Remove APEv2 tags from AC3 files"), ['remove_ape_from_ac3']),

            # WAVE Tags Page
            SettingDesc('write_wave_riff_info', N_("Write RIFF INFO tags to WAVE files"), ['write_wave_riff_info']),
            SettingDesc('remove_wave_riff_info', N_("Remove existing RIFF INFO tags from WAVE files"), ['remove_wave_riff_info']),
            SettingDesc('wave_riff_info_encoding', N_("RIFF INFO text encoding"), ['wave_riff_info_enc_cp1252', 'wave_riff_info_enc_utf8']),
        ],
    }

    SETTINGS_GROUPS['cover'] = {
        'title': N_("Cover Art"),
        'settings': [
            SettingDesc('save_images_to_tags', N_("Embed cover images into tags"), ['save_images_to_tags']),
            SettingDesc('embed_only_one_front_image', N_("Embed only a single front image"), ['cb_embed_front_only']),
            SettingDesc('save_images_to_files', N_("Save cover images as separate files"), ['save_images_to_files']),
            SettingDesc('cover_image_filename', N_("File name for images"), ['cover_image_filename']),
            SettingDesc('save_images_overwrite', N_("Overwrite existing image files"), ['save_images_overwrite']),
            SettingDesc('save_only_one_front_image', N_("Save only a single front image as separate file"), ['save_only_one_front_image']),
            SettingDesc('image_type_as_filename', N_("Always use the primary image type as the file name for non-front images"), ['image_type_as_filename']),
            SettingDesc('ca_providers', N_("Cover art providers"), ['ca_providers_list']),
        ],
    }

    SETTINGS_GROUPS['filerenaming'] = {
        'title': N_("File Naming"),
        'settings': [
            # Main File Naming Page
            SettingDesc('move_files', N_("Move files"), ['move_files']),
            SettingDesc('move_files_to', N_("Destination directory"), ['move_files_to']),
            SettingDesc('move_additional_files', N_("Move additional files"), ['move_additional_files']),
            SettingDesc('move_additional_files_pattern', N_("Additional file patterns"), ['move_additional_files_pattern']),
            SettingDesc('delete_empty_dirs', N_("Delete empty directories"), ['delete_empty_dirs']),
            SettingDesc('rename_files', N_("Rename files"), ['rename_files']),
            SettingDesc('selected_file_naming_script_id', N_("Selected file naming script"), ['naming_script_selector']),

            # File Naming Compatibility Page
            SettingDesc('ascii_filenames', N_("Replace non-ASCII characters"), ['ascii_filenames']),
            SettingDesc('windows_compatibility', N_("Windows compatibility"), ['windows_compatibility']),
            SettingDesc('win_compat_replacements', N_("Replacement characters used for Windows compatibility"), ['win_compat_replacements']),
            SettingDesc('windows_long_paths', N_("Windows long path support"), ['windows_long_paths']),
            SettingDesc('replace_spaces_with_underscores', N_("Replace spaces with underscores"), ['replace_spaces_with_underscores']),
            SettingDesc('replace_dir_separator', N_("Replacement character to use for directory separators"), ['replace_dir_separator']),
        ],
    }

    SETTINGS_GROUPS['scripting'] = {
        'title': N_("Scripting"),
        'settings': [
            SettingDesc('enable_tagger_scripts', N_("Enable tagger scripts"), ['enable_tagger_scripts']),
            SettingDesc('list_of_scripts', N_("Tagger scripts"), ['script_list']),
        ],
    }

    SETTINGS_GROUPS['interface'] = {
        'title': N_("User Interface"),
        'settings': [
            # Main User Interface Page
            SettingDesc('toolbar_show_labels', N_("Show text labels under icons"), ['toolbar_show_labels']),
            SettingDesc('show_menu_icons', N_("Show icons in menus"), ['show_menu_icons']),
            SettingDesc('ui_language', N_("User interface language"), ['ui_language', 'label']),
            SettingDesc('ui_theme', N_("User interface color theme"), ['ui_theme', 'label_theme']),
            SettingDesc('toolbar_multiselect', N_("Allow selection of multiple directories"), ['toolbar_multiselect']),
            SettingDesc('builtin_search', N_("Use builtin search rather than looking in browser"), ['builtin_search']),
            SettingDesc('use_adv_search_syntax', N_("Use advanced search syntax"), ['use_adv_search_syntax']),
            SettingDesc('show_new_user_dialog', N_("Show a usage warning dialog when Picard starts"), ['new_user_dialog']),
            SettingDesc('quit_confirmation', N_("Show a quit confirmation dialog for unsaved changes"), ['quit_confirmation']),
            SettingDesc('file_save_warning', N_("Show a confirmation dialog when saving files"), ['file_save_warning']),
            SettingDesc('filebrowser_horizontal_autoscroll', N_("Adjust horizontal position in file browser automatically"), ['filebrowser_horizontal_autoscroll']),
            SettingDesc('starting_directory', N_("Begin browsing in a specific directory"), ['starting_directory']),
            SettingDesc('starting_directory_path', N_("Directory to begin browsing"), ['starting_directory_path']),

            # User Interface Colors Page
            SettingDesc('interface_colors', N_("Colors to use for light theme"), ['colors']),
            SettingDesc('interface_colors_dark', N_("Colors to use for dark theme"), ['colors']),

            # User Interface Top Tags Page
            SettingDesc('metadatabox_top_tags', N_("Tags to show at the top"), ['top_tags_groupBox']),

            # User Interface Action Toolbar Page
            SettingDesc('toolbar_layout', N_("Layout of the tool bar"), ['toolbar_layout_list']),
        ],
    }

    SETTINGS_GROUPS['advanced'] = {
        'title': N_("Advanced"),
        'settings': [
            # Main Advanced Options Page
            SettingDesc('ignore_regex', N_("Ignore file paths matching a regular expression"), ['ignore_regex']),
            SettingDesc('ignore_hidden_files', N_("Ignore hidden files"), ['ignore_hidden_files']),
            SettingDesc('recursively_add_files', N_("Include sub-folders when adding files from folder"), ['recursively_add_files']),
            SettingDesc(
                'ignore_track_duration_difference_under',
                N_("Ignore track duration difference under x seconds"),
                ['ignore_track_duration_difference_under', 'label_track_duration_diff']
            ),
            SettingDesc(
                'query_limit',
                N_("Maximum number of entities to return per MusicBrainz query"),
                ['query_limit', 'label_query_limit']
            ),
            SettingDesc('completeness_ignore_videos', N_("Completeness check ignore: Video tracks"), ['completeness_ignore_videos']),
            SettingDesc('completeness_ignore_pregap', N_("Completeness check ignore: Pregap tracks"), ['completeness_ignore_pregap']),
            SettingDesc('completeness_ignore_data', N_("Completeness check ignore: Data tracks"), ['completeness_ignore_data']),
            SettingDesc('completeness_ignore_silence', N_("Completeness check ignore: Silent tracks"), ['completeness_ignore_silence']),
            SettingDesc('compare_ignore_tags', N_("Tags to ignore for comparison"), ['groupBox_2']),

            # Network Options Page
            SettingDesc('use_proxy', N_("Use a web proxy server"), []),     # No highlight specified because the 'use_proxy'
                                                                            # object is a QGroupBox and it highlights all sub
                                                                            # options, even if the sub options are not selected.
            SettingDesc('proxy_type', N_("type of proxy server"), ['proxy_type_socks', 'proxy_type_http']),
            SettingDesc('proxy_server_host', N_("Proxy server address"), ['server_host']),
            SettingDesc('proxy_server_port', N_("Proxy server port"), ['server_port']),
            SettingDesc('proxy_username', N_("Proxy username"), ['username']),
            SettingDesc('proxy_password', N_("Proxy password"), ['password']),
            SettingDesc('network_transfer_timeout_seconds', N_("Request timeout in seconds"), ['transfer_timeout']),
            SettingDesc('browser_integration', N_("Browser integration"), []),  # No highlight specified because the 'browser_integration'
                                                                                # object is a QGroupBox and it highlights all sub options,
                                                                                # even if the sub options are not selected.
            SettingDesc('browser_integration_port', N_("Default listening port"), ['browser_integration_port']),
            SettingDesc('browser_integration_localhost_only', N_("Listen only on localhost"), ['browser_integration_localhost_only']),

            # Matching Options Page
            SettingDesc('file_lookup_threshold', N_("Minimal similarity for file lookups"), ['file_lookup_threshold']),
            SettingDesc('cluster_lookup_threshold', N_("Minimal similarity for cluster lookups"), ['cluster_lookup_threshold']),
            SettingDesc('track_matching_threshold', N_("Minimal similarity for matching files to tracks"), ['track_matching_threshold']),
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

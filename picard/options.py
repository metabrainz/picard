# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Laurent Monin
# Copyright (C) 2025 Philipp Wolfer
# Copyright (C) 2025-2026 Bob Swift
# Copyright (C) 2025 David Kellner
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


import logging

from PyQt6 import QtCore

from picard.config import (
    BoolOption,
    FloatOption,
    IntOption,
    ListOption,
    Option,
    TextOption,
)
from picard.const import MUSICBRAINZ_SERVERS
from picard.const.defaults import (
    DEFAULT_AUTOBACKUP_DIRECTORY,
    DEFAULT_CA_NEVER_REPLACE_TYPE_EXCLUDE,
    DEFAULT_CA_NEVER_REPLACE_TYPE_INCLUDE,
    DEFAULT_CA_PROVIDERS,
    DEFAULT_CAA_IMAGE_SIZE,
    DEFAULT_CAA_IMAGE_TYPE_EXCLUDE,
    DEFAULT_CAA_IMAGE_TYPE_INCLUDE,
    DEFAULT_CACHE_SIZE_IN_BYTES,
    DEFAULT_COVER_CONVERTING_FORMAT,
    DEFAULT_COVER_IMAGE_FILENAME,
    DEFAULT_COVER_IMAGE_QUALITY,
    DEFAULT_COVER_MAX_SIZE,
    DEFAULT_COVER_MIN_SIZE,
    DEFAULT_COVER_RESIZE_MODE,
    DEFAULT_CURRENT_BROWSER_PATH,
    DEFAULT_DRIVES,
    DEFAULT_FILTER_COLUMNS,
    DEFAULT_FPCALC_THREADS,
    DEFAULT_LOCAL_COVER_ART_REGEX,
    DEFAULT_LONG_PATHS,
    DEFAULT_MUSIC_DIR,
    DEFAULT_PROGRAM_UPDATE_LEVEL,
    DEFAULT_QUERY_LIMIT,
    DEFAULT_QUICK_MENU_ITEMS,
    DEFAULT_RELEASE_TYPE_SCORES,
    DEFAULT_REPLACEMENT,
    DEFAULT_SHOW_MENU_ICONS,
    DEFAULT_STARTING_DIR,
    DEFAULT_THEME_NAME,
    DEFAULT_TOOLBAR_LAYOUT,
    DEFAULT_TOP_TAGS,
    DEFAULT_WIN_COMPAT_REPLACEMENTS,
)
from picard.i18n import N_

from picard.ui.colors import InterfaceColors


# Note: There are two steps to adding an option to an option page:
#
#   1. The option is added to the appropriate section below.
#      If it's using a default value that may be used elsewhere,
#      a constant starting with `DEFAULT_` can be added to `const/defaults.py`
#      and imported here.
#
#      The `title` parameter of `Option` is required for options that may be
#      used in user profiles.
#      The translated title will be displayed in Profiles option page.
#
#   2. If the option is a 'setting' which is edited in one of the option pages,
#      then the option must be added to the OPTIONS tuple in the class. The
#      first parameter is the option name, the second is a list of UI elements
#      to highlight if the option is part of an option profile. If the setting
#      can be overridden in profiles, the `highlights` has to be a list of
#      widget names associated with the option.
#
#      Registering a setting allows it to be reset to the default when the user
#      asks for it on the corresponding option page.
#
# Please, try to keep options ordered by section and name in their own group.
#
# Note: If the option is a 'setting' which is not edited in one of the option
#       pages, it must be added to the `OPTIONS_NOT_IN_PAGES` set in the file
#       `picard/ui/options/maintenance.py` so that it will not be included in
#       the list of option settings that can be removed by the user.


# picard/coverart/providers/caa.py
# Cover Art Archive Cover Art Archive: Release
BoolOption('setting', 'caa_approved_only', False)
IntOption('setting', 'caa_image_size', DEFAULT_CAA_IMAGE_SIZE)
ListOption('setting', 'caa_image_types', DEFAULT_CAA_IMAGE_TYPE_INCLUDE)
ListOption('setting', 'caa_image_types_to_omit', DEFAULT_CAA_IMAGE_TYPE_EXCLUDE)
BoolOption('setting', 'caa_restrict_image_types', True)

# picard/coverart/providers/local.py
# Local Files
TextOption('setting', 'local_cover_regex', DEFAULT_LOCAL_COVER_ART_REGEX)

# picard/ui/cdlookup.py
#
Option('persist', 'cdlookupdialog_header_state', QtCore.QByteArray())

# picard/ui/filebrowser.py
#
TextOption('persist', 'current_browser_path', DEFAULT_CURRENT_BROWSER_PATH)
BoolOption('persist', 'show_hidden_files', False)

# Store Album View Header State
#
Option('persist', 'album_view_header_columns', {})
BoolOption('persist', 'album_view_header_locked', False)

# Store File View Header State
#
Option('persist', 'file_view_header_columns', {})
BoolOption('persist', 'file_view_header_locked', False)

# picard/ui/logview.py
#
IntOption('setting', 'log_verbosity', logging.WARNING)

# picard/ui/mainwindow.py
#
TextOption('persist', 'current_directory', "")
FloatOption('persist', 'mediaplayer_playback_rate', 1.0)
IntOption('persist', 'mediaplayer_volume', 50)
BoolOption('persist', 'view_cover_art', True)
BoolOption('persist', 'view_file_browser', False)
BoolOption('persist', 'view_metadata_view', True)
BoolOption('persist', 'view_toolbar', True)
BoolOption('persist', 'view_filterbar', False)
BoolOption('persist', 'window_maximized', False)
Option('persist', 'window_state', QtCore.QByteArray())
ListOption('persist', 'filters_FileTreeView', DEFAULT_FILTER_COLUMNS)
ListOption('persist', 'filters_AlbumTreeView', DEFAULT_FILTER_COLUMNS)
TextOption('persist', 'last_session_path', '')
ListOption('persist', 'recent_sessions', [])
TextOption('persist', 'session_autosave_path', '')

# picard/ui/metadatabox.py
#
Option('persist', 'metadatabox_header_state', QtCore.QByteArray())
BoolOption('persist', 'show_changes_first', False)

# picard/ui/options/advanced.py
# Advanced
ListOption('setting', 'compare_ignore_tags', [], title=N_("Tags to ignore for comparison"))
BoolOption('setting', 'completeness_ignore_data', False, title=N_("Completeness ignore: Data tracks"))
BoolOption('setting', 'completeness_ignore_pregap', False, title=N_("Completeness ignore: Pregap tracks"))
BoolOption('setting', 'completeness_ignore_silence', False, title=N_("Completeness ignore: Silent tracks"))
BoolOption('setting', 'completeness_ignore_videos', False, title=N_("Completeness ignore: Video tracks"))
BoolOption('setting', 'ignore_hidden_files', False, title=N_("Ignore hidden files"))
TextOption('setting', 'ignore_regex', '', title=N_("Ignore file paths (regular expression)"))
IntOption('setting', 'ignore_track_duration_difference_under', 2, title=N_("Allowed track difference (seconds)"))
IntOption(
    'setting',
    'query_limit',
    DEFAULT_QUERY_LIMIT,
    title=N_("Maximum MusicBrainz query items"),
)
BoolOption('setting', 'recursively_add_files', True, title=N_("Include sub-folders when adding files"))

# picard/ui/options/cdlookup.py
# CD Lookup
TextOption('setting', 'cd_lookup_device', ','.join(DEFAULT_DRIVES))

# picard/ui/options/cover.py
# Cover Art
ListOption('setting', 'ca_providers', DEFAULT_CA_PROVIDERS, title=N_("Cover art providers"))
TextOption('setting', 'cover_image_filename', DEFAULT_COVER_IMAGE_FILENAME, title=N_("File name for images"))
BoolOption('setting', 'embed_only_one_front_image', True, title=N_("Embed only a single front image"))
BoolOption('setting', 'dont_replace_with_smaller_cover', False, title=N_("Never replace images with smaller ones"))
BoolOption('setting', 'dont_replace_cover_of_types', False, title=N_("Never replace images of selected types"))
ListOption(
    'setting',
    'dont_replace_included_types',
    DEFAULT_CA_NEVER_REPLACE_TYPE_INCLUDE,
    title=N_("Never replace images of these types"),
)
ListOption(
    'setting',
    'dont_replace_excluded_types',
    DEFAULT_CA_NEVER_REPLACE_TYPE_EXCLUDE,
    title=N_("Always replace images of these types"),
)
BoolOption(
    'setting',
    'image_type_as_filename',
    False,
    title=N_("Primary image type as the file name"),
)
BoolOption('setting', 'save_images_overwrite', False, title=N_("Overwrite existing image files"))
BoolOption('setting', 'save_images_to_files', False, title=N_("Save images as separate files"))
BoolOption('setting', 'save_images_to_tags', True, title=N_("Embed images into tags"))
BoolOption('setting', 'save_only_one_front_image', False, title=N_("Save only one front image"))
BoolOption('setting', 'show_cover_art_details', False, title=N_("Show cover art details in view"))
BoolOption('setting', 'show_cover_art_details_type', False, title=N_("Show cover art type"))
BoolOption('setting', 'show_cover_art_details_filesize', True, title=N_("Show cover art file size"))
BoolOption('setting', 'show_cover_art_details_dimensions', True, title=N_("Show cover art dimensions"))
BoolOption('setting', 'show_cover_art_details_mimetype', True, title=N_("Show cover art MIME type"))

# picard/ui/options/cover_processing.py
# Cover Art Image Processing
BoolOption('setting', 'filter_cover_by_size', False, title=N_("Discard small images"))
IntOption('setting', 'cover_minimum_width', DEFAULT_COVER_MIN_SIZE, title=N_("Minimum image width"))
IntOption('setting', 'cover_minimum_height', DEFAULT_COVER_MIN_SIZE, title=N_("Minimum image height"))
BoolOption('setting', 'cover_tags_enlarge', False, title=N_("Allow enlarging tag images"))
BoolOption('setting', 'cover_tags_resize', False, title=N_("Allow resizing tag images"))
IntOption('setting', 'cover_tags_resize_target_width', DEFAULT_COVER_MAX_SIZE, title=N_("Resized tag image width"))
IntOption('setting', 'cover_tags_resize_target_height', DEFAULT_COVER_MAX_SIZE, title=N_("Resized tag image height"))
IntOption('setting', 'cover_tags_resize_mode', DEFAULT_COVER_RESIZE_MODE, title=N_("Tag image resize mode"))
BoolOption('setting', 'cover_tags_convert_images', False, title=N_("Convert tag image format"))
Option('setting', 'cover_tags_convert_to_format', DEFAULT_COVER_CONVERTING_FORMAT, title=N_("New tag image format"))
BoolOption('setting', 'cover_file_enlarge', False, title=N_("Allow enlarging file images"))
BoolOption('setting', 'cover_file_resize', False, title=N_("Allow resizing file images"))
IntOption('setting', 'cover_file_resize_target_width', DEFAULT_COVER_MAX_SIZE, title=N_("Resized file image width"))
IntOption('setting', 'cover_file_resize_target_height', DEFAULT_COVER_MAX_SIZE, title=N_("Resized file image height"))
IntOption('setting', 'cover_file_resize_mode', DEFAULT_COVER_RESIZE_MODE, title=N_("File image resize mode"))
BoolOption('setting', 'cover_file_convert_images', False, title=N_("Convert file image format"))
Option('setting', 'cover_file_convert_to_format', DEFAULT_COVER_CONVERTING_FORMAT, title=N_("New file image format"))
IntOption('setting', 'cover_image_quality', DEFAULT_COVER_IMAGE_QUALITY, title=N_("Format conversion quality"))

# picard/ui/options/dialog.py
# Attached Profiles
TextOption('persist', 'options_last_active_page', '')
ListOption('persist', 'options_pages_tree_state', [])

# picard/ui/options/fingerprinting.py
# Fingerprinting
TextOption('setting', 'acoustid_apikey', '')
TextOption('setting', 'acoustid_fpcalc', '')
TextOption('setting', 'fingerprinting_system', 'acoustid', title=N_('Use AcoustID fingerprinting'))
IntOption('setting', 'fpcalc_threads', DEFAULT_FPCALC_THREADS)
BoolOption('setting', 'ignore_existing_acoustid_fingerprints', False)
BoolOption('setting', 'save_acoustid_fingerprints', False, title=N_('Save AcoustID fingerprints'))

# picard/ui/options/general.py
# General
IntOption('persist', 'last_update_check', 0)
TextOption('persist', 'oauth_access_token', '')
IntOption('persist', 'oauth_access_token_expires', 0)
TextOption('persist', 'oauth_refresh_token', '')
TextOption('persist', 'oauth_refresh_token_scopes', '')
TextOption('persist', 'oauth_username', '')
BoolOption('setting', 'analyze_new_files', False, title=N_("Automatically scan all new files"))
BoolOption('setting', 'check_rtd_updates', False, title=N_("Check for documentation updates"))
BoolOption('setting', 'check_for_plugin_updates', False, title=N_("Check for plugin updates"))
BoolOption('setting', 'check_for_updates', True, title=N_("Check for program updates"))
BoolOption('setting', 'cluster_new_files', False, title=N_("Automatically cluster all new files"))
BoolOption('setting', 'ignore_file_mbids', False, title=N_("Ignore MBIDs when loading new files"))
TextOption('setting', 'server_host', MUSICBRAINZ_SERVERS[0], title=N_("Server address"))
IntOption('setting', 'server_port', 443, title=N_("Port"))
IntOption('setting', 'update_check_days', 7, title=N_("Days between update checks"))
IntOption('setting', 'update_level', DEFAULT_PROGRAM_UPDATE_LEVEL, title=N_("Update types to check"))
BoolOption('setting', 'use_server_for_submission', False, title=N_("Submit to configured server"))

# picard/ui/options/genres.py
# Genres
BoolOption('setting', 'artists_genres', False, title=N_("Use album artist genres"))
BoolOption('setting', 'folksonomy_tags', False, title=N_("Use folksonomy tags as genre"))
TextOption(
    'setting', 'genres_filter', '-seen live\n-favorites\n-fixme\n-owned', title=N_("Genres to include or exclude")
)
TextOption('setting', 'join_genres', '', title=N_("Join multiple genres with"))
IntOption('setting', 'max_genres', 5, title=N_("Maximum number of genres"))
IntOption('setting', 'min_genre_usage', 90, title=N_("Minimal genre usage"))
BoolOption('setting', 'only_my_genres', False, title=N_("Use only my genres"))
BoolOption('setting', 'use_genres', False, title=N_("Use genres from MusicBrainz"))

# picard/ui/options/interface.py
# User Interface
BoolOption('setting', 'allow_multi_dirs_selection', False, title=N_("Allow selecting multiple directories"))
BoolOption('setting', 'builtin_search', True, title=N_("Use builtin search (not browser)"))
BoolOption(
    'setting',
    'filebrowser_horizontal_autoscroll',
    True,
    title=N_("Adjust horizontal position in file browser"),
)
BoolOption('setting', 'file_save_warning', True, title=N_("Confirm when saving"))
TextOption('setting', 'load_image_behavior', 'append')
BoolOption('setting', 'quit_confirmation', True, title=N_("Confirm quit if unsaved changes"))
BoolOption('setting', 'show_menu_icons', DEFAULT_SHOW_MENU_ICONS, title=N_("Show icons in menus"))
BoolOption('setting', 'show_new_user_dialog', True, title=N_("Show warning when Picard starts"))
BoolOption('setting', 'rtd_updates_ask', True, N_("Show documentation update request"))
BoolOption('setting', 'player_now_playing', True, title=N_('Enable "now playing" notifications'))
BoolOption('setting', 'starting_directory', False, title=N_("Begin browsing in a specific directory"))
TextOption('setting', 'starting_directory_path', DEFAULT_STARTING_DIR, title=N_("Directory to begin browsing"))
BoolOption('setting', 'toolbar_show_labels', True, title=N_("Show text labels under icons"))
TextOption('setting', 'ui_language', '', title=N_("User interface language"))
TextOption('setting', 'ui_theme', DEFAULT_THEME_NAME, title=N_("User interface color theme"))
BoolOption('setting', 'use_adv_search_syntax', False, title=N_("Use advanced search syntax"))

# picard/ui/options/interface_colors.py
# Colors
Option(
    'setting',
    'interface_colors',
    InterfaceColors(dark_theme=False).get_colors(),
    title=N_("Colors to use for light theme"),
)
Option(
    'setting',
    'interface_colors_dark',
    InterfaceColors(dark_theme=True).get_colors(),
    title=N_("Colors to use for dark theme"),
)

# picard/ui/options/interface_quick_menu.py
# Quick Menu
ListOption('setting', 'quick_menu_items', DEFAULT_QUICK_MENU_ITEMS, title=N_("Quick Menu options"))

# picard/ui/options/interface_toolbar.py
# Action Toolbar


def make_default_toolbar_layout():
    for e in DEFAULT_TOOLBAR_LAYOUT:
        if e == '-':
            yield e
        else:
            # we want the string matching the MainAction
            yield e.value


ListOption('setting', 'toolbar_layout', list(make_default_toolbar_layout()), title=N_("Layout of the tool bar"))

# picard/ui/options/interface_top_tags.py
# Top Tags
ListOption('setting', 'metadatabox_top_tags', DEFAULT_TOP_TAGS, title=N_("Tags to show at the top"))

# picard/ui/options/maintenance.py
# Maintenance
TextOption('setting', 'autobackup_directory', DEFAULT_AUTOBACKUP_DIRECTORY, title=N_("Configuration backup directory"))

# picard/ui/options/matching.py
# Matching
FloatOption('setting', 'cluster_lookup_threshold', 0.7, title=N_("Similarity for cluster lookups"))
FloatOption('setting', 'file_lookup_threshold', 0.7, title=N_("Similarity for file lookups"))
FloatOption('setting', 'track_matching_threshold', 0.4, title=N_("Similarity for matching files to tracks"))

# picard/ui/options/metadata.py
# Metadata
ListOption('setting', 'artist_locales', ['en'], title=N_("Translation locales"))
BoolOption('setting', 'convert_punctuation', False, title=N_("Convert Unicode punctuation to ASCII"))
BoolOption('setting', 'guess_tracknumber_and_title', True, title=N_("Guess track number and title"))
TextOption('setting', 'nat_name', '[standalone recordings]', title=N_("Standalone recordings name"))
BoolOption('setting', 'release_ars', True, title=N_("Use release relationships"))
ListOption('setting', 'script_exceptions', [], title=N_("Translation script exceptions"))
BoolOption('setting', 'standardize_artists', False, title=N_("Use standardized artist names"))
BoolOption('setting', 'standardize_instruments', True, title=N_("Use standardized instrument credits"))
BoolOption('setting', 'standardize_vocals', True, title=N_("Use standardized vocal credits"))
BoolOption('setting', 'track_ars', False, title=N_("Use track and release relationships"))
# Translation toggles
BoolOption('setting', 'translate_artist_names', False, title=N_("Translate artist names"))
BoolOption('setting', 'translate_album_titles', False, title=N_("Translate album titles"))
BoolOption('setting', 'translate_track_titles', False, title=N_("Translate track titles"))
BoolOption('setting', 'translate_artist_names_script_exception', False, title=N_("Translate artist names exception"))
TextOption('setting', 'va_name', "Various Artists", title=N_("Various Artists name"))
ListOption(
    'setting',
    'disable_date_sanitization_formats',
    [],
    title=N_("Don't sanitize dates for these formats"),
)

# picard/ui/options/network.py
# Network
BoolOption('setting', 'browser_integration', True, title=N_("Browser integration"))
BoolOption('setting', 'browser_integration_localhost_only', True, title=N_("Listen only on localhost"))
IntOption('setting', 'browser_integration_port', 8000, title=N_("Default listening port"))
IntOption('setting', 'network_cache_size_bytes', DEFAULT_CACHE_SIZE_IN_BYTES, title=N_("Network cache size (bytes)"))
IntOption('setting', 'network_transfer_timeout_seconds', 30, title=N_("Request timeout (seconds)"))
TextOption('setting', 'proxy_password', '', title=N_("Proxy password"))
TextOption('setting', 'proxy_server_host', '', title=N_("Proxy server address"))
IntOption('setting', 'proxy_server_port', 80, title=N_("Proxy server port"))
TextOption('setting', 'proxy_type', 'http', title=N_("Type of proxy server"))
TextOption('setting', 'proxy_username', '', title=N_("Proxy username"))
BoolOption('setting', 'use_proxy', False, title=N_("Use a web proxy server"))

# picard/ui/options/plugin_execution_order.py
# Plugin Execution Order
Option('setting', 'plugins3_exec_order', dict(), title=N_("Plugins execution order"))

# picard/ui/options/profiles.py
# Option Profiles
IntOption('persist', 'last_selected_profile_pos', 0)
ListOption('persist', 'profile_settings_tree_expanded_list', [])

# picard/ui/options/ratings.py
# Ratings
BoolOption('setting', 'enable_ratings', False, title=N_("Enable track ratings"))
IntOption('setting', 'rating_steps', 6)
TextOption('setting', 'rating_user_email', 'users@musicbrainz.org', title=N_("Email for saving ratings"))
BoolOption('setting', 'submit_ratings', True, title=N_("Submit ratings to MusicBrainz"))

# picard/ui/options/releases.py
# Preferred Releases
ListOption('setting', 'preferred_release_countries', [], title=N_("Preferred release countries"))
ListOption('setting', 'preferred_release_formats', [], title=N_("Preferred medium formats"))
ListOption('setting', 'release_type_scores', DEFAULT_RELEASE_TYPE_SCORES, title=N_("Preferred release types"))

# picard/ui/options/renaming.py
# File Naming
BoolOption('setting', 'delete_empty_dirs', True, title=N_("Delete empty directories"))
BoolOption('setting', 'move_additional_files', False, title=N_("Move additional files"))
TextOption('setting', 'move_additional_files_pattern', "*.jpg *.png", title=N_("Additional file patterns"))
BoolOption('setting', 'move_files', False, title=N_("Move files"))
TextOption('setting', 'move_files_to', DEFAULT_MUSIC_DIR, title=N_("Destination directory"))
BoolOption('setting', 'move_overwrite_existing_files', False, title=N_("Overwrite existing files"))
BoolOption('setting', 'rename_files', False, title=N_("Rename files"))

# picard/ui/options/renaming_compat.py
# Compatibility
BoolOption('setting', 'ascii_filenames', False, title=N_("Replace non-ASCII characters"))
TextOption(
    'setting',
    'replace_dir_separator',
    DEFAULT_REPLACEMENT,
    title=N_("Directory separators character"),
)
BoolOption('setting', 'replace_spaces_with_underscores', False, title=N_("Replace spaces with underscores"))
Option(
    'setting',
    'win_compat_replacements',
    DEFAULT_WIN_COMPAT_REPLACEMENTS,
    title=N_("Windows compatibility characters"),
)
BoolOption('setting', 'windows_compatibility', True, title=N_("Windows compatibility"))
BoolOption('setting', 'windows_long_paths', DEFAULT_LONG_PATHS, title=N_("Windows long path support"))

# picard/ui/options/scripting.py
# Scripting
IntOption('persist', 'last_selected_script_pos', 0)
BoolOption('setting', 'enable_tagger_scripts', False, title=N_("Enable tagger scripts"))
ListOption('setting', 'list_of_scripts', [], title=N_("Tagger scripts"))

# picard/ui/options/tags.py
# Tags
BoolOption('setting', 'clear_existing_tags', False, title=N_("Clear existing tags"))
BoolOption('setting', 'enable_tag_saving', True, title=N_("Enable saving tags to files"))
BoolOption('setting', 'fix_missing_seekpoints_flac', False, title=N_("Fix missing seekpoints in FLAC"))
ListOption('setting', 'preserved_tags', [], title=N_("Preserved tags list"))
BoolOption('setting', 'preserve_images', False, title=N_("Keep embedded images"))
BoolOption('setting', 'preserve_timestamps', False, title=N_("Preserve timestamps"))
BoolOption('setting', 'remove_ape_from_mp3', False, title=N_("Remove APEv2 tags from MP3"))
BoolOption('setting', 'remove_id3_from_flac', False, title=N_("Remove ID3 tags from FLAC"))

# picard/ui/options/tags_compatibility_aac.py
# AAC
BoolOption('setting', 'aac_save_ape', True, title=N_("Save APEv2 tags to AAC"))
BoolOption('setting', 'remove_ape_from_aac', False, title=N_("Remove APEv2 tags from AAC"))

# picard/ui/options/tags_compatibility_ac3.py
# AC3
BoolOption('setting', 'ac3_save_ape', True, title=N_("Save APEv2 tags to AC3"))
BoolOption('setting', 'remove_ape_from_ac3', False, title=N_("Remove APEv2 tags from AC3"))

# picard/ui/options/tags_compatibility_id3.py
# ID3
TextOption('setting', 'id3v23_join_with', '/', title=N_("ID3v2.3 join character"))
TextOption('setting', 'id3v2_encoding', 'utf-8', title=N_("ID3v2 text encoding"))
BoolOption('setting', 'itunes_compatible_grouping', False, title=N_("iTunes compatible grouping / work"))
BoolOption('setting', 'write_id3v1', True, title=N_("Write ID3v1 tags"))
BoolOption('setting', 'write_id3v23', False, title=N_("ID3v2 version to write"))

# picard/ui/options/tags_compatibility_wave.py
# WAVE
BoolOption('setting', 'remove_wave_riff_info', False, title=N_("Remove RIFF INFO tags from WAVE"))
TextOption('setting', 'wave_riff_info_encoding', 'windows-1252', title=N_("RIFF INFO text encoding"))
BoolOption('setting', 'write_wave_riff_info', True, title=N_("Write RIFF INFO tags to WAVE"))

# picard/ui/scripteditor.py
# File naming script editor Script Details
BoolOption('persist', 'script_editor_show_documentation', False)
Option('setting', 'file_renaming_scripts', {})
TextOption('setting', 'selected_file_naming_script_id', '', title=N_("Selected file naming script"))

# picard/ui/options/sessions.py
# Sessions
BoolOption(
    'setting',
    'session_safe_restore',
    True,
    title=N_("No auto-matching on load"),
)
BoolOption(
    'setting',
    'session_load_last_on_startup',
    False,
    title=N_("Start with last saved session"),
)
IntOption(
    'setting',
    'session_autosave_interval_min',
    0,
    title=N_("Auto-save interval"),
)
BoolOption(
    'setting',
    'session_backup_on_crash',
    True,
    title=N_("Backup session on unexpected exit"),
)
BoolOption(
    'setting',
    'session_include_mb_data',
    True,
    title=N_("Include MusicBrainz data"),
)
BoolOption(
    'setting',
    'session_no_mb_requests_on_load',
    True,
    title=N_("No MusicBrainz requests on restore"),
)
TextOption(
    'setting',
    'session_folder_path',
    '',
    title=N_("Sessions directory"),
)

# picard/ui/searchdialog/album.py
#
Option('persist', 'albumsearchdialog_header_state', QtCore.QByteArray())

# picard/ui/searchdialog/artist.py
#
Option('persist', 'artistsearchdialog_header_state', QtCore.QByteArray())

# picard/ui/searchdialog/track.py
#
Option('persist', 'tracksearchdialog_header_state', QtCore.QByteArray())

# picard/ui/tagsfromfilenames.py
#
TextOption('persist', 'tags_from_filenames_format', '')

# picard/ui/widgets/scripttextedit.py
#
BoolOption('persist', 'script_editor_tooltips', True)
BoolOption('persist', 'script_editor_wordwrap', False)

# picard/plugin3/manager.py
#
Option('setting', 'plugins3_metadata', {})
ListOption('setting', 'plugins3_enabled_plugins', [])
ListOption('persist', 'plugins3_do_not_update', [], title=N_("Plugins to exclude from updates"))
Option('persist', 'plugins3_updates', {})

# picard/ui/itemviews/custom_columns
#
ListOption('setting', 'custom_columns', [])


def init_options():
    pass


def get_option_title(name):
    key = ('setting', name)
    if key not in Option.registry:
        return None
    title = Option.registry[key].title
    if title:
        return title
    return N_('No title for setting "%s"') % name

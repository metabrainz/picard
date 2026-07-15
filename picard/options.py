# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Laurent Monin
# Copyright (C) 2025-2026 Philipp Wolfer
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


from enum import Enum

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
    DEFAULT_CA_NEVER_REPLACE_TYPES,
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
    DEFAULT_LOG_LEVEL,
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


# Note: When adding an option:
#
#   1. Add it to the appropriate section below.
#      If using a default value shared elsewhere, add a `DEFAULT_` constant
#      to `const/defaults.py` and import it here.
#
#   2. If the option can be overridden in user profiles, set:
#      - `title=N_("...")` for display in the Profiles option page
#      - `in_profile=True` to explicitly opt in
#
#   3. If the option is a 'setting' edited in an option page, add it to the
#      page's OPTIONS dict. UI widget highlights for profile display are
#      declared there (not here).
#
# Please, try to keep options ordered by section and name in their own group.


class StandardizeArtistNames(Enum):
    NONE = "none"  # no standardization
    VARIATIONS = "variations"  # standardize variations only
    ALL = "all"  # standardize variations and name changes


# picard/coverart/providers/caa.py
# Cover Art Archive Cover Art Archive: Release
BoolOption('setting', 'caa_approved_only', False, title=N_("Download only approved images"), in_profile=True)
IntOption('setting', 'caa_image_size', DEFAULT_CAA_IMAGE_SIZE, title=N_("Cover art image size"), in_profile=True)
ListOption(
    'setting', 'caa_image_types', DEFAULT_CAA_IMAGE_TYPE_INCLUDE, title=N_("Cover art image types"), in_profile=True
)
ListOption(
    'setting',
    'caa_image_types_to_omit',
    DEFAULT_CAA_IMAGE_TYPE_EXCLUDE,
    title=N_("Cover art image types to omit"),
    in_profile=True,
)
BoolOption('setting', 'caa_restrict_image_types', True, title=N_("Restrict cover art image types"), in_profile=True)

# picard/coverart/providers/local.py
# Local Files
TextOption(
    'setting', 'local_cover_regex', DEFAULT_LOCAL_COVER_ART_REGEX, title=N_("Local cover art regex"), in_profile=True
)

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
ListOption('persist', 'tutorial_steps_shown', [])
BoolOption('persist', 'tutorial_disabled', False)
BoolOption('persist', 'setup_wizard_completed', False)
BoolOption('persist', 'show_plugin_install_warning', True)

# picard/ui/metadatabox.py
#
Option('persist', 'metadatabox_header_state', QtCore.QByteArray())
BoolOption('persist', 'show_changes_first', False)

# picard/ui/options/advanced.py
# Advanced
ListOption('setting', 'compare_ignore_tags', [], title=N_("Tags to ignore for comparison"), in_profile=True)
BoolOption('setting', 'completeness_ignore_data', False, title=N_("Completeness ignore: Data tracks"), in_profile=True)
BoolOption(
    'setting', 'completeness_ignore_pregap', False, title=N_("Completeness ignore: Pregap tracks"), in_profile=True
)
BoolOption(
    'setting', 'completeness_ignore_silence', False, title=N_("Completeness ignore: Silent tracks"), in_profile=True
)
BoolOption(
    'setting', 'completeness_ignore_videos', False, title=N_("Completeness ignore: Video tracks"), in_profile=True
)
BoolOption('setting', 'ignore_hidden_files', False, title=N_("Ignore hidden files"), in_profile=True)
TextOption('setting', 'ignore_regex', '', title=N_("Ignore file paths (regular expression)"), in_profile=True)
IntOption(
    'setting',
    'ignore_track_duration_difference_under',
    2,
    title=N_("Allowed track difference (seconds)"),
    in_profile=True,
)
IntOption(
    'setting',
    'query_limit',
    DEFAULT_QUERY_LIMIT,
    title=N_("Maximum MusicBrainz query items"),
    in_profile=True,
)
BoolOption('setting', 'recursively_add_files', True, title=N_("Include sub-folders when adding files"), in_profile=True)

# picard/ui/options/cdlookup.py
# CD Lookup
TextOption('setting', 'cd_lookup_device', ','.join(DEFAULT_DRIVES), title=N_("CD lookup device"), in_profile=True)

# picard/ui/options/cover.py
# Cover Art
ListOption('setting', 'ca_providers', DEFAULT_CA_PROVIDERS, title=N_("Cover art providers"), in_profile=True)
TextOption(
    'setting', 'cover_image_filename', DEFAULT_COVER_IMAGE_FILENAME, title=N_("File name for images"), in_profile=True
)
BoolOption('setting', 'embed_only_one_front_image', True, title=N_("Embed only a single front image"), in_profile=True)
BoolOption(
    'setting',
    'dont_replace_with_smaller_cover',
    False,
    title=N_("Never replace images with smaller ones"),
    in_profile=True,
)
BoolOption(
    'setting', 'dont_replace_cover_of_types', False, title=N_("Never replace images of selected types"), in_profile=True
)
ListOption(
    'setting',
    'dont_replace_included_types',
    DEFAULT_CA_NEVER_REPLACE_TYPES,
    title=N_("Never replace images of these types"),
    in_profile=True,
)
BoolOption(
    'setting',
    'image_type_as_filename',
    False,
    title=N_("Primary image type as the file name"),
    in_profile=True,
)
BoolOption('setting', 'save_images_overwrite', False, title=N_("Overwrite existing image files"), in_profile=True)
BoolOption('setting', 'save_images_to_files', False, title=N_("Save images as separate files"), in_profile=True)
BoolOption('setting', 'save_images_to_tags', True, title=N_("Embed images into tags"), in_profile=True)
BoolOption('setting', 'save_only_one_front_image', False, title=N_("Save only one front image"), in_profile=True)
BoolOption('setting', 'show_cover_art_details', False, title=N_("Show cover art details in view"), in_profile=True)
BoolOption('setting', 'show_cover_art_details_type', False, title=N_("Show cover art type"), in_profile=True)
BoolOption('setting', 'show_cover_art_details_filesize', True, title=N_("Show cover art file size"), in_profile=True)
BoolOption('setting', 'show_cover_art_details_dimensions', True, title=N_("Show cover art dimensions"), in_profile=True)
BoolOption('setting', 'show_cover_art_details_mimetype', True, title=N_("Show cover art MIME type"), in_profile=True)

# picard/ui/options/cover_processing.py
# Cover Art Image Processing
BoolOption('setting', 'filter_cover_by_size', False, title=N_("Discard small images"), in_profile=True)
IntOption('setting', 'cover_minimum_width', DEFAULT_COVER_MIN_SIZE, title=N_("Minimum image width"), in_profile=True)
IntOption('setting', 'cover_minimum_height', DEFAULT_COVER_MIN_SIZE, title=N_("Minimum image height"), in_profile=True)
BoolOption('setting', 'cover_tags_enlarge', False, title=N_("Allow enlarging tag images"), in_profile=True)
BoolOption('setting', 'cover_tags_resize', False, title=N_("Allow resizing tag images"), in_profile=True)
IntOption(
    'setting',
    'cover_tags_resize_target_width',
    DEFAULT_COVER_MAX_SIZE,
    title=N_("Resized tag image width"),
    in_profile=True,
)
IntOption(
    'setting',
    'cover_tags_resize_target_height',
    DEFAULT_COVER_MAX_SIZE,
    title=N_("Resized tag image height"),
    in_profile=True,
)
IntOption(
    'setting', 'cover_tags_resize_mode', DEFAULT_COVER_RESIZE_MODE, title=N_("Tag image resize mode"), in_profile=True
)
BoolOption('setting', 'cover_tags_convert_images', False, title=N_("Convert tag image format"), in_profile=True)
Option(
    'setting',
    'cover_tags_convert_to_format',
    DEFAULT_COVER_CONVERTING_FORMAT,
    title=N_("New tag image format"),
    in_profile=True,
)
BoolOption('setting', 'cover_file_enlarge', False, title=N_("Allow enlarging file images"), in_profile=True)
BoolOption('setting', 'cover_file_resize', False, title=N_("Allow resizing file images"), in_profile=True)
IntOption(
    'setting',
    'cover_file_resize_target_width',
    DEFAULT_COVER_MAX_SIZE,
    title=N_("Resized file image width"),
    in_profile=True,
)
IntOption(
    'setting',
    'cover_file_resize_target_height',
    DEFAULT_COVER_MAX_SIZE,
    title=N_("Resized file image height"),
    in_profile=True,
)
IntOption(
    'setting', 'cover_file_resize_mode', DEFAULT_COVER_RESIZE_MODE, title=N_("File image resize mode"), in_profile=True
)
BoolOption('setting', 'cover_file_convert_images', False, title=N_("Convert file image format"), in_profile=True)
Option(
    'setting',
    'cover_file_convert_to_format',
    DEFAULT_COVER_CONVERTING_FORMAT,
    title=N_("New file image format"),
    in_profile=True,
)
IntOption(
    'setting',
    'cover_image_quality',
    DEFAULT_COVER_IMAGE_QUALITY,
    title=N_("Format conversion quality"),
    in_profile=True,
)

# picard/ui/options/dialog.py
# Attached Profiles
TextOption('persist', 'options_last_active_page', '')
ListOption('persist', 'options_pages_tree_state', [])

# picard/ui/options/fingerprinting.py
# Fingerprinting
TextOption('setting', 'acoustid_apikey', '')
TextOption('setting', 'acoustid_fpcalc', '')
TextOption('setting', 'fingerprinting_system', 'acoustid', title=N_('Use AcoustID fingerprinting'), in_profile=True)
IntOption('setting', 'fpcalc_threads', DEFAULT_FPCALC_THREADS)
BoolOption(
    'setting',
    'ignore_existing_acoustid_fingerprints',
    False,
    title=N_('Ignore existing AcoustID fingerprints'),
    in_profile=True,
)
BoolOption('setting', 'save_acoustid_fingerprints', False, title=N_('Save AcoustID fingerprints'), in_profile=True)

# ISRC submission
BoolOption('setting', 'submit_isrcs', False, title=N_('Submit ISRCs to MusicBrainz'))
BoolOption('setting', 'read_isrcs_from_disc', True, title=N_('Read ISRCs from CD'))

# picard/ui/options/general.py
# General
TextOption('persist', 'oauth_access_token', '')
IntOption('persist', 'oauth_access_token_expires', 0)
TextOption('persist', 'oauth_refresh_token', '')
TextOption('persist', 'oauth_refresh_token_scopes', '')
TextOption('persist', 'oauth_username', '')
BoolOption('setting', 'analyze_new_files', False, title=N_("Automatically scan all new files"), in_profile=True)
BoolOption('setting', 'cluster_new_files', False, title=N_("Automatically cluster all new files"), in_profile=True)
BoolOption('setting', 'ignore_file_mbids', False, title=N_("Ignore MBIDs when loading new files"), in_profile=True)
TextOption('setting', 'server_host', MUSICBRAINZ_SERVERS[0], title=N_("Server address"), in_profile=True)
IntOption('setting', 'server_port', 443, title=N_("Port"), in_profile=True)
BoolOption('setting', 'use_server_for_submission', False, title=N_("Submit to configured server"), in_profile=True)
BoolOption('setting', 'enable_user_collections', True, title=N_("Enable managing user collections"), in_profile=True)

# picard/ui/options/genres.py
# Genres
BoolOption('setting', 'artists_genres', False, title=N_("Use album artist genres"), in_profile=True)
BoolOption('setting', 'folksonomy_tags', False, title=N_("Use folksonomy tags as genre"), in_profile=True)
TextOption(
    'setting',
    'genres_filter',
    '-seen live\n-favorites\n-fixme\n-owned',
    title=N_("Genres to include or exclude"),
    in_profile=True,
)
TextOption('setting', 'join_genres', '', title=N_("Join multiple genres with"), in_profile=True)
IntOption('setting', 'max_genres', 5, title=N_("Maximum number of genres"), in_profile=True)
IntOption('setting', 'min_genre_usage', 90, title=N_("Minimal genre usage"), in_profile=True)
BoolOption('setting', 'only_my_genres', False, title=N_("Use only my genres"), in_profile=True)
BoolOption('setting', 'use_genres', False, title=N_("Use genres from MusicBrainz"), in_profile=True)

# picard/ui/options/interface.py
# User Interface
BoolOption(
    'setting', 'allow_multi_dirs_selection', False, title=N_("Allow selecting multiple directories"), in_profile=True
)
BoolOption('setting', 'builtin_search', True, title=N_("Use builtin search (not browser)"), in_profile=True)
BoolOption(
    'setting',
    'filebrowser_horizontal_autoscroll',
    True,
    title=N_("Adjust horizontal position in file browser"),
    in_profile=True,
)
BoolOption('setting', 'file_save_warning', True, title=N_("Confirm when saving"), in_profile=True)
TextOption('setting', 'load_image_behavior', 'append')
BoolOption('setting', 'quit_confirmation', True, title=N_("Confirm quit if unsaved changes"), in_profile=True)
BoolOption('setting', 'show_menu_icons', DEFAULT_SHOW_MENU_ICONS, title=N_("Show icons in menus"), in_profile=True)
BoolOption('setting', 'show_new_user_dialog', True, title=N_("Show warning when Picard starts"), in_profile=True)
BoolOption('setting', 'starting_directory', False, title=N_("Begin browsing in a specific directory"), in_profile=True)
TextOption(
    'setting',
    'starting_directory_path',
    DEFAULT_STARTING_DIR,
    title=N_("Directory to begin browsing"),
    in_profile=True,
    shareable=False,
)
BoolOption('setting', 'toolbar_show_labels', True, title=N_("Show text labels under icons"), in_profile=True)
TextOption('setting', 'ui_language', '', title=N_("User interface language"))
TextOption('setting', 'ui_theme', DEFAULT_THEME_NAME, title=N_("User interface color theme"))
BoolOption('setting', 'use_adv_search_syntax', False, title=N_("Use advanced search syntax"), in_profile=True)

# picard/ui/options/interface_player.py
# Audio Player
BoolOption('setting', 'player_now_playing', True, title=N_('Enable "now playing" notifications'), in_profile=True)
BoolOption(
    'setting', 'listenbrainz_enabled', False, title=N_('Enable ListenBrainz listen submissions'), in_profile=True
)
BoolOption(
    'setting',
    'listenbrainz_submit_only_tagged',
    True,
    title=N_('Submit only tagged files ListenBrainz'),
    in_profile=True,
)
TextOption('setting', 'listenbrainz_token', '', title=N_('ListenBrainz user token'), in_profile=True, shareable=False)

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
ListOption('setting', 'quick_menu_items', DEFAULT_QUICK_MENU_ITEMS, title=N_("Quick Menu options"), in_profile=True)

# picard/ui/options/interface_toolbar.py
# Action Toolbar


def make_default_toolbar_layout():
    for e in DEFAULT_TOOLBAR_LAYOUT:
        if e == '-':
            yield e
        else:
            # we want the string matching the MainAction
            yield e.value


ListOption(
    'setting',
    'toolbar_layout',
    list(make_default_toolbar_layout()),
    title=N_("Layout of the tool bar"),
    in_profile=True,
)

# picard/ui/options/interface_top_tags.py
# Top Tags
ListOption('setting', 'metadatabox_top_tags', DEFAULT_TOP_TAGS, title=N_("Tags to show at the top"), in_profile=True)

# picard/ui/options/maintenance.py
# Maintenance
TextOption(
    'setting',
    'autobackup_directory',
    DEFAULT_AUTOBACKUP_DIRECTORY,
    title=N_("Configuration backup directory"),
    in_profile=True,
    shareable=False,
)

# picard/ui/options/matching.py
# Matching
FloatOption('setting', 'match_min_similarity', 0.25, title=N_("Minimum similarity"), in_profile=True)
FloatOption('setting', 'match_min_margin', 0.02, title=N_("Minimum margin"), in_profile=True)
FloatOption(
    'setting', 'track_matching_threshold', 0.4, title=N_("Similarity for matching files to tracks"), in_profile=True
)

# picard/ui/options/metadata.py
# Metadata
ListOption('setting', 'translation_locales', ['en'], title=N_("Translation locales"), in_profile=True)
BoolOption('setting', 'convert_punctuation', False, title=N_("Convert Unicode punctuation to ASCII"), in_profile=True)
BoolOption('setting', 'guess_tracknumber_and_title', True, title=N_("Guess track number and title"), in_profile=True)
TextOption('setting', 'nat_name', '[standalone recordings]', title=N_("Standalone recordings name"), in_profile=True)
BoolOption('setting', 'release_ars', True, title=N_("Use release relationships"), in_profile=True)
ListOption('setting', 'script_exceptions', [], title=N_("Translation script exceptions"), in_profile=True)
Option(
    'setting',
    'standardize_artist_names',
    StandardizeArtistNames.VARIATIONS,
    title=N_("Standardize artist names"),
    in_profile=True,
)
BoolOption('setting', 'standardize_instruments', True, title=N_("Use standardized instrument credits"), in_profile=True)
BoolOption('setting', 'standardize_vocals', True, title=N_("Use standardized vocal credits"), in_profile=True)
BoolOption('setting', 'track_ars', False, title=N_("Use track and release relationships"), in_profile=True)
# Translation toggles
BoolOption('setting', 'translate_artist_names', False, title=N_("Translate artist names"), in_profile=True)
BoolOption('setting', 'translate_album_titles', False, title=N_("Translate album titles"), in_profile=True)
BoolOption('setting', 'translate_track_titles', False, title=N_("Translate track titles"), in_profile=True)
BoolOption(
    'setting', 'translate_from_sortname', False, title=N_("Use artist sort name for translation"), in_profile=True
)
BoolOption(
    'setting',
    'translate_artist_names_script_exception',
    False,
    title=N_("Translate artist names exception"),
    in_profile=True,
)
TextOption('setting', 'va_name', "Various Artists", title=N_("Various Artists name"), in_profile=True)
ListOption(
    'setting',
    'disable_date_sanitization_formats',
    [],
    title=N_("Don't sanitize dates for these formats"),
    in_profile=True,
)

# picard/ui/options/network.py
# Network
BoolOption('setting', 'browser_integration', True, title=N_("Browser integration"), in_profile=True)
BoolOption('setting', 'browser_integration_localhost_only', True, title=N_("Listen only on localhost"), in_profile=True)
IntOption('setting', 'browser_integration_port', 8000, title=N_("Default listening port"), in_profile=True)
IntOption(
    'setting',
    'network_cache_size_bytes',
    DEFAULT_CACHE_SIZE_IN_BYTES,
    title=N_("Network cache size (bytes)"),
    in_profile=True,
)
IntOption('setting', 'network_transfer_timeout_seconds', 30, title=N_("Request timeout (seconds)"), in_profile=True)
TextOption('setting', 'proxy_password', '', title=N_("Proxy password"), in_profile=True, shareable=False)
TextOption('setting', 'proxy_server_host', '', title=N_("Proxy server address"), in_profile=True, shareable=False)
IntOption('setting', 'proxy_server_port', 80, title=N_("Proxy server port"), in_profile=True, shareable=False)
TextOption('setting', 'proxy_type', 'http', title=N_("Type of proxy server"), in_profile=True)
TextOption('setting', 'proxy_username', '', title=N_("Proxy username"), in_profile=True, shareable=False)
BoolOption('setting', 'use_proxy', False, title=N_("Use a web proxy server"), in_profile=True)

# picard/ui/options/plugin_execution_order.py
# Plugin Execution Order
Option('setting', 'plugins3_exec_order', dict(), title=N_("Plugins execution order"), in_profile=True)

# picard/ui/options/profiles.py
# Option Profiles
IntOption('persist', 'last_selected_profile_pos', 0)
ListOption('persist', 'profile_settings_tree_expanded_list', [])

# picard/ui/options/ratings.py
# Ratings
BoolOption('setting', 'enable_ratings', False, title=N_("Enable track ratings"), in_profile=True)
IntOption('setting', 'rating_steps', 6)
TextOption(
    'setting', 'rating_user_email', 'users@musicbrainz.org', title=N_("Email for saving ratings"), in_profile=True
)
BoolOption('setting', 'submit_ratings', True, title=N_("Submit ratings to MusicBrainz"), in_profile=True)

# picard/ui/options/releases.py
# Preferred Releases
ListOption('setting', 'preferred_release_countries', [], title=N_("Preferred release countries"), in_profile=True)
ListOption('setting', 'preferred_release_formats', [], title=N_("Preferred medium formats"), in_profile=True)
ListOption(
    'setting', 'release_type_scores', DEFAULT_RELEASE_TYPE_SCORES, title=N_("Preferred release types"), in_profile=True
)

# picard/ui/options/renaming.py
# File Naming
BoolOption('setting', 'delete_empty_dirs', True, title=N_("Delete empty directories"), in_profile=True)
BoolOption('setting', 'move_additional_files', False, title=N_("Move additional files"), in_profile=True)
TextOption(
    'setting', 'move_additional_files_pattern', "*.jpg *.png", title=N_("Additional file patterns"), in_profile=True
)
BoolOption('setting', 'move_files', False, title=N_("Move files"), in_profile=True)
TextOption(
    'setting', 'move_files_to', DEFAULT_MUSIC_DIR, title=N_("Destination directory"), in_profile=True, shareable=False
)
BoolOption('setting', 'move_overwrite_existing_files', False, title=N_("Overwrite existing files"), in_profile=True)
BoolOption('setting', 'rename_files', False, title=N_("Rename files"), in_profile=True)

# picard/ui/options/renaming_compat.py
# Compatibility
BoolOption('setting', 'ascii_filenames', False, title=N_("Replace non-ASCII characters"), in_profile=True)
TextOption(
    'setting',
    'replace_dir_separator',
    DEFAULT_REPLACEMENT,
    title=N_("Directory separators character"),
    in_profile=True,
)
BoolOption(
    'setting', 'replace_spaces_with_underscores', False, title=N_("Replace spaces with underscores"), in_profile=True
)
Option(
    'setting',
    'win_compat_replacements',
    DEFAULT_WIN_COMPAT_REPLACEMENTS,
    title=N_("Windows compatibility characters"),
    in_profile=True,
)
BoolOption('setting', 'windows_compatibility', True, title=N_("Windows compatibility"), in_profile=True)
BoolOption(
    'setting',
    'windows_long_paths',
    DEFAULT_LONG_PATHS,
    title=N_("Windows long path support"),
    in_profile=True,
    shareable=False,
)

# picard/ui/options/scripting.py
# Scripting
IntOption('persist', 'last_selected_script_pos', 0)
BoolOption('setting', 'enable_tagger_scripts', False, title=N_("Enable tagger scripts"), in_profile=True)
ListOption('setting', 'list_of_scripts', [], title=N_("Tagger scripts"), in_profile=True)

# picard/ui/options/startup.py
# Startup
IntOption('persist', 'last_update_check', 0)
BoolOption('setting', 'check_rtd_updates', False, title=N_("Check for documentation updates"), in_profile=True)
BoolOption('setting', 'check_for_plugin_updates', False, title=N_("Check for plugin updates"), in_profile=True)
BoolOption('setting', 'check_for_updates', False, title=N_("Check for program updates"), in_profile=True)
IntOption('setting', 'update_check_days', 7, title=N_("Days between update checks"), in_profile=True)
IntOption('setting', 'update_level', DEFAULT_PROGRAM_UPDATE_LEVEL, title=N_("Update types to check"), in_profile=True)
IntOption('setting', 'log_verbosity', DEFAULT_LOG_LEVEL, title=N_("Log verbosity level"), in_profile=True)


# picard/ui/options/tags.py
# Tags
BoolOption('setting', 'clear_existing_tags', False, title=N_("Clear existing tags"), in_profile=True)
BoolOption('setting', 'enable_tag_saving', True, title=N_("Save tags to files"), in_profile=True)
BoolOption('setting', 'fix_missing_seekpoints_flac', False, title=N_("Fix missing seekpoints in FLAC"), in_profile=True)
ListOption('setting', 'preserved_tags', [], title=N_("Preserved tags list"), in_profile=True)
BoolOption('setting', 'preserve_images', False, title=N_("Keep embedded images"), in_profile=True)
BoolOption('setting', 'preserve_timestamps', False, title=N_("Preserve timestamps"), in_profile=True)
BoolOption('setting', 'remove_ape_from_mp3', False, title=N_("Remove APEv2 tags from MP3"), in_profile=True)
BoolOption('setting', 'remove_id3_from_flac', False, title=N_("Remove ID3 tags from FLAC"), in_profile=True)

# picard/ui/options/tags_compatibility_aac.py
# AAC
BoolOption('setting', 'aac_save_ape', True, title=N_("Save APEv2 tags to AAC"), in_profile=True)
BoolOption('setting', 'remove_ape_from_aac', False, title=N_("Remove APEv2 tags from AAC"), in_profile=True)

# picard/ui/options/tags_compatibility_ac3.py
# AC3
BoolOption('setting', 'ac3_save_ape', True, title=N_("Save APEv2 tags to AC3"), in_profile=True)
BoolOption('setting', 'remove_ape_from_ac3', False, title=N_("Remove APEv2 tags from AC3"), in_profile=True)

# picard/ui/options/tags_compatibility_id3.py
# ID3
TextOption('setting', 'id3v23_join_with', '/', title=N_("ID3v2.3 join character"), in_profile=True)
TextOption('setting', 'id3v2_encoding', 'utf-8', title=N_("ID3v2 text encoding"), in_profile=True)
BoolOption(
    'setting', 'itunes_compatible_grouping', False, title=N_("iTunes compatible grouping / work"), in_profile=True
)
BoolOption('setting', 'write_id3v1', True, title=N_("Write ID3v1 tags"), in_profile=True)
BoolOption('setting', 'write_id3v23', False, title=N_("ID3v2 version to write"), in_profile=True)

# picard/ui/options/tags_compatibility_wave.py
# WAVE
BoolOption('setting', 'remove_wave_riff_info', False, title=N_("Remove RIFF INFO tags from WAVE"), in_profile=True)
TextOption('setting', 'wave_riff_info_encoding', 'windows-1252', title=N_("RIFF INFO text encoding"), in_profile=True)
BoolOption('setting', 'write_wave_riff_info', True, title=N_("Write RIFF INFO tags to WAVE"), in_profile=True)

# picard/ui/scripteditor.py
# File naming script editor Script Details
BoolOption('persist', 'script_editor_show_documentation', False)
Option('setting', 'file_renaming_scripts', {})
TextOption('setting', 'active_file_naming_script_id', '', title=N_("Active file naming script"), in_profile=True)

# picard/ui/options/sessions.py
# Sessions
BoolOption(
    'setting',
    'session_safe_restore',
    True,
    title=N_("No auto-matching on load"),
    in_profile=True,
)
BoolOption(
    'setting',
    'session_load_last_on_startup',
    False,
    title=N_("Start with last saved session"),
    in_profile=True,
)
IntOption(
    'setting',
    'session_autosave_interval_min',
    0,
    title=N_("Auto-save interval"),
    in_profile=True,
)
BoolOption(
    'setting',
    'session_backup_on_crash',
    True,
    title=N_("Backup session on unexpected exit"),
    in_profile=True,
)
BoolOption(
    'setting',
    'session_include_mb_data',
    True,
    title=N_("Include MusicBrainz data"),
    in_profile=True,
)
BoolOption(
    'setting',
    'session_no_mb_requests_on_load',
    True,
    title=N_("No MusicBrainz requests on restore"),
    in_profile=True,
)
TextOption(
    'setting',
    'session_folder_path',
    '',
    title=N_("Sessions directory"),
    in_profile=True,
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
    return Option.registry[key].title or name

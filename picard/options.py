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


# Note: The following are the options used in Picard. When adding a new option,
#       please make sure to do the following:
#
#   1. The option is added to the appropriate section below.  If it's using a
#      default value that may be used elsewhere, a constant starting with `DEFAULT_`
#      can be added to `const/defaults.py` and imported here.
#
#   2. If the option is a 'setting' which is edited in one of the option pages,
#      then the `page` parameter of the option must be set to the `NAME` constant
#      of the OptionsPage subclass in which the setting is edited.
#
#      Registering a setting allows it to be reset to the default when the user
#      asks for it on the corresponding option page.
#
#   3. If the option is a 'setting' that may be included in the user's option profiles,
#      the `title` parameter of the option must be set to a string briefly describing
#      the setting, using the `N_` function for translation.  The translated title will
#      be displayed in the Profiles option page.
#
#      If the `title` parameter is set for an option, the option will be included in
#      the list of options that can be added to an option profile.
#
#   4. If the option is a 'setting' that may be included in the user's option profiles,
#      the `highlights` parameter of the option should be set to a list of widget names
#      associated with the option on the specified option page.  This allows the UI
#      elements to be highlighted when the option is part of an active option profile.
#
#      The `highlights` parameter is ignored if the `title` parameter is not set, so it
#      is not necessary to set it for options that are not included in option profiles.
#
#
# Please, try to keep options ordered by section and name in their own group.


# picard/coverart/providers/caa.py
# Cover Art Archive Cover Art Archive: Release
BoolOption(
    'setting',
    'caa_approved_only',
    False,
    page='provider_caa',
    title=N_("Only include approved images"),
    highlights=['cb_approved_only'],
)
IntOption(
    'setting',
    'caa_image_size',
    DEFAULT_CAA_IMAGE_SIZE,
    page='provider_caa',
    title=N_("Image size"),
    highlights=['cb_image_size', 'label'],
)
ListOption(
    'setting',
    'caa_image_types',
    DEFAULT_CAA_IMAGE_TYPE_INCLUDE,
    page='provider_caa',
    title=N_("Image types"),
)
ListOption(
    'setting',
    'caa_image_types_to_omit',
    DEFAULT_CAA_IMAGE_TYPE_EXCLUDE,
    page='provider_caa',
    title=N_("Image types to omit"),
)
BoolOption(
    'setting',
    'caa_restrict_image_types',
    True,
    page='provider_caa',
    title=N_("Restrict image types"),
    highlights=['restrict_images_types'],
)

# picard/coverart/providers/local.py
# Local Files
TextOption(
    'setting',
    'local_cover_regex',
    DEFAULT_LOCAL_COVER_ART_REGEX,
    page='provider_local',
    title=N_("Local cover art file name regular expression"),
    highlights=['local_cover_regex_edit'],
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
ListOption(
    'setting',
    'compare_ignore_tags',
    [],
    page='advanced',
    title=N_("Tags to ignore for comparison"),
    highlights=['groupBox_ignore_tags'],
)
BoolOption(
    'setting',
    'completeness_ignore_data',
    False,
    page='advanced',
    title=N_("Completeness ignore: Data tracks"),
    highlights=['completeness_ignore_data'],
)
BoolOption(
    'setting',
    'completeness_ignore_pregap',
    False,
    page='advanced',
    title=N_("Completeness ignore: Pregap tracks"),
    highlights=['completeness_ignore_pregap'],
)
BoolOption(
    'setting',
    'completeness_ignore_silence',
    False,
    page='advanced',
    title=N_("Completeness ignore: Silent tracks"),
    highlights=['completeness_ignore_silence'],
)
BoolOption(
    'setting',
    'completeness_ignore_videos',
    False,
    page='advanced',
    title=N_("Completeness ignore: Video tracks"),
    highlights=['completeness_ignore_videos'],
)
BoolOption(
    'setting',
    'ignore_hidden_files',
    False,
    page='advanced',
    title=N_("Ignore hidden files"),
    highlights=['ignore_hidden_files'],
)
TextOption(
    'setting',
    'ignore_regex',
    '',
    page='advanced',
    title=N_("Ignore file paths (regular expression)"),
    highlights=['ignore_regex'],
)
IntOption(
    'setting',
    'ignore_track_duration_difference_under',
    2,
    page='advanced',
    title=N_("Allowed track difference (seconds)"),
    highlights=['ignore_track_duration_difference_under', 'label_track_duration_diff'],
)
IntOption(
    'setting',
    'query_limit',
    DEFAULT_QUERY_LIMIT,
    page='advanced',
    title=N_("Maximum MusicBrainz query items"),
    highlights=['query_limit', 'label_query_limit'],
)
BoolOption(
    'setting',
    'recursively_add_files',
    True,
    page='advanced',
    title=N_("Include sub-folders when adding files"),
    highlights=['recursively_add_files'],
)

# picard/ui/options/cdlookup.py
# CD Lookup
TextOption(
    'setting',
    'cd_lookup_device',
    ','.join(DEFAULT_DRIVES),
    page='cdlookup',
)

# picard/ui/options/cover.py
# Cover Art
ListOption(
    'setting',
    'ca_providers',
    DEFAULT_CA_PROVIDERS,
    page='cover',
    title=N_("Cover art providers"),
    highlights=['ca_providers_list'],
)
TextOption(
    'setting',
    'cover_image_filename',
    DEFAULT_COVER_IMAGE_FILENAME,
    page='cover',
    title=N_("File name for images"),
    highlights=['cover_image_filename'],
)
BoolOption(
    'setting',
    'embed_only_one_front_image',
    True,
    page='cover',
    title=N_("Embed only a single front image"),
    highlights=['cb_embed_front_only'],
)
BoolOption(
    'setting',
    'dont_replace_with_smaller_cover',
    False,
    page='cover',
    title=N_("Never replace images with smaller ones"),
    highlights=['cb_dont_replace_with_smaller'],
)
BoolOption(
    'setting',
    'dont_replace_cover_of_types',
    False,
    page='cover',
    title=N_("Never replace images of selected types"),
    highlights=['cb_never_replace_types'],
)
ListOption(
    'setting',
    'dont_replace_included_types',
    DEFAULT_CA_NEVER_REPLACE_TYPES,
    page='cover',
    title=N_("Never replace images of these types"),
    highlights=['cb_never_replace_types'],
)
BoolOption(
    'setting',
    'image_type_as_filename',
    False,
    page='cover',
    title=N_("Primary image type as the file name"),
    highlights=['image_type_as_filename'],
)
BoolOption(
    'setting',
    'save_images_overwrite',
    False,
    page='cover',
    title=N_("Overwrite existing image files"),
    highlights=['save_images_overwrite'],
)
BoolOption(
    'setting',
    'save_images_to_files',
    False,
    page='cover',
    title=N_("Save images as separate files"),
    highlights=['save_images_to_files'],
)
BoolOption(
    'setting',
    'save_images_to_tags',
    True,
    page='cover',
    title=N_("Embed images into tags"),
    highlights=['save_images_to_tags'],
)
BoolOption(
    'setting',
    'save_only_one_front_image',
    False,
    page='cover',
    title=N_("Save only one front image"),
    highlights=['save_only_one_front_image'],
)

# picard/ui/options/interface_cover_art_box.py
# Cover Art Box
BoolOption(
    'setting',
    'show_cover_art_details',
    False,
    page='interface_cover_art_box',
    title=N_("Show cover art details in view"),
    highlights=['cb_show_cover_art_details'],
)
BoolOption(
    'setting',
    'show_cover_art_details_type',
    False,
    page='interface_cover_art_box',
    title=N_("Show cover art type"),
    highlights=['cb_show_cover_art_details_type'],
)
BoolOption(
    'setting',
    'show_cover_art_details_filesize',
    True,
    page='interface_cover_art_box',
    title=N_("Show cover art file size"),
    highlights=['cb_show_cover_art_details_filesize'],
)
BoolOption(
    'setting',
    'show_cover_art_details_dimensions',
    True,
    page='interface_cover_art_box',
    title=N_("Show cover art dimensions"),
    highlights=['cb_show_cover_art_details_dimensions'],
)
BoolOption(
    'setting',
    'show_cover_art_details_mimetype',
    True,
    page='interface_cover_art_box',
    title=N_("Show cover art MIME type"),
    highlights=['cb_show_cover_art_details_mimetype'],
)

# picard/ui/options/cover_processing.py
# Cover Art Image Processing
BoolOption(
    'setting',
    'filter_cover_by_size',
    False,
    page='cover_processing',
    title=N_("Discard small images"),
    highlights=['filtering'],
)
IntOption(
    'setting',
    'cover_minimum_width',
    DEFAULT_COVER_MIN_SIZE,
    page='cover_processing',
    title=N_("Minimum image width"),
    highlights=['filtering_width_label', 'filtering_width_value', 'px_label1'],
)
IntOption(
    'setting',
    'cover_minimum_height',
    DEFAULT_COVER_MIN_SIZE,
    page='cover_processing',
    title=N_("Minimum image height"),
    highlights=['filtering_height_label', 'filtering_height_value', 'px_label2'],
)
BoolOption(
    'setting',
    'cover_tags_enlarge',
    False,
    page='cover_processing',
    title=N_("Allow enlarging tag images"),
    highlights=['tags_scale_up'],
)
BoolOption(
    'setting',
    'cover_tags_resize',
    False,
    page='cover_processing',
    title=N_("Allow resizing tag images"),
    highlights=['tags_scale_down'],
)
IntOption(
    'setting',
    'cover_tags_resize_target_width',
    DEFAULT_COVER_MAX_SIZE,
    page='cover_processing',
    title=N_("Resized tag image width"),
    highlights=['tags_resize_width_label', 'tags_resize_width_value', 'px_label5'],
)
IntOption(
    'setting',
    'cover_tags_resize_target_height',
    DEFAULT_COVER_MAX_SIZE,
    page='cover_processing',
    title=N_("Resized tag image height"),
    highlights=['tags_resize_height_label', 'tags_resize_height_value', 'px_label6'],
)
IntOption(
    'setting',
    'cover_tags_resize_mode',
    DEFAULT_COVER_RESIZE_MODE,
    page='cover_processing',
    title=N_("Tag image resize mode"),
    highlights=['tags_resize_mode'],
)
BoolOption(
    'setting',
    'cover_tags_convert_images',
    False,
    page='cover_processing',
    title=N_("Convert tag image format"),
    highlights=['convert_tags'],
)
Option(
    'setting',
    'cover_tags_convert_to_format',
    DEFAULT_COVER_CONVERTING_FORMAT,
    page='cover_processing',
    title=N_("New tag image format"),
    highlights=['convert_tags_label', 'convert_tags_format'],
)
BoolOption(
    'setting',
    'cover_file_enlarge',
    False,
    page='cover_processing',
    title=N_("Allow enlarging file images"),
    highlights=['file_scale_up'],
)
BoolOption(
    'setting',
    'cover_file_resize',
    False,
    page='cover_processing',
    title=N_("Allow resizing file images"),
    highlights=['file_scale_down'],
)
IntOption(
    'setting',
    'cover_file_resize_target_width',
    DEFAULT_COVER_MAX_SIZE,
    page='cover_processing',
    title=N_("Resized file image width"),
    highlights=['file_resize_width_label', 'file_resize_width_value', 'px_label3'],
)
IntOption(
    'setting',
    'cover_file_resize_target_height',
    DEFAULT_COVER_MAX_SIZE,
    page='cover_processing',
    title=N_("Resized file image height"),
    highlights=['file_resize_height_label', 'file_resize_height_value', 'px_label4'],
)
IntOption(
    'setting',
    'cover_file_resize_mode',
    DEFAULT_COVER_RESIZE_MODE,
    page='cover_processing',
    title=N_("File image resize mode"),
    highlights=['file_resize_mode'],
)
BoolOption(
    'setting',
    'cover_file_convert_images',
    False,
    page='cover_processing',
    title=N_("Convert file image format"),
    highlights=['convert_file'],
)
Option(
    'setting',
    'cover_file_convert_to_format',
    DEFAULT_COVER_CONVERTING_FORMAT,
    page='cover_processing',
    title=N_("New file image format"),
    highlights=['convert_file_label', 'convert_file_format'],
)
IntOption(
    'setting',
    'cover_image_quality',
    DEFAULT_COVER_IMAGE_QUALITY,
    page='cover_processing',
    title=N_("Format conversion quality"),
    highlights=['cover_image_quality_label', 'cover_image_quality_value', 'percent_label'],
)

# picard/ui/options/dialog.py
# Attached Profiles
TextOption('persist', 'options_last_active_page', '')
ListOption('persist', 'options_pages_tree_state', [])

# picard/ui/options/fingerprinting.py
# Fingerprinting
TextOption(
    'setting',
    'acoustid_apikey',
    '',
    page='fingerprinting',
)
TextOption(
    'setting',
    'acoustid_fpcalc',
    '',
    page='fingerprinting',
)
TextOption(
    'setting',
    'fingerprinting_system',
    'acoustid',
    page='fingerprinting',
    title=N_("Fingerprinting system"),
    highlights=['disable_fingerprinting', 'use_acoustid'],
)
IntOption(
    'setting',
    'fpcalc_threads',
    DEFAULT_FPCALC_THREADS,
    page='fingerprinting',
)
BoolOption(
    'setting',
    'ignore_existing_acoustid_fingerprints',
    False,
    page='fingerprinting',
    title=N_("Ignore existing AcoustID fingerprints"),
    highlights=['ignore_existing_acoustid_fingerprints'],
)
BoolOption(
    'setting',
    'save_acoustid_fingerprints',
    False,
    page='fingerprinting',
    title=N_("Save generated fingerprints"),
    highlights=['save_acoustid_fingerprints'],
)

# picard/ui/options/general.py
# General
TextOption('persist', 'oauth_access_token', '')
IntOption('persist', 'oauth_access_token_expires', 0)
TextOption('persist', 'oauth_refresh_token', '')
TextOption('persist', 'oauth_refresh_token_scopes', '')
TextOption('persist', 'oauth_username', '')
BoolOption(
    'setting',
    'analyze_new_files',
    False,
    page='general',
    title=N_("Automatically scan all new files"),
    highlights=['analyze_new_files'],
)
BoolOption(
    'setting',
    'cluster_new_files',
    False,
    page='general',
    title=N_("Automatically cluster all new files"),
    highlights=['cluster_new_files'],
)
BoolOption(
    'setting',
    'ignore_file_mbids',
    False,
    page='general',
    title=N_("Ignore MBIDs when loading new files"),
    highlights=['ignore_file_mbids'],
)
TextOption(
    'setting',
    'server_host',
    MUSICBRAINZ_SERVERS[0],
    page='general',
    title=N_("Server address"),
    highlights=['server_host'],
)
IntOption(
    'setting',
    'server_port',
    443,
    page='general',
    title=N_("Port"),
    highlights=['server_port'],
)
BoolOption(
    'setting',
    'use_server_for_submission',
    False,
    page='general',
    title=N_("Submit to configured server"),
    highlights=['use_server_for_submission'],
)

# picard/ui/options/genres.py
# Genres
BoolOption(
    'setting',
    'artists_genres',
    False,
    page='genres',
    title=N_("Use album artist genres"),
    highlights=['artists_genres'],
)
BoolOption(
    'setting',
    'folksonomy_tags',
    False,
    page='genres',
    title=N_("Use folksonomy tags as genre"),
    highlights=['folksonomy_tags'],
)
TextOption(
    'setting',
    'genres_filter',
    '-seen live\n-favorites\n-fixme\n-owned',
    page='genres',
    title=N_("Genres to include or exclude"),
    highlights=['genres_filter'],
)
TextOption(
    'setting',
    'join_genres',
    '',
    page='genres',
    title=N_("Join multiple genres with"),
    highlights=['join_genres'],
)
IntOption(
    'setting',
    'max_genres',
    5,
    page='genres',
    title=N_("Maximum number of genres"),
    highlights=['max_genres'],
)
IntOption(
    'setting',
    'min_genre_usage',
    90,
    page='genres',
    title=N_("Minimal genre usage"),
    highlights=['min_genre_usage'],
)
BoolOption(
    'setting',
    'only_my_genres',
    False,
    page='genres',
    title=N_("Use only my genres"),
    highlights=['only_my_genres'],
)
BoolOption(
    'setting',
    'use_genres',
    False,
    page='genres',
    title=N_("Use genres from MusicBrainz"),
)

# picard/ui/options/interface.py
# User Interface
BoolOption(
    'setting',
    'allow_multi_dirs_selection',
    False,
    page='interface',
    title=N_("Allow selecting multiple directories"),
    highlights=['allow_multi_dirs_selection'],
)
BoolOption(
    'setting',
    'builtin_search',
    True,
    page='interface',
    title=N_("Use builtin search (not browser)"),
    highlights=['builtin_search'],
)
BoolOption(
    'setting',
    'filebrowser_horizontal_autoscroll',
    True,
    page='interface',
    title=N_("Adjust horizontal position in file browser"),
    highlights=['filebrowser_horizontal_autoscroll'],
)
BoolOption(
    'setting',
    'file_save_warning',
    True,
    page='interface',
    title=N_("Confirm when saving"),
    highlights=['file_save_warning'],
)
TextOption('setting', 'load_image_behavior', 'append')  # Managed in `picard/ui/coverartbox/__init__.py`
BoolOption(
    'setting',
    'quit_confirmation',
    True,
    page='interface',
    title=N_("Confirm quit if unsaved changes"),
    highlights=['quit_confirmation'],
)
BoolOption(
    'setting',
    'rtd_updates_ask',
    True,
    page='interface',
    title=N_("Show documentation update request"),
    highlights=['rtd_updates_ask'],
)
BoolOption(
    'setting',
    'show_menu_icons',
    DEFAULT_SHOW_MENU_ICONS,
    page='interface',
    title=N_("Show icons in menus"),
    highlights=['show_menu_icons'],
)
BoolOption(
    'setting',
    'show_new_user_dialog',
    True,
    page='interface',
    title=N_("Show warning when Picard starts"),
    highlights=['new_user_dialog'],
)
BoolOption(
    'setting',
    'starting_directory',
    False,
    page='interface',
    title=N_("Begin browsing in a specific directory"),
    highlights=['starting_directory'],
)
TextOption(
    'setting',
    'starting_directory_path',
    DEFAULT_STARTING_DIR,
    page='interface',
    title=N_("Directory to begin browsing"),
    highlights=['starting_directory_path'],
)
BoolOption(
    'setting',
    'toolbar_show_labels',
    True,
    page='interface',
    title=N_("Show text labels under icons"),
    highlights=['toolbar_show_labels'],
)
TextOption(
    'setting',
    'ui_language',
    '',
    page='interface',
    title=N_("User interface language"),
    highlights=['ui_language'],
)
TextOption(
    'setting',
    'ui_theme',
    DEFAULT_THEME_NAME,
    page='interface',
    title=N_("User interface color theme"),
    highlights=['ui_theme'],
)
BoolOption(
    'setting',
    'use_adv_search_syntax',
    False,
    page='interface',
    title=N_("Use advanced search syntax"),
    highlights=['use_adv_search_syntax'],
)

# picard/ui/options/player.py
# Audio Player
BoolOption(
    'setting',
    'listenbrainz_enabled',
    False,
    page='player',
    title=N_('Enable ListenBrainz listen submissions'),
    highlights=['listenbrainz_enabled'],
)
BoolOption(
    'setting',
    'listenbrainz_submit_only_tagged',
    True,
    page='player',
    title=N_('Submit only tagged files ListenBrainz'),
    highlights=['listenbrainz_submit_only_tagged'],
)
TextOption(
    'setting',
    'listenbrainz_token',
    '',
    page='player',
    title=N_('ListenBrainz user token'),
    highlights=['listenbrainz_token'],
)
BoolOption(
    'setting',
    'player_now_playing',
    True,
    page='player',
    title=N_('Enable "now playing" notifications'),
    highlights=['player_now_playing'],
)

# picard/ui/options/interface_colors.py
# Colors
Option(
    'setting',
    'interface_colors',
    InterfaceColors(dark_theme=False).get_colors(),
    page='interface_colors',
    title=N_("Colors to use for light theme"),
    highlights=['colors'],
)
Option(
    'setting',
    'interface_colors_dark',
    InterfaceColors(dark_theme=True).get_colors(),
    page='interface_colors',
    title=N_("Colors to use for dark theme"),
    highlights=['colors'],
)

# picard/ui/options/interface_quick_menu.py
# Quick Menu
ListOption(
    'setting',
    'quick_menu_items',
    DEFAULT_QUICK_MENU_ITEMS,
    page='interface_quick_menu',
    title=N_("Quick Menu options"),
    highlights=['quick_menu_items'],
)

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
    page='interface_toolbar',
    title=N_("Layout of the tool bar"),
    highlights=['toolbar_layout_list'],
)

# picard/ui/options/interface_top_tags.py
# Top Tags
ListOption(
    'setting',
    'metadatabox_top_tags',
    DEFAULT_TOP_TAGS,
    page='interface_top_tags',
    title=N_("Tags to show at the top"),
    highlights=['top_tags_groupBox'],
)

# picard/ui/options/maintenance.py
# Maintenance
TextOption(
    'setting',
    'autobackup_directory',
    DEFAULT_AUTOBACKUP_DIRECTORY,
    page='maintenance',
    title=N_("Configuration backup directory"),
    highlights=['autobackup_dir'],
)

# picard/ui/options/matching.py
# Matching
FloatOption(
    'setting',
    'match_min_similarity',
    0.25,
    page='matching',
    title=N_("Minimum similarity"),
    highlights=['match_min_similarity', 'label_min_similarity'],
)
FloatOption(
    'setting',
    'match_min_margin',
    0.02,
    page='matching',
    title=N_("Minimum margin"),
    highlights=['match_min_margin', 'label_min_margin'],
)
FloatOption(
    'setting',
    'track_matching_threshold',
    0.4,
    page='matching',
    title=N_("Similarity for matching files to tracks"),
    highlights=['track_matching_threshold', 'label_track_matching'],
)

# picard/ui/options/metadata.py
# Metadata
BoolOption(
    'setting',
    'convert_punctuation',
    False,
    page='metadata',
    title=N_("Convert Unicode punctuation to ASCII"),
    highlights=['convert_punctuation'],
)
BoolOption(
    'setting',
    'guess_tracknumber_and_title',
    True,
    page='metadata',
    title=N_("Guess track number and title"),
    highlights=['guess_tracknumber_and_title'],
)
TextOption(
    'setting',
    'nat_name',
    '[standalone recordings]',
    page='metadata',
    title=N_("Standalone recordings name"),
    highlights=['nat_name'],
)
BoolOption(
    'setting',
    'release_ars',
    True,
    page='metadata',
    title=N_("Use release relationships"),
    highlights=['release_ars'],
)
ListOption(
    'setting',
    'script_exceptions',
    [],
    page='metadata',
    title=N_("Translation script exceptions"),
    highlights=['selected_scripts'],
)
BoolOption(
    'setting',
    'standardize_artists',
    False,
    page='metadata',
    title=N_("Use standardized artist names"),
    highlights=['standardize_artists'],
)
BoolOption(
    'setting',
    'standardize_instruments',
    True,
    page='metadata',
    title=N_("Use standardized instrument credits"),
    highlights=['standardize_instruments'],
)
BoolOption(
    'setting',
    'standardize_vocals',
    True,
    page='metadata',
    title=N_("Use standardized vocal credits"),
    highlights=['standardize_vocals'],
)
BoolOption(
    'setting',
    'track_ars',
    False,
    page='metadata',
    title=N_("Use track and release relationships"),
    highlights=['track_ars'],
)
# Translation toggles
BoolOption(
    'setting',
    'translate_album_titles',
    False,
    page='metadata',
    title=N_("Translate album titles"),
    highlights=['translate_album_titles'],
)
BoolOption(
    'setting',
    'translate_artist_names',
    False,
    page='metadata',
    title=N_("Translate artist names"),
    highlights=['translate_artist_names'],
)
BoolOption(
    'setting',
    'translate_artist_names_script_exception',
    False,
    page='metadata',
    title=N_("Translate artist names exception"),
    highlights=['translate_artist_names_script_exception'],
)
BoolOption(
    'setting',
    'translate_from_sortname',
    False,
    page='metadata',
    title=N_("Use artist sort name for translation"),
    highlights=['translate_from_sortname'],
)
BoolOption(
    'setting',
    'translate_track_titles',
    False,
    page='metadata',
    title=N_("Translate track titles"),
    highlights=['translate_track_titles'],
)
ListOption(
    'setting',
    'translation_locales',
    ['en'],
    page='metadata',
    title=N_("Translation locales"),
    highlights=['selected_locales'],
)
TextOption(
    'setting',
    'va_name',
    "Various Artists",
    page='metadata',
    title=N_("Various Artists name"),
    highlights=['va_name'],
)

# picard/ui/options/network.py
# Network
BoolOption(
    'setting',
    'browser_integration',
    True,
    page='network',
    title=N_("Browser integration"),
    highlights=['browser_integration'],
)
BoolOption(
    'setting',
    'browser_integration_localhost_only',
    True,
    page='network',
    title=N_("Listen only on localhost"),
    highlights=['browser_integration_localhost_only'],
)
IntOption(
    'setting',
    'browser_integration_port',
    8000,
    page='network',
    title=N_("Default listening port"),
    highlights=['browser_integration_port'],
)
IntOption(
    'setting',
    'network_cache_size_bytes',
    DEFAULT_CACHE_SIZE_IN_BYTES,
    page='network',
    title=N_("Network cache size (bytes)"),
    highlights=['network_cache_size'],
)
IntOption(
    'setting',
    'network_transfer_timeout_seconds',
    30,
    page='network',
    title=N_("Request timeout (seconds)"),
    highlights=['transfer_timeout'],
)
TextOption(
    'setting',
    'proxy_password',
    '',
    page='network',
    title=N_("Proxy password"),
    highlights=['password'],
)
TextOption(
    'setting',
    'proxy_server_host',
    '',
    page='network',
    title=N_("Proxy server address"),
    highlights=['server_host'],
)
IntOption(
    'setting',
    'proxy_server_port',
    80,
    page='network',
    title=N_("Proxy server port"),
    highlights=['server_port'],
)
TextOption(
    'setting',
    'proxy_type',
    'http',
    page='network',
    title=N_("Type of proxy server"),
    highlights=['proxy_type_http'],
)
TextOption(
    'setting',
    'proxy_username',
    '',
    page='network',
    title=N_("Proxy username"),
    highlights=['username'],
)
BoolOption(
    'setting',
    'use_proxy',
    False,
    page='network',
    title=N_("Use a web proxy server"),
    highlights=['web_proxy'],
)

# picard/ui/dialogs/plugin_order_selector.py
# Plugin Execution Order
Option('setting', 'plugins3_exec_order', dict())

# picard/ui/options/profiles.py
# Option Profiles
IntOption('persist', 'last_selected_profile_pos', 0)
ListOption('persist', 'profile_settings_tree_expanded_list', [])

# picard/ui/options/ratings.py
# Ratings
BoolOption(
    'setting',
    'enable_ratings',
    False,
    page='ratings',
    title=N_("Enable track ratings"),
    highlights=['enable_ratings'],
)
TextOption(
    'setting',
    'rating_user_email',
    'users@musicbrainz.org',
    page='ratings',
    title=N_("Email for saving ratings"),
    highlights=['rating_user_email'],
)
BoolOption(
    'setting',
    'submit_ratings',
    True,
    page='ratings',
    title=N_("Submit ratings to MusicBrainz"),
    highlights=['submit_ratings'],
)

# picard/ui/options/releases.py
# Preferred Releases
ListOption(
    'setting',
    'preferred_release_countries',
    [],
    page='releases',
    title=N_("Preferred release countries"),
    highlights=['country_group'],
)
ListOption(
    'setting',
    'preferred_release_formats',
    [],
    page='releases',
    title=N_("Preferred medium formats"),
    highlights=['format_group'],
)
ListOption(
    'setting',
    'release_type_scores',
    DEFAULT_RELEASE_TYPE_SCORES,
    page='releases',
    title=N_("Preferred release types"),
    highlights=['type_group'],
)

# picard/ui/options/renaming.py
# File Naming
TextOption(
    'setting',
    'active_file_naming_script_id',
    '',
    page='filerenaming',
    title=N_("Active file naming script"),
    highlights=['naming_script_selector', 'naming_script_label'],
)
BoolOption(
    'setting',
    'delete_empty_dirs',
    True,
    page='filerenaming',
    title=N_("Delete empty directories"),
    highlights=['delete_empty_dirs'],
)
BoolOption(
    'setting',
    'move_additional_files',
    False,
    page='filerenaming',
    title=N_("Move additional files"),
    highlights=['move_additional_files'],
)
TextOption(
    'setting',
    'move_additional_files_pattern',
    "*.jpg *.png",
    page='filerenaming',
    title=N_("Additional file patterns"),
    highlights=['move_additional_files_pattern'],
)
BoolOption(
    'setting',
    'move_files',
    False,
    page='filerenaming',
    title=N_("Move files"),
    highlights=['move_files'],
)
TextOption(
    'setting',
    'move_files_to',
    DEFAULT_MUSIC_DIR,
    page='filerenaming',
    title=N_("Destination directory"),
    highlights=['move_files_to'],
)
BoolOption(
    'setting',
    'move_overwrite_existing_files',
    False,
    page='filerenaming',
    title=N_("Overwrite existing files"),
    highlights=['move_overwrite_existing_files'],
)
BoolOption(
    'setting',
    'rename_files',
    False,
    page='filerenaming',
    title=N_("Rename files"),
    highlights=['rename_files'],
)

# picard/ui/options/renaming_compat.py
# Compatibility
BoolOption(
    'setting',
    'ascii_filenames',
    False,
    page='filerenaming_compat',
    title=N_("Replace non-ASCII characters"),
    highlights=['ascii_filenames'],
)
TextOption(
    'setting',
    'replace_dir_separator',
    DEFAULT_REPLACEMENT,
    page='filerenaming_compat',
    title=N_("Directory separators character"),
    highlights=['replace_dir_separator'],
)
BoolOption(
    'setting',
    'replace_spaces_with_underscores',
    False,
    page='filerenaming_compat',
    title=N_("Replace spaces with underscores"),
    highlights=['replace_spaces_with_underscores'],
)
Option(
    'setting',
    'win_compat_replacements',
    DEFAULT_WIN_COMPAT_REPLACEMENTS,
    page='filerenaming_compat',
    title=N_("Windows compatibility characters"),
    highlights=['windows_compatibility'],
)
BoolOption(
    'setting',
    'windows_compatibility',
    True,
    page='filerenaming_compat',
    title=N_("Windows compatibility"),
    highlights=['windows_compatibility'],
)
BoolOption(
    'setting',
    'windows_long_paths',
    DEFAULT_LONG_PATHS,
    page='filerenaming_compat',
    title=N_("Windows long path support"),
    highlights=['windows_long_paths'],
)

# picard/ui/options/scripting.py
# Scripting
IntOption('persist', 'last_selected_script_pos', 0)
BoolOption(
    'setting',
    'enable_tagger_scripts',
    False,
    page='scripting',
    title=N_("Enable tagger scripts"),
    highlights=['enable_tagger_scripts'],
)
ListOption(
    'setting',
    'list_of_scripts',
    [],
    page='scripting',
    title=N_("Tagger scripts"),
    highlights=['script_list'],
)

# picard/ui/options/startup.py
# Startup
IntOption('persist', 'last_update_check', 0)
BoolOption(
    'setting',
    'check_for_plugin_updates',
    False,
    page='startup',
    title=N_("Check for plugin updates"),
    highlights=['check_plugin_updates'],
)
BoolOption(
    'setting',
    'check_for_updates',
    True,
    page='startup',
    title=N_("Check for program updates"),
    highlights=['check_for_updates'],
)
BoolOption(
    'setting',
    'check_rtd_updates',
    False,
    page='startup',
    title=N_("Check for documentation updates"),
    highlights=['check_rtd_updates'],
)
IntOption(
    'setting',
    'log_verbosity',
    DEFAULT_LOG_LEVEL,
    page='startup',
    title=N_("Log verbosity level"),
    highlights=['log_verbosity_label', 'starting_log_level'],
)
IntOption(
    'setting',
    'update_check_days',
    7,
    page='startup',
    title=N_("Days between update checks"),
    highlights=['update_check_days'],
)
IntOption(
    'setting',
    'update_level',
    DEFAULT_PROGRAM_UPDATE_LEVEL,
    page='startup',
    title=N_("Update types to check"),
    highlights=['update_level'],
)

# picard/ui/options/tags.py
# Tags
BoolOption(
    'setting',
    'clear_existing_tags',
    False,
    page='tags',
    title=N_("Clear existing tags"),
    highlights=['clear_existing_tags'],
)
ListOption(
    'setting',
    'disable_date_sanitization_formats',
    [],
    page='tags',
    title=N_("Don't sanitize dates for these formats"),
    highlights=['do_not_sanitize_label', 'do_not_sanitize_container'],
)
BoolOption(
    'setting',
    'enable_tag_saving',
    True,
    page='tags',
    title=N_("Save tags to files"),
    highlights=['write_tags'],
)
BoolOption(
    'setting',
    'fix_missing_seekpoints_flac',
    False,
    page='tags',
    title=N_("Fix missing seekpoints in FLAC"),
    highlights=['fix_missing_seekpoints_flac'],
)
BoolOption(
    'setting',
    'preserve_images',
    False,
    page='tags',
    title=N_("Keep embedded images"),
    highlights=['preserve_images'],
)
BoolOption(
    'setting',
    'preserve_timestamps',
    False,
    page='tags',
    title=N_("Preserve timestamps"),
    highlights=['preserve_timestamps'],
)
ListOption(
    'setting',
    'preserved_tags',
    [],
    page='tags',
    title=N_("Preserved tags list"),
    highlights=['preserved_tags', 'preserved_tags_label'],
)
BoolOption(
    'setting',
    'remove_ape_from_mp3',
    False,
    page='tags',
    title=N_("Remove APEv2 tags from MP3"),
    highlights=['remove_ape_from_mp3'],
)
BoolOption(
    'setting',
    'remove_id3_from_flac',
    False,
    page='tags',
    title=N_("Remove ID3 tags from FLAC"),
    highlights=['remove_id3_from_flac'],
)

# picard/ui/options/tags_compatibility_aac.py
# AAC
BoolOption(
    'setting',
    'aac_save_ape',
    True,
    page='tags_compatibility_aac',
    title=N_("Save APEv2 tags to AAC"),
    highlights=['aac_save_ape', 'aac_no_tags'],
)
BoolOption(
    'setting',
    'remove_ape_from_aac',
    False,
    page='tags_compatibility_aac',
    title=N_("Remove APEv2 tags from AAC"),
    highlights=['remove_ape_from_aac'],
)

# picard/ui/options/tags_compatibility_ac3.py
# AC3
BoolOption(
    'setting',
    'ac3_save_ape',
    True,
    page='tags_compatibility_ac3',
    title=N_("Save APEv2 tags to AC3"),
    highlights=['ac3_save_ape', 'ac3_no_tags'],
)
BoolOption(
    'setting',
    'remove_ape_from_ac3',
    False,
    page='tags_compatibility_ac3',
    title=N_("Remove APEv2 tags from AC3"),
    highlights=['remove_ape_from_ac3'],
)

# picard/ui/options/tags_compatibility_id3.py
# ID3
(
    TextOption(
        'setting',
        'id3v23_join_with',
        '/',
        page='tags_compatibility_id3',
        title=N_("ID3v2.3 join character"),
        highlights=['id3v23_join_with'],
    ),
)
TextOption(
    'setting',
    'id3v2_encoding',
    'utf-8',
    page='tags_compatibility_id3',
    title=N_("ID3v2 text encoding"),
    highlights=['enc_utf8', 'enc_utf16', 'enc_iso88591'],
)
BoolOption(
    'setting',
    'itunes_compatible_grouping',
    False,
    page='tags_compatibility_id3',
    title=N_("iTunes compatible grouping / work"),
    highlights=['itunes_compatible_grouping'],
)
BoolOption(
    'setting',
    'write_id3v1',
    True,
    page='tags_compatibility_id3',
    title=N_("Write ID3v1 tags"),
    highlights=['write_id3v1'],
)
BoolOption(
    'setting',
    'write_id3v23',
    False,
    page='tags_compatibility_id3',
    title=N_("ID3v2 version to write"),
    highlights=['write_id3v23', 'write_id3v24'],
)

# picard/ui/options/tags_compatibility_wave.py
# WAVE
BoolOption(
    'setting',
    'remove_wave_riff_info',
    False,
    page='tags_compatibility_wave',
    title=N_("Remove RIFF INFO tags from WAVE"),
    highlights=['remove_wave_riff_info'],
)
TextOption(
    'setting',
    'wave_riff_info_encoding',
    'windows-1252',
    page='tags_compatibility_wave',
    title=N_("RIFF INFO text encoding"),
    highlights=['wave_riff_info_enc_cp1252', 'wave_riff_info_enc_utf8'],
)
BoolOption(
    'setting',
    'write_wave_riff_info',
    True,
    page='tags_compatibility_wave',
    title=N_("Write RIFF INFO tags to WAVE"),
    highlights=['write_wave_riff_info'],
)

# picard/ui/ratingwidget.py
# Rating Widget
IntOption('setting', 'rating_steps', 6)

# picard/ui/scripteditor.py
# File naming script editor Script Details
BoolOption('persist', 'script_editor_show_documentation', False)
Option('setting', 'file_renaming_scripts', {})

# picard/ui/options/sessions.py
# Sessions
IntOption(
    'setting',
    'session_autosave_interval_min',
    0,
    page='sessions',
    title=N_("Auto-save interval"),
    highlights=['autosave_spin', 'autosave_label'],
)
BoolOption(
    'setting',
    'session_backup_on_crash',
    True,
    page='sessions',
    title=N_("Backup session on unexpected exit"),
    highlights=['backup_checkbox'],
)
TextOption(
    'setting',
    'session_folder_path',
    '',
    page='sessions',
    title=N_("Sessions directory"),
    highlights=['folder_path_edit'],
)
BoolOption(
    'setting',
    'session_include_mb_data',
    True,
    page='sessions',
    title=N_("Include MusicBrainz data"),
    highlights=['include_mb_data_checkbox'],
)
BoolOption(
    'setting',
    'session_load_last_on_startup',
    False,
    page='sessions',
    title=N_("Start with last saved session"),
    highlights=['load_last_checkbox'],
)
BoolOption(
    'setting',
    'session_no_mb_requests_on_load',
    True,
    page='sessions',
    title=N_("No MusicBrainz requests on restore"),
    highlights=['no_mb_requests_checkbox'],
)
BoolOption(
    'setting',
    'session_safe_restore',
    True,
    page='sessions',
    title=N_("No auto-matching on load"),
    highlights=['safe_restore_checkbox'],
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
ListOption('persist', 'plugins3_do_not_update', [])
ListOption('setting', 'plugins3_enabled_plugins', [])
Option('setting', 'plugins3_metadata', {})
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

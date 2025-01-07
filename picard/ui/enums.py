# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011-2012, 2014 Lukáš Lalinský
# Copyright (C) 2007 Nikolai Prokoschenko
# Copyright (C) 2008 Gary van der Merwe
# Copyright (C) 2008 Robert Kaye
# Copyright (C) 2008 Will
# Copyright (C) 2008-2010, 2015, 2018-2023 Philipp Wolfer
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009 David Hilton
# Copyright (C) 2011-2012 Chad Wilson
# Copyright (C) 2011-2013, 2015-2017 Wieland Hoffmann
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2013-2014, 2017 Sophist-UK
# Copyright (C) 2013-2024 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2015 samithaj
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Simon Legner
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Frederik “Freso” S. Olesen
# Copyright (C) 2018 Kartik Ohri
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018 virusMac
# Copyright (C) 2018, 2021-2023 Bob Swift
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Petit Minion
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


from enum import (
    Enum,
    unique,
)


# TODO: when Python 3.11 will the lowest version supported move this to StrEnum
# see https://tsak.dev/posts/python-enum/

@unique
class MainAction(str, Enum):
    ABOUT = 'about_action'
    ADD_DIRECTORY = 'add_directory_action'
    ADD_FILES = 'add_files_action'
    ALBUM_OTHER_VERSIONS = 'album_other_versions_action'
    ALBUM_SEARCH = 'album_search_action'
    ANALYZE = 'analyze_action'
    AUTOTAG = 'autotag_action'
    BROWSER_LOOKUP = 'browser_lookup_action'
    CD_LOOKUP = 'cd_lookup_action'
    CHECK_UPDATE = 'check_update_action'
    CLOSE_WINDOW = 'close_window_action'
    CLUSTER = 'cluster_action'
    CUT = 'cut_action'
    DONATE = 'donate_action'
    ENABLE_MOVING = 'enable_moving_action'
    ENABLE_RENAMING = 'enable_renaming_action'
    ENABLE_TAG_SAVING = 'enable_tag_saving_action'
    EXIT = 'exit_action'
    GENERATE_FINGERPRINTS = 'generate_fingerprints_action'
    HELP = 'help_action'
    OPEN_COLLECTION_IN_BROWSER = 'open_collection_in_browser_action'
    OPEN_FOLDER = 'open_folder_action'
    OPTIONS = 'options_action'
    PASTE = 'paste_action'
    PLAY_FILE = 'play_file_action'
    PLAYER_TOOLBAR_TOGGLE = 'player_toolbar_toggle_action'  # defined in MainWindow
    REFRESH = 'refresh_action'
    REMOVE = 'remove_action'
    REPORT_BUG = 'report_bug_action'
    SAVE = 'save_action'
    SEARCH = 'search_action'
    SEARCH_TOOLBAR_TOGGLE = 'search_toolbar_toggle_action'  # defined in MainWindow
    SHOW_COVER_ART = 'show_cover_art_action'
    SHOW_FILE_BROWSER = 'show_file_browser_action'
    SHOW_METADATA_VIEW = 'show_metadata_view_action'
    SHOW_SCRIPT_EDITOR = 'show_script_editor_action'
    SHOW_TOOLBAR = 'show_toolbar_action'
    SIMILAR_ITEMS_SEARCH = 'similar_items_search_action'
    SUBMIT_ACOUSTID = 'submit_acoustid_action'
    SUBMIT_CLUSTER = 'submit_cluster_action'
    SUBMIT_FILE_AS_RECORDING = 'submit_file_as_recording_action'
    SUBMIT_FILE_AS_RELEASE = 'submit_file_as_release_action'
    SUPPORT_FORUM = 'support_forum_action'
    TAGS_FROM_FILENAMES = 'tags_from_filenames_action'
    TRACK_SEARCH = 'track_search_action'
    VIEW_HISTORY = 'view_history_action'
    VIEW_INFO = 'view_info_action'
    VIEW_LOG = 'view_log_action'

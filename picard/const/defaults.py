# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007, 2014, 2016 Lukáš Lalinský
# Copyright (C) 2014, 2019-2022 Philipp Wolfer
# Copyright (C) 2014-2016, 2018-2021, 2024 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Wieland Hoffmann
# Copyright (C) 2016-2017 Frederik “Freso” S. Olesen
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018, 2021, 2023 Bob Swift
# Copyright (C) 2020 RomFouq
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Vladislav Karbovskii
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

import os

from PyQt6 import QtCore
from PyQt6.QtCore import QStandardPaths

from picard import log
from picard.const import (
    CACHE_SIZE_DISPLAY_UNIT,
    RELEASE_PRIMARY_GROUPS,
    RELEASE_SECONDARY_GROUPS,
)
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import N_
from picard.util import system_supports_long_paths
from picard.util.cdrom import discid

from picard.ui.theme import UiTheme


DEFAULT_REPLACEMENT = '_'
DEFAULT_WIN_COMPAT_REPLACEMENTS = {
    '*': DEFAULT_REPLACEMENT,
    ':': DEFAULT_REPLACEMENT,
    '<': DEFAULT_REPLACEMENT,
    '>': DEFAULT_REPLACEMENT,
    '?': DEFAULT_REPLACEMENT,
    '|': DEFAULT_REPLACEMENT,
    '"': DEFAULT_REPLACEMENT,
}

DEFAULT_MUSIC_DIR = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)

DEFAULT_RELEASE_SCORE = 0.5
DEFAULT_RELEASE_TYPE_SCORES = [(g, DEFAULT_RELEASE_SCORE) for g in list(RELEASE_PRIMARY_GROUPS.keys()) + list(RELEASE_SECONDARY_GROUPS.keys())]


DEFAULT_CAA_IMAGE_SIZE = 500
DEFAULT_CAA_IMAGE_TYPE_INCLUDE = ['front']
DEFAULT_CAA_IMAGE_TYPE_EXCLUDE = ['matrix/runout', 'raw/unedited', 'watermark']

DEFAULT_LOCAL_COVER_ART_REGEX = r'^(?:cover|folder|albumart)(.*)\.(?:jpe?g|png|gif|tiff?|webp)$'


DEFAULT_CURRENT_BROWSER_PATH = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
if IS_MACOS:
    def _macos_extend_root_volume_path(path):

        def _macos_find_root_volume():
            try:
                for entry in os.scandir("/Volumes/"):
                    if entry.is_symlink() and os.path.realpath(entry.path) == "/":
                        return entry.path
            except OSError:
                log.warning("Could not detect macOS boot volume", exc_info=True)
            return None

        if not path.startswith("/Volumes/"):
            root_volume = _macos_find_root_volume()
            if root_volume:
                if path.startswith("/"):
                    path = path[1:]
                path = os.path.join(root_volume, path)
        return path

    DEFAULT_CURRENT_BROWSER_PATH = _macos_extend_root_volume_path(DEFAULT_CURRENT_BROWSER_PATH)

# Default query limit
DEFAULT_QUERY_LIMIT = 50

DEFAULT_DRIVES = []
if discid is not None:
    device = discid.get_default_device()
    if device:
        DEFAULT_DRIVES.append(device)


DEFAULT_CA_PROVIDERS = [
    ('Cover Art Archive', True),
    ('UrlRelationships', True),
    ('CaaReleaseGroup', True),
    ('Local', False),
]
DEFAULT_COVER_IMAGE_FILENAME = 'cover'

DEFAULT_FPCALC_THREADS = 2
DEFAULT_PROGRAM_UPDATE_LEVEL = 0

# On macOS it is not common that the global menu shows icons
DEFAULT_SHOW_MENU_ICONS = not IS_MACOS

DEFAULT_STARTING_DIR = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)

DEFAULT_THEME_NAME = str(UiTheme.DEFAULT)

DEFAULT_TOOLBAR_LAYOUT = [
    'add_directory_action',
    'add_files_action',
    'separator',
    'cluster_action',
    'separator',
    'autotag_action',
    'analyze_action',
    'browser_lookup_action',
    'separator',
    'save_action',
    'view_info_action',
    'remove_action',
    'separator',
    'cd_lookup_action',
    'separator',
    'submit_acoustid_action',
]

DEFAULT_TOP_TAGS = [
    'title',
    'artist',
    'album',
    'tracknumber',
    '~length',
    'date',
]

DEFAULT_AUTOBACKUP_DIRECTORY = os.path.normpath(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation))

DEFAULT_CACHE_SIZE_IN_BYTES = 100*CACHE_SIZE_DISPLAY_UNIT

DEFAULT_LONG_PATHS = system_supports_long_paths() if IS_WIN else False

DEFAULT_FILE_NAMING_FORMAT = "$if2(%albumartist%,%artist%)/\n" \
    "$if(%albumartist%,%album%/,)\n" \
    "$if($gt(%totaldiscs%,1),$if($gt(%totaldiscs%,9),$num(%discnumber%,2),%discnumber%)-,)" \
    "$if($and(%albumartist%,%tracknumber%),$num(%tracknumber%,2) ,)" \
    "$if(%_multiartist%,%artist% - ,)" \
    "%title%"


DEFAULT_SCRIPT_NAME = N_("My script")
DEFAULT_PROFILE_NAME = N_("My profile")
DEFAULT_COPY_TEXT = N_("(copy)")
DEFAULT_NUMBERED_TITLE_FORMAT = N_("{title} ({count})")
DEFAULT_NAMING_PRESET_ID = "Preset 1"

DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

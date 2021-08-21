# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2007, 2014, 2016 Lukáš Lalinský
# Copyright (C) 2014, 2019-2021 Philipp Wolfer
# Copyright (C) 2014-2016, 2018-2021 Laurent Monin
# Copyright (C) 2015 Ohm Patel
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016 Wieland Hoffmann
# Copyright (C) 2016-2017 Frederik “Freso” S. Olesen
# Copyright (C) 2017 Antonio Larrosa
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Bob Swift
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2020 RomFouq
# Copyright (C) 2021 Bob Swift
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


import builtins
from collections import OrderedDict
import os

from PyQt5.QtCore import QStandardPaths

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
)
from picard.const.attributes import MB_ATTRIBUTES

# Install gettext "noop" function in case const.py gets imported directly.
builtins.__dict__['N_'] = lambda a: a


# Config directory
_appconfiglocation = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
USER_DIR = os.path.normpath(os.path.join(_appconfiglocation, PICARD_ORG_NAME, PICARD_APP_NAME))
USER_PLUGIN_DIR = os.path.normpath(os.path.join(USER_DIR, "plugins"))

# Network Cache default settings
CACHE_DIR = os.path.normpath(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))
CACHE_SIZE_IN_BYTES = 100*1000*1000

# AcousticBrainz
ACOUSTICBRAINZ_HOST = 'acousticbrainz.org'
ACOUSTICBRAINZ_PORT = 443
ACOUSTICBRAINZ_DOWNLOAD_URL = 'https://acousticbrainz.org/download'
EXTRACTOR_NAMES = ['streaming_extractor_music']

# AcoustID client API key
ACOUSTID_KEY = 'v8pQ6oyB'
ACOUSTID_HOST = 'api.acoustid.org'
ACOUSTID_PORT = 443
FPCALC_NAMES = ['fpcalc', 'pyfpcalc']

# MB OAuth client credentials
MUSICBRAINZ_OAUTH_CLIENT_ID = 'ACa9wsDX19cLp-AeEP-vVw'
MUSICBRAINZ_OAUTH_CLIENT_SECRET = 'xIsvXbIuntaLuRRhzuazOA'

# Cover art archive URL and port
CAA_HOST = "coverartarchive.org"
CAA_PORT = 443

# Prepare documentation URLs
if PICARD_VERSION.identifier == 'final':
    DOCS_VERSION = "v{}.{}/".format(PICARD_VERSION.major, PICARD_VERSION.minor)
else:
    DOCS_VERSION = ""  # points to latest version
DOCS_LANGUAGE = 'en'
DOCS_BASE_URL = "https://picard-docs.musicbrainz.org/" + DOCS_VERSION + DOCS_LANGUAGE

# URLs
PICARD_URLS = {
    'home':                    "https://picard.musicbrainz.org/",
    'documentation':           DOCS_BASE_URL + '/',
    'troubleshooting':         DOCS_BASE_URL + '/troubleshooting/troubleshooting.html',
    'doc_options':             DOCS_BASE_URL + '/config/configuration.html',
    'doc_scripting':           DOCS_BASE_URL + '/extending/scripting.html',
    'doc_tags_from_filenames': DOCS_BASE_URL + '/usage/tags_from_file_names.html',
    'doc_naming_script_edit':  DOCS_BASE_URL + '/config/options_filerenaming_editor.html',
    'doc_cover_art_types':     "https://musicbrainz.org/doc/Cover_Art/Types",
    'plugins':                 "https://picard.musicbrainz.org/plugins/",
    'forum':                   "https://community.metabrainz.org/c/picard",
    'donate':                  "https://metabrainz.org/donate",
    'chromaprint':             "https://acoustid.org/chromaprint#download",
    'acoustid_apikey':         "https://acoustid.org/api-key",
    'acoustid_track':          "https://acoustid.org/track/",
}

# Various Artists MBID
VARIOUS_ARTISTS_ID = '89ad4ac3-39f7-470e-963a-56509c546377'

# Special purpose track titles
SILENCE_TRACK_TITLE = '[silence]'
DATA_TRACK_TITLE = '[data track]'

# Release formats
RELEASE_FORMATS = {}
RELEASE_PRIMARY_GROUPS = {}
RELEASE_SECONDARY_GROUPS = {}
RELEASE_STATUS = {}
for k, v in MB_ATTRIBUTES.items():
    if k.startswith('DB:medium_format/name:'):
        RELEASE_FORMATS[v] = v
    elif k.startswith('DB:release_group_primary_type/name:'):
        RELEASE_PRIMARY_GROUPS[v] = v
    elif k.startswith('DB:release_group_secondary_type/name:'):
        RELEASE_SECONDARY_GROUPS[v] = v
    elif k.startswith('DB:release_status/name:'):
        RELEASE_STATUS[v] = v

# Release countries
from picard.const.countries import RELEASE_COUNTRIES  # noqa: F401,E402 # pylint: disable=unused-import

# List of available user interface languages
from picard.const.languages import UI_LANGUAGES  # noqa: F401,E402 # pylint: disable=unused-import

# List of alias locales
from picard.const.locales import ALIAS_LOCALES  # noqa: F401,E402 # pylint: disable=unused-import

# List of official musicbrainz servers - must support SSL for mblogin requests (such as collections).
MUSICBRAINZ_SERVERS = [
    'musicbrainz.org',
    'beta.musicbrainz.org',
]

# Plugins and Release Versions API
PLUGINS_API = {
    'host': 'picard.musicbrainz.org',
    'port': 443,
    'endpoint': {
        'plugins': '/api/v2/plugins/',
        'download': '/api/v2/download/',
        'releases': '/api/v2/releases',
    }
}

# Default query limit
QUERY_LIMIT = 25

# Maximum number of covers to draw in a stack in CoverArtThumbnail
MAX_COVERS_TO_STACK = 4

# Update levels available for automatic checking
PROGRAM_UPDATE_LEVELS = OrderedDict(
    [
        (
            0, {
                'name': 'stable',
                'title': N_('Stable releases only'),
            }
        ),
        (
            1, {
                'name': 'beta',
                'title': N_('Stable and Beta releases'),
            }
        ),
        (
            2, {
                'name': 'dev',
                'title': N_('Stable, Beta and Dev releases'),
            }
        ),
    ]
)


DEFAULT_FILE_NAMING_FORMAT = "$if2(%albumartist%,%artist%)/\n" \
    "$if(%albumartist%,%album%/,)\n" \
    "$if($gt(%totaldiscs%,1),$if($gt(%totaldiscs%,9),$num(%discnumber%,2),%discnumber%)-,)" \
    "$if($and(%albumartist%,%tracknumber%),$num(%tracknumber%,2) ,)" \
    "$if(%_multiartist%,%artist% - ,)" \
    "%title%"


DEFAULT_NUMBERED_SCRIPT_NAME = N_("My script %d")
DEFAULT_SCRIPT_NAME = N_("My script")
DEFAULT_COVER_IMAGE_FILENAME = "cover"
DEFAULT_NUMBERED_PROFILE_NAME = N_("My profile %d")
DEFAULT_PROFILE_NAME = N_("My profile")

SCRIPT_LANGUAGE_VERSION = '1.1'

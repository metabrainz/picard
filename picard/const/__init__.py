# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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
import sys

from PyQt5.QtCore import QStandardPaths
from picard import PICARD_APP_NAME

# Install gettext "noop" function in case const.py gets imported directly.
import builtins
builtins.__dict__['N_'] = lambda a: a


# Config directory
_appconfiglocation = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
USER_DIR = os.path.join(_appconfiglocation, "MusicBrainz", PICARD_APP_NAME)
USER_PLUGIN_DIR = os.path.join(USER_DIR, "plugins")

# AcoustID client API key
ACOUSTID_KEY = 'v8pQ6oyB'
ACOUSTID_HOST = 'api.acoustid.org'
ACOUSTID_PORT = 80
FPCALC_NAMES = ['fpcalc', 'pyfpcalc']

# MB OAuth client credentials
MUSICBRAINZ_OAUTH_CLIENT_ID = 'ACa9wsDX19cLp-AeEP-vVw'
MUSICBRAINZ_OAUTH_CLIENT_SECRET = 'xIsvXbIuntaLuRRhzuazOA'

# Cover art archive URL and port
CAA_HOST = "coverartarchive.org"
CAA_PORT = 443

# URLs
PICARD_URLS = {
    'documentation':    "https://picard.musicbrainz.org/docs/",
    'troubleshooting':  "https://picard.musicbrainz.org/docs/troubleshooting/",
    'home':             "https://picard.musicbrainz.org/",
    'doc_options':      "https://picard.musicbrainz.org/docs/options/",
    'doc_scripting':    "https://picard.musicbrainz.org/docs/scripting",
    'plugins':          "https://picard.musicbrainz.org/plugins/",
    'forum':            "https://community.metabrainz.org/c/picard",
    'donate':           "https://metabrainz.org/donate",
    'chromaprint':      "https://acoustid.org/chromaprint#download",
    'acoustid_apikey':  "https://acoustid.org/api-key",
    'doc_cover_art_types': "https://musicbrainz.org/doc/Cover_Art/Types",
    'acoustid_track': "https://acoustid.org/track/",
}

# Various option for plugin action
PLUGIN_ACTION_NONE, PLUGIN_ACTION_UPDATE, PLUGIN_ACTION_INSTALL, PLUGIN_ACTION_UNINSTALL = range(4)

# Various Artists MBID
VARIOUS_ARTISTS_ID = '89ad4ac3-39f7-470e-963a-56509c546377'

# Special purpose track titles
SILENCE_TRACK_TITLE = '[silence]'
DATA_TRACK_TITLE = '[data track]'

# Release formats
from picard.const.attributes import MB_ATTRIBUTES
RELEASE_FORMATS = {}
RELEASE_PRIMARY_GROUPS = {}
RELEASE_SECONDARY_GROUPS = {}
for k, v in MB_ATTRIBUTES.items():
    if k.startswith('DB:medium_format/name:'):
        RELEASE_FORMATS[v] = v
    elif k.startswith('DB:release_group_primary_type/name:'):
        RELEASE_PRIMARY_GROUPS[v] = v
    elif k.startswith('DB:release_group_secondary_type/name:'):
        RELEASE_SECONDARY_GROUPS[v] = v

# Release countries
from picard.const.countries import RELEASE_COUNTRIES

# List of available user interface languages
from picard.const.languages import UI_LANGUAGES

# List of alias locales
from picard.const.locales import ALIAS_LOCALES

# List of official musicbrainz servers - must support SSL for mblogin requests (such as collections).
MUSICBRAINZ_SERVERS = [
    'musicbrainz.org',
    'beta.musicbrainz.org',
]

# Plugins API
PLUGINS_API = {
    'host': 'picard.musicbrainz.org',
    'port': 443,
    'endpoint': {
        'plugins': '/api/v2/plugins/',
        'download': '/api/v2/download/'
    }
}

# Default query limit
QUERY_LIMIT = 25

# Maximum number of covers to draw in a stack in CoverArtThumbnail
MAX_COVERS_TO_STACK = 4

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Constants for session management.

This module contains all constants used throughout the session management system,
including retry delays, file extensions, and excluded tags.
"""


class SessionConstants:
    """Constants for session management operations."""

    # File handling
    SESSION_FILE_EXTENSION = ".mbps"
    SESSION_FORMAT_VERSION = 1

    # Retry delays in milliseconds
    DEFAULT_RETRY_DELAY_MS = 200
    FAST_RETRY_DELAY_MS = 150

    # Metadata handling
    INTERNAL_TAG_PREFIX = "~"
    EXCLUDED_OVERRIDE_TAGS = frozenset({"length", "~length"})

    # Location types
    LOCATION_UNCLUSTERED = "unclustered"
    LOCATION_TRACK = "track"
    LOCATION_ALBUM_UNMATCHED = "album_unmatched"
    LOCATION_CLUSTER = "cluster"
    LOCATION_NAT = "nat"

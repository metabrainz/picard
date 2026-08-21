# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Khoa Nguyen
# Copyright (C) 2026 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Shared session type aliases.

These aliases centralize nested mapping structures used across session
export/import to improve readability and maintainability.
"""

from typing import (
    Any,
    TypeAlias,
)


# Base aliases
TagValues: TypeAlias = list[Any]

# Tag overrides per entity
TagOverrideMap: TypeAlias = dict[str, TagValues]  # tag -> values
TrackOverrideMap: TypeAlias = dict[str, TagOverrideMap]  # track_id -> tags

# Aggregated overrides
AlbumTrackOverrides: TypeAlias = dict[str, TrackOverrideMap]  # album_id -> tracks
AlbumOverrides: TypeAlias = dict[str, TagOverrideMap]  # album_id -> tags

# Misc session types
UnmatchedAlbums: TypeAlias = list[str]
MbReleaseCache: TypeAlias = dict[str, Any]  # album_id -> release node

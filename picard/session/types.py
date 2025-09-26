"""Shared session type aliases.

These aliases centralize nested mapping structures used across session
export/import to improve readability and maintainability.
"""

from __future__ import annotations

from typing import Any, TypeAlias


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

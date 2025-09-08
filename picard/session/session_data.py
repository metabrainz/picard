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

"""Data structures for session management.

This module contains data classes and type definitions used throughout
the session management system.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from picard.metadata import Metadata


@dataclass(frozen=True)
class SessionItemLocation:
    """Location information for a file within a session.

    Parameters
    ----------
    type : str
        The type of location (e.g., "unclustered", "track", "album_unmatched", "cluster", "nat").
    album_id : str | None, optional
        The MusicBrainz album ID if the file is associated with an album.
    recording_id : str | None, optional
        The MusicBrainz recording ID if the file is associated with a specific track.
    cluster_title : str | None, optional
        The cluster title for files in a cluster.
    cluster_artist : str | None, optional
        The cluster artist for files in a cluster.
    """

    type: str
    album_id: str | None = None
    recording_id: str | None = None
    cluster_title: str | None = None
    cluster_artist: str | None = None


@dataclass
class SessionOptions:
    """Configuration options for a session.

    Parameters
    ----------
    rename_files : bool
        Whether to rename files during processing.
    move_files : bool
        Whether to move files during processing.
    dont_write_tags : bool
        Whether to skip writing tags to files.
    """

    rename_files: bool
    move_files: bool
    dont_write_tags: bool


@dataclass
class SessionItem:
    """A single file item in a session.

    Parameters
    ----------
    file_path : Path
        The path to the file.
    location : SessionItemLocation
        The location information for the file.
    metadata : Metadata | None, optional
        Optional metadata overrides for the file.
    """

    file_path: Path
    location: SessionItemLocation
    metadata: Metadata | None = None


@dataclass
class SessionData:
    """Container for complete session data.

    Parameters
    ----------
    version : int
        The session format version.
    options : SessionOptions
        Configuration options for the session.
    items : list[SessionItem]
        List of file items in the session.
    album_track_overrides : dict[str, dict[str, dict[str, list[Any]]]]
        Track-level metadata overrides per album.
    album_overrides : dict[str, dict[str, list[Any]]]
        Album-level metadata overrides.
    unmatched_albums : list[str]
        List of album IDs that are loaded but have no files matched.
    """

    version: int
    options: SessionOptions
    items: list[SessionItem]
    album_track_overrides: dict[str, dict[str, dict[str, list[Any]]]]
    album_overrides: dict[str, dict[str, list[Any]]]
    unmatched_albums: list[str]


@dataclass
class GroupedItems:
    """Grouped session items by location type.

    Parameters
    ----------
    unclustered : list[Path]
        Files to be placed in unclustered area.
    by_cluster : dict[tuple[str, str], list[Path]]
        Files grouped by cluster (title, artist).
    by_album : dict[str, AlbumItems]
        Files grouped by album ID.
    nat_items : list[tuple[Path, str]]
        NAT items with their recording IDs.
    """

    unclustered: list[Path]
    by_cluster: dict[tuple[str, str], list[Path]]
    by_album: dict[str, AlbumItems]
    nat_items: list[tuple[Path, str]]


@dataclass
class AlbumItems:
    """Items associated with a specific album.

    Parameters
    ----------
    unmatched : list[Path]
        Files to be placed in album unmatched area.
    tracks : list[tuple[Path, str]]
        Files to be moved to specific tracks (path, recording_id).
    """

    unmatched: list[Path]
    tracks: list[tuple[Path, str]]


@dataclass
class TrackOverrides:
    """Metadata overrides for a specific track.

    Parameters
    ----------
    track_id : str
        The recording ID of the track.
    overrides : dict[str, list[Any]]
        The metadata overrides.
    """

    track_id: str
    overrides: dict[str, list[Any]]


@dataclass
class AlbumOverrides:
    """Metadata overrides for a specific album.

    Parameters
    ----------
    album_id : str
        The album ID.
    overrides : dict[str, list[Any]]
        The metadata overrides.
    """

    album_id: str
    overrides: dict[str, list[Any]]

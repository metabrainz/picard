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

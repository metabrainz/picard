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

"""Location detection for session management.

This module handles detecting where files should be placed within a session,
separating the complex location detection logic from other concerns.
"""

from __future__ import annotations

from picard.album import Album, NatAlbum
from picard.cluster import Cluster, UnclusteredFiles
from picard.file import File
from picard.session.constants import SessionConstants
from picard.session.session_data import SessionItemLocation


class LocationDetector:
    """Detects the location type of files in the session."""

    def detect(self, file: File) -> SessionItemLocation:
        """Detect where a file should be placed in the session.

        Parameters
        ----------
        file : File
            The file to detect the location for.

        Returns
        -------
        SessionItemLocation
            The location information for the file.

        Notes
        -----
        This method analyzes the file's parent item to determine its proper
        location within the session structure.
        """
        parent = file.parent_item
        if parent is None:
            return self._unclustered_location()

        if self._is_track_parent(parent):
            return self._detect_track_location(parent)
        elif self._is_cluster_parent(parent):
            return self._detect_cluster_location(parent)
        else:
            return self._unclustered_location()

    def _is_track_parent(self, parent: object) -> bool:
        """Check if parent is a track (has album attribute).

        Parameters
        ----------
        parent : object
            The parent item to check.

        Returns
        -------
        bool
            True if parent is a track.
        """
        return hasattr(parent, "album") and isinstance(parent.album, Album)

    def _is_cluster_parent(self, parent: object) -> bool:
        """Check if parent is a cluster.

        Parameters
        ----------
        parent : object
            The parent item to check.

        Returns
        -------
        bool
            True if parent is a cluster.
        """
        return isinstance(parent, Cluster)

    def _detect_track_location(self, parent: object) -> SessionItemLocation:
        """Detect location for files under a track.

        Parameters
        ----------
        parent : object
            The track parent item.

        Returns
        -------
        SessionItemLocation
            The location information for the track.
        """
        if isinstance(parent.album, NatAlbum):
            # NAT special handling
            return SessionItemLocation(type=SessionConstants.LOCATION_NAT, recording_id=parent.id)

        # Track placement
        if hasattr(parent, "id") and parent.id:
            return SessionItemLocation(
                type=SessionConstants.LOCATION_TRACK, album_id=parent.album.id, recording_id=parent.id
            )

        # Fallback to album unmatched
        return SessionItemLocation(type=SessionConstants.LOCATION_ALBUM_UNMATCHED, album_id=parent.album.id)

    def _detect_cluster_location(self, parent: Cluster) -> SessionItemLocation:
        """Detect location for files under a cluster.

        Parameters
        ----------
        parent : Cluster
            The cluster parent item.

        Returns
        -------
        SessionItemLocation
            The location information for the cluster.
        """
        # Unmatched files inside an album
        if parent.related_album:
            return SessionItemLocation(type=SessionConstants.LOCATION_ALBUM_UNMATCHED, album_id=parent.related_album.id)

        # Left pane cluster
        if isinstance(parent, UnclusteredFiles):
            return self._unclustered_location()

        return SessionItemLocation(
            type=SessionConstants.LOCATION_CLUSTER,
            cluster_title=str(parent.metadata["album"]),
            cluster_artist=str(parent.metadata["albumartist"]),
        )

    def _unclustered_location(self) -> SessionItemLocation:
        """Create an unclustered location.

        Returns
        -------
        SessionItemLocation
            Location for unclustered files.
        """
        return SessionItemLocation(type=SessionConstants.LOCATION_UNCLUSTERED)

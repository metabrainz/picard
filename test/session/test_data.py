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

"""Tests for session data structures."""

from pathlib import Path

from picard.session.session_data import (
    AlbumItems,
    GroupedItems,
    SessionItemLocation,
)

import pytest


# =============================================================================
# SessionItemLocation Tests
# =============================================================================


@pytest.mark.parametrize(
    ("location_type", "album_id", "recording_id", "cluster_title", "cluster_artist"),
    [
        ("unclustered", None, None, None, None),
        ("track", "album-123", "recording-456", None, None),
        ("album_unmatched", "album-789", None, None, None),
        ("cluster", None, None, "Album Title", "Artist Name"),
        ("nat", None, "recording-999", None, None),
    ],
)
def test_session_item_location_creation(
    location_type: str,
    album_id: str | None,
    recording_id: str | None,
    cluster_title: str | None,
    cluster_artist: str | None,
) -> None:
    """Test SessionItemLocation creation with various parameters."""
    location = SessionItemLocation(
        type=location_type,
        album_id=album_id,
        recording_id=recording_id,
        cluster_title=cluster_title,
        cluster_artist=cluster_artist,
    )

    assert location.type == location_type
    assert location.album_id == album_id
    assert location.recording_id == recording_id
    assert location.cluster_title == cluster_title
    assert location.cluster_artist == cluster_artist


def test_session_item_location_immutable() -> None:
    """Test that SessionItemLocation is immutable."""
    location = SessionItemLocation(type="test")

    with pytest.raises(AttributeError):
        location.type = "modified"


# =============================================================================
# GroupedItems Tests
# =============================================================================


def test_grouped_items_creation() -> None:
    """Test GroupedItems creation with all components."""
    unclustered = [Path("/test/unclustered.mp3")]
    by_cluster = {("Album", "Artist"): [Path("/test/cluster.mp3")]}
    by_album = {
        'album-123': AlbumItems(
            unmatched=[Path("/test/unmatched.mp3")], tracks=[(Path("/test/track.mp3"), "recording-456")]
        )
    }
    nat_items = [(Path("/test/nat.mp3"), "recording-789")]

    grouped = GroupedItems(
        unclustered=unclustered,
        by_cluster=by_cluster,
        by_album=by_album,
        nat_items=nat_items,
    )

    assert grouped.unclustered == unclustered
    assert grouped.by_cluster == by_cluster
    assert grouped.by_album == by_album
    assert grouped.nat_items == nat_items


# =============================================================================
# AlbumItems Tests
# =============================================================================


def test_album_items_creation() -> None:
    """Test AlbumItems creation with unmatched files and tracks."""
    unmatched = [Path("/test/unmatched1.mp3"), Path("/test/unmatched2.mp3")]
    tracks = [(Path("/test/track1.mp3"), "recording-123"), (Path("/test/track2.mp3"), "recording-456")]

    album_items = AlbumItems(unmatched=unmatched, tracks=tracks)

    assert album_items.unmatched == unmatched
    assert album_items.tracks == tracks

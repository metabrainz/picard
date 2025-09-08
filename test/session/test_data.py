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

from picard.metadata import Metadata
from picard.session.session_data import (
    AlbumItems,
    AlbumOverrides,
    GroupedItems,
    SessionData,
    SessionItem,
    SessionItemLocation,
    SessionOptions,
    TrackOverrides,
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
# SessionOptions Tests
# =============================================================================


@pytest.mark.parametrize(
    ("rename_files", "move_files", "dont_write_tags"),
    [
        (True, True, True),
        (False, False, False),
        (True, False, True),
        (False, True, False),
    ],
)
def test_session_options_creation(rename_files: bool, move_files: bool, dont_write_tags: bool) -> None:
    """Test SessionOptions creation with various boolean combinations."""
    options = SessionOptions(
        rename_files=rename_files,
        move_files=move_files,
        dont_write_tags=dont_write_tags,
    )

    assert options.rename_files == rename_files
    assert options.move_files == move_files
    assert options.dont_write_tags == dont_write_tags


# =============================================================================
# SessionItem Tests
# =============================================================================


def test_session_item_creation() -> None:
    """Test SessionItem creation with metadata."""
    file_path = Path("/test/file.mp3")
    location = SessionItemLocation(type="track", album_id="album-123", recording_id="recording-456")
    metadata = Metadata()
    metadata["title"] = "Test Song"

    item = SessionItem(file_path=file_path, location=location, metadata=metadata)

    assert item.file_path == file_path
    assert item.location == location
    assert item.metadata == metadata


def test_session_item_creation_without_metadata() -> None:
    """Test SessionItem creation without metadata."""
    file_path = Path("/test/file.mp3")
    location = SessionItemLocation(type="unclustered")

    item = SessionItem(file_path=file_path, location=location)

    assert item.file_path == file_path
    assert item.location == location
    assert item.metadata is None


# =============================================================================
# SessionData Tests
# =============================================================================


def test_session_data_creation() -> None:
    """Test SessionData creation with all components."""
    options = SessionOptions(rename_files=True, move_files=False, dont_write_tags=True)
    location = SessionItemLocation(type="track", album_id="album-123")
    item = SessionItem(file_path=Path("/test/file.mp3"), location=location)

    data = SessionData(
        version=1,
        options=options,
        items=[item],
        album_track_overrides={"album-123": {"track-456": {"title": ["New Title"]}}},
        album_overrides={"album-123": {"albumartist": ["New Artist"]}},
        unmatched_albums=["album-789"],
    )

    assert data.version == 1
    assert data.options == options
    assert data.items == [item]
    assert data.album_track_overrides == {"album-123": {"track-456": {"title": ["New Title"]}}}
    assert data.album_overrides == {"album-123": {"albumartist": ["New Artist"]}}
    assert data.unmatched_albums == ["album-789"]


# =============================================================================
# GroupedItems Tests
# =============================================================================


def test_grouped_items_creation() -> None:
    """Test GroupedItems creation with all components."""
    unclustered = [Path("/test/unclustered.mp3")]
    by_cluster = {("Album", "Artist"): [Path("/test/cluster.mp3")]}
    by_album = {
        "album-123": AlbumItems(
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


# =============================================================================
# TrackOverrides Tests
# =============================================================================


def test_track_overrides_creation() -> None:
    """Test TrackOverrides creation."""
    overrides = {"title": ["New Title"], "artist": ["New Artist"]}

    track_overrides = TrackOverrides(track_id="recording-123", overrides=overrides)

    assert track_overrides.track_id == "recording-123"
    assert track_overrides.overrides == overrides


# =============================================================================
# AlbumOverrides Tests
# =============================================================================


def test_album_overrides_creation() -> None:
    """Test AlbumOverrides creation."""
    overrides = {"albumartist": ["New Artist"], "album": ["New Album"]}

    album_overrides = AlbumOverrides(album_id="album-123", overrides=overrides)

    assert album_overrides.album_id == "album-123"
    assert album_overrides.overrides == overrides

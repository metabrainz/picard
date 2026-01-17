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

"""Tests for location detector."""

from pathlib import Path
from unittest.mock import Mock

from picard.album import (
    Album,
    NatAlbum,
)
from picard.cluster import (
    Cluster,
    UnclusteredFiles,
)
from picard.file import File
from picard.session.constants import SessionConstants
from picard.session.location_detector import LocationDetector

import pytest


@pytest.fixture
def location_detector() -> LocationDetector:
    """Provide a LocationDetector instance."""
    return LocationDetector()


@pytest.fixture
def mock_file() -> Mock:
    """Provide a mock file object."""
    file_mock = Mock(spec=File)
    file_mock.filename = str(Path("/test/file.mp3"))
    return file_mock


def test_location_detector_unclustered_file(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for unclustered files."""
    mock_file.parent_item = None

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_UNCLUSTERED
    assert location.album_id is None
    assert location.recording_id is None


def test_location_detector_track_file(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for files under tracks."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"

    mock_track = Mock()
    mock_track.album = mock_album
    mock_track.id = "recording-456"
    mock_file.parent_item = mock_track

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_TRACK
    assert location.album_id == "album-123"
    assert location.recording_id == "recording-456"


def test_location_detector_nat_file(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for NAT files."""
    mock_album = Mock(spec=NatAlbum)
    mock_album.id = "nat-album-123"

    mock_track = Mock()
    mock_track.album = mock_album
    mock_track.id = "recording-456"
    mock_file.parent_item = mock_track

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_NAT
    assert location.recording_id == "recording-456"
    assert location.album_id is None


def test_location_detector_cluster_file(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for files under clusters."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"

    mock_cluster = Mock(spec=Cluster)
    mock_cluster.album = mock_album
    mock_cluster.metadata = {'album': "Test Album", 'albumartist': "Test Artist"}
    mock_file.parent_item = mock_cluster

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_ALBUM_UNMATCHED
    assert location.album_id == "album-123"


def test_location_detector_unclustered_files_cluster(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for UnclusteredFiles cluster."""
    mock_cluster = Mock(spec=UnclusteredFiles)
    mock_cluster.album = None
    mock_file.parent_item = mock_cluster

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_UNCLUSTERED


def test_location_detector_regular_cluster(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for regular clusters."""
    mock_cluster = Mock(spec=Cluster)
    mock_cluster.album = None
    mock_cluster.metadata = {'album': "Test Album", 'albumartist': "Test Artist"}
    mock_file.parent_item = mock_cluster

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_CLUSTER
    assert location.cluster_title == "Test Album"
    assert location.cluster_artist == "Test Artist"


def test_location_detector_track_without_id(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for tracks without ID."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"

    mock_track = Mock()
    mock_track.album = mock_album
    # No id attribute
    del mock_track.id
    mock_file.parent_item = mock_track

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_ALBUM_UNMATCHED
    assert location.album_id == "album-123"


def test_location_detector_unknown_parent(location_detector: LocationDetector, mock_file: Mock) -> None:
    """Test location detection for unknown parent types."""
    mock_file.parent_item = Mock()  # Not a track or cluster

    location = location_detector.detect(mock_file)

    assert location.type == SessionConstants.LOCATION_UNCLUSTERED


def test_location_detector_is_track_parent(location_detector: LocationDetector) -> None:
    """Test _is_track_parent method."""
    # Valid track parent
    mock_track = Mock()
    mock_album = Mock(spec=Album)
    mock_track.album = mock_album

    assert location_detector._is_track_parent(mock_track) is True

    # Invalid track parent - no album
    mock_track_no_album = Mock()
    mock_track_no_album.album = None

    assert location_detector._is_track_parent(mock_track_no_album) is False

    # Invalid track parent - album not Album instance
    mock_track_wrong_album = Mock()
    mock_track_wrong_album.album = Mock()  # Not Album instance

    assert location_detector._is_track_parent(mock_track_wrong_album) is False


def test_location_detector_is_cluster_parent(location_detector: LocationDetector) -> None:
    """Test _is_cluster_parent method."""
    # Valid cluster parent
    mock_cluster = Mock(spec=Cluster)
    assert location_detector._is_cluster_parent(mock_cluster) is True

    # Invalid cluster parent
    mock_not_cluster = Mock()
    assert location_detector._is_cluster_parent(mock_not_cluster) is False


def test_location_detector_detect_track_location_nat(location_detector: LocationDetector) -> None:
    """Test _detect_track_location for NAT albums."""
    mock_album = Mock(spec=NatAlbum)
    mock_track = Mock()
    mock_track.album = mock_album
    mock_track.id = "recording-123"

    location = location_detector._detect_track_location(mock_track)

    assert location.type == SessionConstants.LOCATION_NAT
    assert location.recording_id == "recording-123"


def test_location_detector_detect_track_location_regular(location_detector: LocationDetector) -> None:
    """Test _detect_track_location for regular albums."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"
    mock_track = Mock()
    mock_track.album = mock_album
    mock_track.id = "recording-456"

    location = location_detector._detect_track_location(mock_track)

    assert location.type == SessionConstants.LOCATION_TRACK
    assert location.album_id == "album-123"
    assert location.recording_id == "recording-456"


def test_location_detector_detect_track_location_no_id(location_detector: LocationDetector) -> None:
    """Test _detect_track_location for tracks without ID."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"
    mock_track = Mock()
    mock_track.album = mock_album
    # No id attribute
    del mock_track.id

    location = location_detector._detect_track_location(mock_track)

    assert location.type == SessionConstants.LOCATION_ALBUM_UNMATCHED
    assert location.album_id == "album-123"


def test_location_detector_detect_cluster_location_with_album(location_detector: LocationDetector) -> None:
    """Test _detect_cluster_location with related album."""
    mock_album = Mock(spec=Album)
    mock_album.id = "album-123"
    mock_cluster = Mock(spec=Cluster)
    mock_cluster.album = mock_album

    location = location_detector._detect_cluster_location(mock_cluster)

    assert location.type == SessionConstants.LOCATION_ALBUM_UNMATCHED
    assert location.album_id == "album-123"


def test_location_detector_detect_cluster_location_unclustered_files(location_detector: LocationDetector) -> None:
    """Test _detect_cluster_location with UnclusteredFiles."""
    mock_cluster = Mock(spec=UnclusteredFiles)
    mock_cluster.album = None

    location = location_detector._detect_cluster_location(mock_cluster)

    assert location.type == SessionConstants.LOCATION_UNCLUSTERED


def test_location_detector_detect_cluster_location_regular_cluster(location_detector: LocationDetector) -> None:
    """Test _detect_cluster_location with regular cluster."""
    mock_cluster = Mock(spec=Cluster)
    mock_cluster.album = None
    mock_cluster.metadata = {'album': "Test Album", 'albumartist': "Test Artist"}

    location = location_detector._detect_cluster_location(mock_cluster)

    assert location.type == SessionConstants.LOCATION_CLUSTER
    assert location.cluster_title == "Test Album"
    assert location.cluster_artist == "Test Artist"


def test_location_detector_unclustered_location(location_detector: LocationDetector) -> None:
    """Test _unclustered_location method."""
    location = location_detector._unclustered_location()

    assert location.type == SessionConstants.LOCATION_UNCLUSTERED
    assert location.album_id is None
    assert location.recording_id is None
    assert location.cluster_title is None
    assert location.cluster_artist is None

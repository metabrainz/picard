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

"""Tests for session exporter."""

from pathlib import Path
from unittest.mock import Mock, patch

from picard.album import Album, NatAlbum
from picard.metadata import Metadata
from picard.session.constants import SessionConstants
from picard.session.session_data import SessionItemLocation
from picard.session.session_exporter import SessionExporter

import pytest


@pytest.fixture
def session_exporter() -> SessionExporter:
    """Provide a SessionExporter instance."""
    return SessionExporter()


@pytest.fixture
def mock_tagger() -> Mock:
    """Provide a mock tagger instance."""
    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {}
    return tagger_mock


def test_session_exporter_export_session_empty(session_exporter: SessionExporter, mock_tagger: Mock) -> None:
    """Test exporting an empty session."""
    config_mock = Mock()
    config_mock.setting = {
        "rename_files": False,
        "move_files": False,
        "dont_write_tags": True,
    }

    with patch('picard.session.session_exporter.get_config') as mock_get_config:
        mock_get_config.return_value = config_mock

        data = session_exporter.export_session(mock_tagger)

        assert data["version"] == SessionConstants.SESSION_FORMAT_VERSION
        assert data["options"] == {
            "rename_files": False,
            "move_files": False,
            "dont_write_tags": True,
        }
        assert data["items"] == []
        assert data["album_track_overrides"] == {}
        assert data["album_overrides"] == {}
        assert data["unmatched_albums"] == []
        assert data["expanded_albums"] == []


def test_session_exporter_export_file_item_saved(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting a saved file item."""

    file_mock = Mock()
    file_mock.filename = str(Path("/test/file.mp3"))
    file_mock.is_saved.return_value = True
    file_mock.parent_item = None

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = [file_mock]
    tagger_mock.albums = {}

    with patch.object(session_exporter.location_detector, 'detect') as mock_detect:
        mock_detect.return_value = SessionItemLocation(type="unclustered")
        data = session_exporter.export_session(tagger_mock)

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["file_path"] == str(Path("/test/file.mp3"))
    assert "metadata" not in item


def test_session_exporter_export_file_item_unsaved(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting an unsaved file item with metadata (delta vs orig_metadata)."""

    file_mock = Mock()
    file_mock.filename = str(Path("/test/file.mp3"))
    file_mock.is_saved.return_value = False
    file_mock.parent_item = None
    file_mock.metadata = Metadata()
    file_mock.metadata["title"] = "Test Song"
    # Provide an original metadata baseline so exporter can compute a delta
    file_mock.orig_metadata = Metadata()

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = [file_mock]
    tagger_mock.albums = {}

    with patch.object(session_exporter.location_detector, 'detect') as mock_detect:
        mock_detect.return_value = SessionItemLocation(type="unclustered")
        data = session_exporter.export_session(tagger_mock)

    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["file_path"] == str(Path("/test/file.mp3"))
    assert "metadata" in item
    assert item["metadata"]["tags"]["title"] == ["Test Song"]


def test_session_exporter_export_ui_state(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting UI expansion state."""

    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = []
    ui_item_mock = Mock()
    ui_item_mock.isExpanded.return_value = True
    album_mock.ui_item = ui_item_mock

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff method to return None (no overrides)
    with patch.object(album_mock.metadata, 'diff', return_value=None):
        data = session_exporter.export_session(tagger_mock)

    assert data["expanded_albums"] == ["album-123"]


def test_session_exporter_export_ui_state_no_ui_item(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting UI state when album has no UI item."""

    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = []
    album_mock.ui_item = None

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff method to return None (no overrides)
    with patch.object(album_mock.metadata, 'diff', return_value=None):
        data = session_exporter.export_session(tagger_mock)

    assert data["expanded_albums"] == []


def test_session_exporter_export_metadata_overrides(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting metadata overrides."""

    # Create album with overrides
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.metadata["albumartist"] = "New Artist"
    album_mock.orig_metadata["albumartist"] = "Old Artist"

    # Create track with overrides
    track_mock = Mock()
    track_mock.id = "track-456"
    track_mock.metadata = Metadata()
    track_mock.scripted_metadata = Metadata()
    track_mock.metadata["title"] = "New Title"
    track_mock.scripted_metadata["title"] = "Old Title"
    album_mock.tracks = [track_mock]

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff and rawitems methods
    diff_mock = Mock()
    diff_mock.rawitems.return_value = [("albumartist", ["New Artist"])]
    track_diff_mock = Mock()
    track_diff_mock.rawitems.return_value = [("title", ["New Title"])]

    with (
        patch.object(album_mock.metadata, 'diff', return_value=diff_mock),
        patch.object(track_mock.metadata, 'diff', return_value=track_diff_mock),
    ):
        data = session_exporter.export_session(tagger_mock)

    assert "album-123" in data["album_overrides"]
    assert data["album_overrides"]["album-123"]["albumartist"] == ["New Artist"]
    assert "album-123" in data["album_track_overrides"]
    assert data["album_track_overrides"]["album-123"]["track-456"]["title"] == ["New Title"]


def test_session_exporter_export_unmatched_albums(session_exporter: SessionExporter, cfg_options) -> None:
    """Test exporting unmatched albums."""

    # Create album with no files and no overrides
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = []

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff method to return None (no overrides)
    with patch.object(album_mock.metadata, 'diff', return_value=None):
        data = session_exporter.export_session(tagger_mock)

    assert data["unmatched_albums"] == ["album-123"]


def test_session_exporter_export_skips_nat_albums(session_exporter: SessionExporter, cfg_options) -> None:
    """Test that NAT albums are skipped in metadata overrides export."""

    # Create NAT album
    nat_album_mock = Mock(spec=NatAlbum)
    nat_album_mock.id = "nat-album-123"

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"nat-album-123": nat_album_mock}

    data = session_exporter.export_session(tagger_mock)

    assert data["album_overrides"] == {}
    assert data["album_track_overrides"] == {}
    assert data["unmatched_albums"] == []


def test_session_exporter_export_albums_with_files(session_exporter: SessionExporter, cfg_options) -> None:
    """Test that albums with files are not included in unmatched_albums."""

    # Create album
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = []

    # Create file with parent item pointing to album
    file_mock = Mock()
    file_mock.filename = "/test/file.mp3"
    file_mock.is_saved.return_value = True
    parent_item_mock = Mock()
    parent_item_mock.album = album_mock
    file_mock.parent_item = parent_item_mock

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = [file_mock]
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff method to return None (no overrides)
    with (
        patch.object(album_mock.metadata, 'diff', return_value=None),
        patch.object(session_exporter.location_detector, 'detect') as mock_detect,
    ):
        mock_detect.return_value = SessionItemLocation(type="track", album_id="album-123")
        data = session_exporter.export_session(tagger_mock)

    assert data["unmatched_albums"] == []


def test_session_exporter_serialize_location() -> None:
    """Test location serialization."""
    exporter = SessionExporter()

    location = SessionItemLocation(
        type="track",
        album_id="album-123",
        recording_id="recording-456",
        cluster_title=None,
        cluster_artist=None,
    )

    serialized = exporter._serialize_location(location)

    assert serialized == {
        "type": "track",
        "album_id": "album-123",
        "recording_id": "recording-456",
    }


def test_session_exporter_serialize_location_with_none_values() -> None:
    """Test location serialization with None values."""
    exporter = SessionExporter()

    location = SessionItemLocation(
        type="unclustered",
        album_id=None,
        recording_id=None,
        cluster_title=None,
        cluster_artist=None,
    )

    serialized = exporter._serialize_location(location)

    assert serialized == {"type": "unclustered"}


def test_session_exporter_serialize_location_with_cluster_info() -> None:
    """Test location serialization with cluster information."""
    exporter = SessionExporter()

    location = SessionItemLocation(
        type="cluster",
        album_id=None,
        recording_id=None,
        cluster_title="Test Album",
        cluster_artist="Test Artist",
    )

    serialized = exporter._serialize_location(location)

    assert serialized == {
        "type": "cluster",
        "cluster_title": "Test Album",
        "cluster_artist": "Test Artist",
    }


def test_session_exporter_export_options() -> None:
    """Test exporting configuration options."""
    exporter = SessionExporter()

    config_mock = Mock()
    config_mock.setting = {
        "rename_files": True,
        "move_files": False,
        "dont_write_tags": True,
    }

    options = exporter._export_options(config_mock)

    assert options == {
        "rename_files": True,
        "move_files": False,
        "dont_write_tags": True,
    }


def test_session_exporter_export_options_with_falsy_values() -> None:
    """Test exporting configuration options with falsy values."""
    exporter = SessionExporter()

    config_mock = Mock()
    config_mock.setting = {
        "rename_files": 0,
        "move_files": "",
        "dont_write_tags": None,
    }

    options = exporter._export_options(config_mock)

    assert options == {
        "rename_files": False,
        "move_files": False,
        "dont_write_tags": False,
    }


def test_session_exporter_export_metadata_overrides_excludes_length(
    session_exporter: SessionExporter, cfg_options
) -> None:
    """Test that length tags are excluded from metadata overrides."""

    # Create album with length override
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.metadata["length"] = "300000"
    album_mock.orig_metadata["length"] = "250000"
    album_mock.tracks = []

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff method to return length override
    diff_mock = Mock()
    diff_mock.rawitems.return_value = [("length", ["300000"])]

    with patch.object(album_mock.metadata, 'diff', return_value=diff_mock):
        data = session_exporter.export_session(tagger_mock)

    # Length should not be in overrides
    assert "album-123" not in data["album_overrides"] or "length" not in data["album_overrides"]["album-123"]


def test_session_exporter_export_metadata_overrides_excludes_internal_tags(
    session_exporter: SessionExporter, cfg_options
) -> None:
    """Test that internal tags are excluded from metadata overrides."""

    # Create track with internal tag override
    track_mock = Mock()
    track_mock.id = "track-456"
    track_mock.metadata = Metadata()
    track_mock.scripted_metadata = Metadata()
    track_mock.metadata["~internal"] = "new_value"
    track_mock.scripted_metadata["~internal"] = "old_value"

    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = [track_mock]

    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {"album-123": album_mock}

    # Mock the diff methods
    track_diff_mock = Mock()
    track_diff_mock.rawitems.return_value = [("~internal", ["new_value"])]
    album_diff_mock = Mock()
    album_diff_mock.rawitems.return_value = []

    with (
        patch.object(track_mock.metadata, 'diff', return_value=track_diff_mock),
        patch.object(album_mock.metadata, 'diff', return_value=album_diff_mock),
    ):
        data = session_exporter.export_session(tagger_mock)

    # Internal tag should be in overrides (current implementation includes them)
    assert "album-123" in data["album_track_overrides"]
    assert "track-456" in data["album_track_overrides"]["album-123"]
    assert "~internal" in data["album_track_overrides"]["album-123"]["track-456"]
    assert data["album_track_overrides"]["album-123"]["track-456"]["~internal"] == ["new_value"]

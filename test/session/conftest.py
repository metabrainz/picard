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

"""Fixtures and mocks for tests in session management package for Picard."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from picard.album import Album, NatAlbum
from picard.cluster import Cluster, UnclusteredFiles
import picard.config as picard_config
from picard.file import File
from picard.metadata import Metadata
from picard.session.location_detector import LocationDetector
from picard.session.session_data import AlbumItems, SessionItemLocation
from picard.session.session_exporter import SessionExporter
from picard.session.session_loader import SessionLoader
from picard.session.track_mover import TrackMover

import pytest


# =============================================================================
# Stub Classes
# =============================================================================


class _StubFile:
    """Stub file class for testing."""

    def __init__(self, filename: str, metadata: Metadata, saved: bool, parent_item: Any = None) -> None:
        self.filename = filename
        self.metadata = metadata
        self._saved = saved
        self.parent_item = parent_item

    def is_saved(self) -> bool:
        return self._saved


class _StubTrack:
    """Stub track class for testing."""

    def __init__(self, track_id: str, scripted: Metadata, current: Metadata) -> None:
        self.id = track_id
        self.scripted_metadata = scripted
        self.metadata = current


class _StubAlbum:
    """Stub album class for testing."""

    def __init__(self, album_id: str, orig: Metadata, current: Metadata, tracks: list[_StubTrack]) -> None:
        self.id = album_id
        self.orig_metadata = orig
        self.metadata = current
        self.tracks = tracks


class _StubTagger:
    """Stub tagger class for testing."""

    def __init__(self, files: list[_StubFile], albums: dict[str, Any] | None = None) -> None:
        self._files = files
        self.albums = albums or {}

    def iter_all_files(self):
        yield from self._files


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _fake_script_config(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide minimal config so functions accessing get_config() have settings."""

    class _FakeSetting(dict):
        def raw_value(self, name, qtype=None):
            return self.get(name)

        def key(self, name):
            return name

    cfg = SimpleNamespace(setting=_FakeSetting({'enabled_plugins': []}), sync=lambda: None)
    import picard.config as picard_config_mod
    import picard.extension_points as ext_points_mod
    import picard.session.session_exporter as session_exporter_mod
    import picard.session.session_loader as session_loader_mod

    monkeypatch.setattr(picard_config_mod, 'get_config', lambda: cfg, raising=True)
    monkeypatch.setattr(ext_points_mod, 'get_config', lambda: cfg, raising=True)
    monkeypatch.setattr(session_exporter_mod, 'get_config', lambda: cfg, raising=True)
    monkeypatch.setattr(session_loader_mod, 'get_config', lambda: cfg, raising=True)
    return cfg


@pytest.fixture()
def cfg_options() -> None:
    """Ensure required config keys exist with defaults."""
    cfg = picard_config.get_config()
    # Ensure required keys exist with defaults
    cfg.setting['rename_files'] = False
    cfg.setting['move_files'] = False
    cfg.setting['dont_write_tags'] = False


# =============================================================================
# Mock Objects
# =============================================================================


@pytest.fixture
def mock_file() -> Mock:
    """Provide a mock file object."""
    file_mock = Mock(spec=File)
    file_mock.filename = "/test/file.mp3"
    return file_mock


@pytest.fixture
def mock_file_with_metadata() -> Mock:
    """Provide a mock file with metadata."""
    file_mock = Mock(spec=File)
    metadata = Metadata()
    metadata["title"] = "Test Song"
    metadata["artist"] = "Test Artist"
    metadata["~internal"] = "internal_value"
    metadata["length"] = "123456"
    file_mock.metadata = metadata
    return file_mock


@pytest.fixture
def mock_tagger() -> Mock:
    """Provide a mock tagger instance."""
    tagger_mock = Mock()
    tagger_mock.iter_all_files.return_value = []
    tagger_mock.albums = {}
    return tagger_mock


@pytest.fixture
def mock_album() -> Mock:
    """Provide a mock album instance."""
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.tracks = []
    return album_mock


@pytest.fixture
def mock_nat_album() -> Mock:
    """Provide a mock NAT album instance."""
    nat_album_mock = Mock(spec=NatAlbum)
    nat_album_mock.id = "nat-album-123"
    return nat_album_mock


@pytest.fixture
def mock_cluster() -> Mock:
    """Provide a mock cluster instance."""
    cluster_mock = Mock(spec=Cluster)
    cluster_mock.related_album = None
    cluster_mock.metadata = {"album": "Test Album", "albumartist": "Test Artist"}
    return cluster_mock


@pytest.fixture
def mock_unclustered_files() -> Mock:
    """Provide a mock UnclusteredFiles instance."""
    unclustered_mock = Mock(spec=UnclusteredFiles)
    unclustered_mock.related_album = None
    return unclustered_mock


@pytest.fixture
def mock_track() -> Mock:
    """Provide a mock track instance."""
    track_mock = Mock()
    track_mock.id = "recording-123"
    track_mock.metadata = Metadata()
    track_mock.scripted_metadata = Metadata()
    return track_mock


# =============================================================================
# Session Component Fixtures
# =============================================================================


@pytest.fixture
def location_detector() -> LocationDetector:
    """Provide a LocationDetector instance."""
    return LocationDetector()


@pytest.fixture
def session_exporter() -> SessionExporter:
    """Provide a SessionExporter instance."""
    return SessionExporter()


@pytest.fixture
def session_loader() -> SessionLoader:
    """Provide a SessionLoader instance."""
    tagger_mock = Mock()
    return SessionLoader(tagger_mock)


@pytest.fixture
def track_mover() -> TrackMover:
    """Provide a TrackMover instance."""
    tagger_mock = Mock()
    return TrackMover(tagger_mock)


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_metadata() -> Metadata:
    """Provide sample metadata for testing."""
    metadata = Metadata()
    metadata["title"] = "Test Song"
    metadata["artist"] = "Test Artist"
    metadata["album"] = "Test Album"
    metadata["~internal"] = "internal_value"
    metadata["length"] = "123456"
    return metadata


@pytest.fixture
def sample_session_item_location() -> SessionItemLocation:
    """Provide a sample SessionItemLocation for testing."""
    return SessionItemLocation(type="track", album_id="album-123", recording_id="recording-456")


@pytest.fixture
def sample_album_items() -> AlbumItems:
    """Provide sample AlbumItems for testing."""
    return AlbumItems(unmatched=[Path("/test/unmatched.mp3")], tracks=[(Path("/test/track.mp3"), "recording-456")])


@pytest.fixture
def sample_session_data() -> dict[str, Any]:
    """Provide sample session data for testing."""
    return {
        "version": 1,
        "options": {
            "rename_files": True,
            "move_files": False,
            "dont_write_tags": True,
        },
        "items": [
            {
                "file_path": "/test/file1.mp3",
                "location": {"type": "unclustered"},
            },
            {
                "file_path": "/test/file2.mp3",
                "location": {"type": "track", "album_id": "album-123", "recording_id": "recording-456"},
                "metadata": {"tags": {"title": ["Test Song"]}},
            },
        ],
        "album_track_overrides": {"album-123": {"track-456": {"title": ["New Title"]}}},
        "album_overrides": {"album-123": {"albumartist": ["New Artist"]}},
        "unmatched_albums": ["album-789"],
        "expanded_albums": ["album-123"],
    }


# =============================================================================
# Utility Functions
# =============================================================================


def create_stub_file(filename: str, metadata: Metadata, saved: bool = False, parent_item: Any = None) -> _StubFile:
    """Create a stub file for testing."""
    return _StubFile(filename, metadata, saved, parent_item)


def create_stub_track(track_id: str, scripted: Metadata, current: Metadata) -> _StubTrack:
    """Create a stub track for testing."""
    return _StubTrack(track_id, scripted, current)


def create_stub_album(album_id: str, orig: Metadata, current: Metadata, tracks: list[_StubTrack]) -> _StubAlbum:
    """Create a stub album for testing."""
    return _StubAlbum(album_id, orig, current, tracks)


def create_stub_tagger(files: list[_StubFile], albums: dict[str, Any] | None = None) -> _StubTagger:
    """Create a stub tagger for testing."""
    return _StubTagger(files, albums)


def create_mock_album_with_tracks(album_id: str, track_count: int = 2) -> Mock:
    """Create a mock album with specified number of tracks."""
    album_mock = Mock(spec=Album)
    album_mock.id = album_id
    album_mock.metadata = Metadata()
    album_mock.orig_metadata = Metadata()
    album_mock.tracks = []

    for i in range(track_count):
        track_mock = Mock()
        track_mock.id = f"recording-{i + 1}"
        track_mock.metadata = Metadata()
        track_mock.scripted_metadata = Metadata()
        album_mock.tracks.append(track_mock)

    return album_mock


def create_mock_file_with_parent(filename: str, parent_type: str = "track", album_id: str = "album-123") -> Mock:
    """Create a mock file with specified parent type."""
    file_mock = Mock(spec=File)
    file_mock.filename = filename
    file_mock.is_saved.return_value = False
    file_mock.metadata = Metadata()

    if parent_type == "track":
        mock_album = Mock(spec=Album)
        mock_album.id = album_id

        mock_track = Mock()
        mock_track.album = mock_album
        mock_track.id = "recording-456"
        file_mock.parent_item = mock_track
    elif parent_type == "cluster":
        mock_cluster = Mock(spec=Cluster)
        mock_cluster.related_album = None
        mock_cluster.metadata = {"album": "Test Album", "albumartist": "Test Artist"}
        file_mock.parent_item = mock_cluster
    elif parent_type == "nat":
        mock_album = Mock(spec=NatAlbum)
        mock_album.id = "nat-album-123"

        mock_track = Mock()
        mock_track.album = mock_album
        mock_track.id = "recording-456"
        file_mock.parent_item = mock_track
    else:
        file_mock.parent_item = None

    return file_mock


def create_session_items_with_locations() -> list[dict[str, Any]]:
    """Create a list of session items with different location types."""
    return [
        {
            "file_path": "/test/unclustered.mp3",
            "location": {"type": "unclustered"},
        },
        {
            "file_path": "/test/cluster.mp3",
            "location": {"type": "cluster", "cluster_title": "Album", "cluster_artist": "Artist"},
        },
        {
            "file_path": "/test/track.mp3",
            "location": {"type": "track", "album_id": "album-123", "recording_id": "recording-456"},
        },
        {
            "file_path": "/test/unmatched.mp3",
            "location": {"type": "album_unmatched", "album_id": "album-789"},
        },
        {
            "file_path": "/test/nat.mp3",
            "location": {"type": "nat", "recording_id": "recording-999"},
        },
    ]


# =============================================================================
# Mock Fixtures for Patches
# =============================================================================


@pytest.fixture
def mock_get_config() -> Mock:
    """Provide a mock get_config function."""
    return Mock()


@pytest.fixture
def mock_single_shot() -> Mock:
    """Provide a mock QTimer.singleShot function."""
    return Mock()


# =============================================================================
# Patch Helpers
# =============================================================================


def patch_get_config(monkeypatch: pytest.MonkeyPatch, **settings) -> Mock:
    """Patch get_config with specified settings."""
    config_mock = Mock()
    config_mock.setting = {
        "rename_files": False,
        "move_files": False,
        "dont_write_tags": False,
        "session_safe_restore": True,
        **settings,
    }

    import picard.session.session_exporter as session_exporter_mod
    import picard.session.session_loader as session_loader_mod

    monkeypatch.setattr(session_exporter_mod, 'get_config', lambda: config_mock, raising=True)
    monkeypatch.setattr(session_loader_mod, 'get_config', lambda: config_mock, raising=True)

    return config_mock


def patch_qtimer_singleshot(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Patch QtCore.QTimer.singleShot for testing."""
    mock_single_shot = Mock()
    monkeypatch.setattr('PyQt6.QtCore.QTimer.singleShot', mock_single_shot)
    return mock_single_shot

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

"""Tests for session loader."""

from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from picard.album import Album
import picard.config as picard_config
from picard.metadata import Metadata
from picard.session.session_data import AlbumItems, GroupedItems
from picard.session.session_loader import SessionLoader

import pytest


@pytest.fixture
def session_loader() -> SessionLoader:
    """Provide a SessionLoader instance."""
    tagger_mock = Mock()
    return SessionLoader(tagger_mock)


def test_session_loader_read_session_file(session_loader: SessionLoader, tmp_path: Path) -> None:
    """Test reading session file."""
    session_data = {'version': 1, 'items': []}
    session_file = tmp_path / "test.mbps"
    session_file.write_text(yaml.dump(session_data, default_flow_style=False), encoding="utf-8")

    data = session_loader._read_session_file(session_file)

    assert data == session_data


def test_session_loader_read_session_file_invalid_yaml(session_loader: SessionLoader, tmp_path: Path) -> None:
    """Test reading invalid YAML session file."""
    session_file = tmp_path / "test.mbps"
    session_file.write_text("invalid yaml: [", encoding="utf-8")

    with pytest.raises(yaml.YAMLError):
        session_loader._read_session_file(session_file)


def test_session_loader_read_session_file_not_found(session_loader: SessionLoader) -> None:
    """Test reading non-existent session file."""
    with pytest.raises(FileNotFoundError):
        session_loader._read_session_file(Path("/nonexistent/file.mbps"))


def test_session_loader_prepare_session(session_loader: SessionLoader, cfg_options) -> None:
    """Test session preparation."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = True

    data = {'version': 1}
    session_loader._prepare_session(data)

    session_loader.tagger.clear_session.assert_called_once()
    assert session_loader.tagger._restoring_session is True


def test_session_loader_prepare_session_safe_restore_disabled(session_loader: SessionLoader, cfg_options) -> None:
    """Test session preparation with safe restore disabled."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = False

    data = {'version': 1}
    session_loader._prepare_session(data)

    session_loader.tagger.clear_session.assert_called_once()
    # When safe restore is disabled, _restoring_session should not be set to True
    # (it might exist from previous tests, but should not be True)
    if hasattr(session_loader.tagger, '_restoring_session'):
        assert session_loader.tagger._restoring_session is not True


def test_session_loader_restore_options(session_loader: SessionLoader, cfg_options) -> None:
    """Test restoring configuration options."""
    # The cfg_options fixture already sets the default values

    options = {
        'rename_files': True,
        'move_files': True,
        'dont_write_tags': True,
    }

    session_loader._restore_options(options)

    cfg = picard_config.get_config()
    assert cfg.setting['rename_files'] is True
    assert cfg.setting['move_files'] is True
    assert cfg.setting['dont_write_tags'] is True


@patch("picard.session.session_loader.get_config")
def test_session_loader_restore_options_with_defaults(session_loader: SessionLoader, mock_get_config) -> None:
    """Test restoring configuration options with default values."""
    config_mock = Mock()
    config_mock.setting = {
        'rename_files': False,
        'move_files': False,
        'dont_write_tags': False,
    }
    mock_get_config.return_value = config_mock

    # Empty options should use current config values
    options = {}

    session_loader._restore_options(options)

    assert config_mock.setting['rename_files'] is False
    assert config_mock.setting['move_files'] is False
    assert config_mock.setting['dont_write_tags'] is False


def test_session_loader_group_items_by_location(session_loader: SessionLoader) -> None:
    """Test grouping items by location type."""
    items = [
        {
            'file_path': "/test/unclustered.mp3",
            'location': {'type': "unclustered"},
        },
        {
            'file_path': "/test/cluster.mp3",
            'location': {'type': "cluster", 'cluster_title': "Album", 'cluster_artist': "Artist"},
        },
        {
            'file_path': "/test/track.mp3",
            'location': {'type': "track", 'album_id': "album-123", 'recording_id': "recording-456"},
        },
        {
            'file_path': "/test/unmatched.mp3",
            'location': {'type': "album_unmatched", 'album_id': "album-789"},
        },
        {
            'file_path': "/test/nat.mp3",
            'location': {'type': "nat", 'recording_id': "recording-999"},
        },
    ]

    grouped = session_loader._group_items_by_location(items)

    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "unclustered.mp3"

    assert len(grouped.by_cluster) == 1
    assert ("Album", "Artist") in grouped.by_cluster

    assert "album-123" in grouped.by_album
    assert len(grouped.by_album['album-123'].tracks) == 1

    assert "album-789" in grouped.by_album
    assert len(grouped.by_album['album-789'].unmatched) == 1

    assert len(grouped.nat_items) == 1
    assert grouped.nat_items[0][1] == "recording-999"


def test_session_loader_group_items_by_location_unknown_type(session_loader: SessionLoader) -> None:
    """Test grouping items with unknown location type."""
    items = [
        {
            'file_path': "/test/unknown.mp3",
            'location': {'type': "unknown_type"},
        },
    ]

    grouped = session_loader._group_items_by_location(items)

    # Unknown types should be treated as unclustered
    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "unknown.mp3"


def test_session_loader_group_items_by_location_missing_location(session_loader: SessionLoader) -> None:
    """Test grouping items with missing location."""
    items = [
        {
            'file_path': "/test/no_location.mp3",
        },
    ]

    grouped = session_loader._group_items_by_location(items)

    # Missing location should default to unclustered
    assert len(grouped.unclustered) == 1
    assert Path(grouped.unclustered[0]).name == "no_location.mp3"


def test_session_loader_extract_metadata(session_loader: SessionLoader) -> None:
    """Test extracting metadata from session items."""
    items = [
        {
            'file_path': "/test/file1.mp3",
            'metadata': {'tags': {'title': ["Song 1"], 'artist': ["Artist 1"]}},
        },
        {
            'file_path': "/test/file2.mp3",
            # No metadata
        },
        {
            'file_path': "/test/file3.mp3",
            'metadata': {'tags': {'title': ["Song 3"]}},
        },
    ]

    metadata_map = session_loader._extract_metadata(items)

    assert len(metadata_map) == 2
    assert Path("/test/file1.mp3") in metadata_map
    assert Path("/test/file3.mp3") in metadata_map
    assert metadata_map[Path("/test/file1.mp3")]['title'] == ["Song 1"]


def test_session_loader_extract_metadata_empty_items(session_loader: SessionLoader) -> None:
    """Test extracting metadata from empty items list."""
    metadata_map = session_loader._extract_metadata([])

    assert len(metadata_map) == 0


def test_session_loader_extract_metadata_no_metadata(session_loader: SessionLoader) -> None:
    """Test extracting metadata when no items have metadata."""
    items = [
        {'file_path': "/test/file1.mp3"},
        {'file_path': "/test/file2.mp3"},
    ]

    metadata_map = session_loader._extract_metadata(items)

    assert len(metadata_map) == 0


def test_session_loader_load_unmatched_albums(session_loader: SessionLoader) -> None:
    """Test loading unmatched albums."""
    unmatched_album_ids = ["album-123", "album-456"]

    album_mock1 = Mock(spec=Album)
    album_mock2 = Mock(spec=Album)
    session_loader.tagger.load_album.side_effect = [album_mock1, album_mock2]

    session_loader._load_unmatched_albums(unmatched_album_ids)

    assert session_loader.loaded_albums['album-123'] == album_mock1
    assert session_loader.loaded_albums['album-456'] == album_mock2
    assert session_loader.tagger.load_album.call_count == 2


def test_session_loader_load_unmatched_albums_empty_list(session_loader: SessionLoader) -> None:
    """Test loading unmatched albums with empty list."""
    session_loader._load_unmatched_albums([])

    assert len(session_loader.loaded_albums) == 0
    session_loader.tagger.load_album.assert_not_called()


def test_session_loader_load_albums(session_loader: SessionLoader) -> None:
    """Test loading albums."""
    grouped_items = GroupedItems(
        unclustered=[],
        by_cluster={},
        by_album={'album-123': AlbumItems(unmatched=[], tracks=[]), 'album-456': AlbumItems(unmatched=[], tracks=[])},
        nat_items=[],
    )

    album_mock1 = Mock(spec=Album)
    album_mock2 = Mock(spec=Album)

    # Use a function to return the appropriate mock based on the album_id
    def load_album_side_effect(album_id):
        if album_id == "album-123":
            return album_mock1
        elif album_id == "album-456":
            return album_mock2
        return Mock(spec=Album)

    session_loader.tagger.load_album.side_effect = load_album_side_effect

    session_loader._load_albums(grouped_items)

    assert session_loader.loaded_albums['album-123'] == album_mock1
    assert session_loader.loaded_albums['album-456'] == album_mock2


def test_session_loader_load_albums_no_albums(session_loader: SessionLoader) -> None:
    """Test loading albums when no albums are needed."""
    grouped_items = GroupedItems(
        unclustered=[],
        by_cluster={},
        by_album={},
        nat_items=[],
    )

    session_loader._load_albums(grouped_items)

    assert len(session_loader.loaded_albums) == 0
    session_loader.tagger.load_album.assert_not_called()


def test_session_loader_load_album_files(session_loader: SessionLoader) -> None:
    """Test loading files into albums."""
    album_mock = Mock(spec=Album)
    album_mock.unmatched_files = Mock()
    session_loader.loaded_albums = {'album-123': album_mock}

    by_album = {
        'album-123': AlbumItems(
            unmatched=[Path("/test/unmatched.mp3")],
            tracks=[(Path("/test/track.mp3"), "recording-456")],
        )
    }

    with patch.object(session_loader.track_mover, "move_files_to_tracks") as mock_move:
        session_loader._load_album_files(by_album)

    session_loader.tagger.add_files.assert_called_once()
    mock_move.assert_called_once_with(album_mock, [(Path("/test/track.mp3"), "recording-456")])


def test_session_loader_load_album_files_no_files(session_loader: SessionLoader) -> None:
    """Test loading album files when no files are present."""
    album_mock = Mock(spec=Album)
    session_loader.loaded_albums = {'album-123': album_mock}

    by_album = {'album-123': AlbumItems(unmatched=[], tracks=[])}

    session_loader._load_album_files(by_album)

    session_loader.tagger.add_files.assert_not_called()


def test_session_loader_apply_track_overrides(session_loader: SessionLoader) -> None:
    """Test applying track-level overrides."""
    album_mock = Mock(spec=Album)
    track_mock = Mock()
    track_mock.id = "track-123"
    track_mock.metadata = {}  # Add metadata dict
    album_mock.tracks = [track_mock]

    overrides = {'track-123': {'title': ["New Title"], 'artist': ["New Artist"]}}

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._apply_track_overrides(album_mock, overrides)

    assert track_mock.metadata['title'] == ["New Title"]
    assert track_mock.metadata['artist'] == ["New Artist"]
    track_mock.update.assert_called_once()


def test_session_loader_apply_track_overrides_track_not_found(session_loader: SessionLoader) -> None:
    """Test applying track overrides when track is not found."""
    album_mock = Mock(spec=Album)
    track_mock = Mock()
    track_mock.id = "track-123"
    album_mock.tracks = [track_mock]

    overrides = {'track-999': {'title': ["New Title"]}}  # Non-existent track

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._apply_track_overrides(album_mock, overrides)

    # Should not modify existing track
    track_mock.update.assert_not_called()


def test_session_loader_apply_album_overrides(session_loader: SessionLoader) -> None:
    """Test applying album-level overrides."""
    album_mock = Mock(spec=Album)
    album_mock.metadata = {}  # Add metadata dict

    overrides = {'albumartist': ["New Artist"], 'album': ["New Album"]}

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._apply_album_overrides(album_mock, overrides)

    assert album_mock.metadata['albumartist'] == ["New Artist"]
    assert album_mock.metadata['album'] == ["New Album"]
    album_mock.update.assert_called_once_with(update_tracks=False)


def test_session_loader_schedule_metadata_application(session_loader: SessionLoader, mock_single_shot) -> None:
    """Test scheduling metadata application."""
    metadata_map = {Path("/test/file.mp3"): Metadata()}

    with patch("PyQt6.QtCore.QTimer.singleShot", mock_single_shot):
        session_loader._schedule_metadata_application(metadata_map)

    mock_single_shot.assert_called_once()


def test_session_loader_schedule_metadata_application_empty_map(
    session_loader: SessionLoader, mock_single_shot
) -> None:
    """Test scheduling metadata application with empty map."""
    with patch("PyQt6.QtCore.QTimer.singleShot", mock_single_shot):
        session_loader._schedule_metadata_application({})

    mock_single_shot.assert_called_once()


def test_session_loader_unset_restoring_flag_when_idle_safe_restore_disabled(
    session_loader: SessionLoader, cfg_options
) -> None:
    """Test unsetting restoring flag when safe restore is disabled."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = False

    session_loader._unset_restoring_flag_when_idle()

    # Should not check pending files or web requests when safe restore is disabled
    # The method should return early without checking attributes


def test_session_loader_unset_restoring_flag_when_idle_pending_files(
    session_loader: SessionLoader, mock_single_shot, cfg_options
) -> None:
    """Test unsetting restoring flag when files are still pending."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = True

    session_loader.tagger._pending_files_count = 1
    session_loader.tagger.webservice.num_pending_web_requests = 0

    with patch("PyQt6.QtCore.QTimer.singleShot", mock_single_shot):
        session_loader._unset_restoring_flag_when_idle()

    # Should schedule another check
    mock_single_shot.assert_called_once()


def test_session_loader_unset_restoring_flag_when_idle_pending_requests(
    session_loader: SessionLoader, mock_single_shot, cfg_options
) -> None:
    """Test unsetting restoring flag when web requests are still pending."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = True

    session_loader.tagger._pending_files_count = 0
    session_loader.tagger.webservice.num_pending_web_requests = 1

    with patch("PyQt6.QtCore.QTimer.singleShot", mock_single_shot):
        session_loader._unset_restoring_flag_when_idle()

    # Should schedule another check
    mock_single_shot.assert_called_once()


def test_session_loader_unset_restoring_flag_when_idle_all_done(session_loader: SessionLoader, cfg_options) -> None:
    """Test unsetting restoring flag when all operations are complete."""
    # Set the config value for this test
    cfg = picard_config.get_config()
    cfg.setting['session_safe_restore'] = True

    session_loader.tagger._pending_files_count = 0
    session_loader.tagger.webservice.num_pending_web_requests = 0

    session_loader._unset_restoring_flag_when_idle()

    # Should unset the flag
    assert session_loader.tagger._restoring_session is False


def test_session_loader_finalize_loading(session_loader: SessionLoader, mock_single_shot) -> None:
    """Test finalizing the loading process."""
    with patch("PyQt6.QtCore.QTimer.singleShot", mock_single_shot):
        session_loader.finalize_loading()

    mock_single_shot.assert_called_once()


def test_session_loader_initialization() -> None:
    """Test SessionLoader initialization."""
    tagger_mock = Mock()
    loader = SessionLoader(tagger_mock)

    assert loader.tagger == tagger_mock
    assert loader.loaded_albums == {}
    assert loader._saved_expanded_albums is None
    assert hasattr(loader, 'track_mover')


def test_session_loader_ensure_album_visible(session_loader: SessionLoader) -> None:
    """Test ensuring album is visible and expanded."""
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    ui_item_mock = Mock()
    album_mock.ui_item = ui_item_mock

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._saved_expanded_albums = {"album-123"}
    session_loader._ensure_album_visible(album_mock)

    album_mock.update.assert_called_once_with(update_tracks=True)
    ui_item_mock.setExpanded.assert_called_once_with(True)


def test_session_loader_ensure_album_visible_no_saved_state(session_loader: SessionLoader) -> None:
    """Test ensuring album is visible when no saved expansion state."""
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    ui_item_mock = Mock()
    album_mock.ui_item = ui_item_mock

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._saved_expanded_albums = None
    session_loader._ensure_album_visible(album_mock)

    album_mock.update.assert_called_once_with(update_tracks=True)
    ui_item_mock.setExpanded.assert_called_once_with(True)


def test_session_loader_ensure_album_visible_no_ui_item(session_loader: SessionLoader) -> None:
    """Test ensuring album is visible when album has no UI item."""
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.ui_item = None

    # Mock run_when_loaded to call callback immediately
    def run_callback(callback):
        callback()

    album_mock.run_when_loaded.side_effect = run_callback

    session_loader._ensure_album_visible(album_mock)

    album_mock.update.assert_called_once_with(update_tracks=True)
    # Should not crash when ui_item is None

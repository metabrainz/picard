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

"""Tests for track mover."""

from pathlib import Path
from unittest.mock import Mock, patch

from picard.album import Album
from picard.file import File
from picard.session.constants import SessionConstants
from picard.session.track_mover import TrackMover

import pytest


@pytest.fixture
def track_mover() -> TrackMover:
    """Provide a TrackMover instance."""
    tagger_mock = Mock()
    return TrackMover(tagger_mock)


@pytest.fixture
def mock_album() -> Mock:
    """Provide a mock album instance."""
    album_mock = Mock(spec=Album)
    album_mock.id = "album-123"
    album_mock.tracks = []
    return album_mock


def test_track_mover_move_files_to_tracks(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test moving files to tracks."""
    track_specs = [(Path("/test/file1.mp3"), "recording-123"), (Path("/test/file2.mp3"), "recording-456")]

    with patch("picard.session.track_mover.RetryHelper"):
        track_mover.move_files_to_tracks(mock_album, track_specs)

        mock_album.run_when_loaded.assert_called_once()


def test_track_mover_schedule_move(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test scheduling file moves."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        mock_retry_helper.retry_until.assert_called_once()


def test_track_mover_move_file_to_nat(track_mover: TrackMover) -> None:
    """Test moving file to NAT."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_file_to_nat(fpath, recording_id)

        mock_retry_helper.retry_until.assert_called_once()


def test_track_mover_schedule_move_file_pending(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test scheduling move when file is in PENDING state."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file in PENDING state
    file_mock = Mock(spec=File)
    file_mock.state = File.PENDING
    track_mover.tagger.files.get.return_value = file_mock

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper"):
        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        # Should not attempt move when file is pending
        file_mock.move.assert_not_called()


def test_track_mover_schedule_move_file_not_found(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test scheduling move when file is not found."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file not found
    track_mover.tagger.files.get.return_value = None

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        # Should not attempt move when file is not found
        mock_retry_helper.retry_until.assert_called_once()


def test_track_mover_schedule_move_track_not_found(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test scheduling move when track is not found."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file ready
    file_mock = Mock(spec=File)
    file_mock.state = 0  # Not PENDING
    track_mover.tagger.files.get.return_value = file_mock

    # Mock album with no matching track
    mock_album.tracks = []  # No tracks

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper"):
        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        # Should not attempt move when track is not found
        file_mock.move.assert_not_called()


def test_track_mover_schedule_move_success(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test successful file move to track."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file ready
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)
    track_mover.tagger.files.get.return_value = file_mock

    # Mock track
    track_mock = Mock()
    track_mock.id = recording_id
    mock_album.tracks = [track_mock]

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        # Mock retry_until to call the action function immediately if condition is met
        def mock_retry_until(condition_fn, action_fn, delay_ms):
            if condition_fn():
                action_fn()

        mock_retry_helper.retry_until.side_effect = mock_retry_until

        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        # Should attempt move when both file and track are ready
        file_mock.move.assert_called_once_with(track_mock)


def test_track_mover_move_file_to_nat_file_pending(track_mover: TrackMover) -> None:
    """Test moving file to NAT when file is in PENDING state."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file in PENDING state
    file_mock = Mock(spec=File)
    file_mock.state = File.PENDING
    track_mover.tagger.files.get.return_value = file_mock

    with patch("picard.session.track_mover.RetryHelper"):
        track_mover.move_file_to_nat(fpath, recording_id)

        # Should not attempt NAT move when file is pending
        track_mover.tagger.move_file_to_nat.assert_not_called()


def test_track_mover_move_file_to_nat_file_not_found(track_mover: TrackMover) -> None:
    """Test moving file to NAT when file is not found."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file not found
    track_mover.tagger.files.get.return_value = None

    with patch("picard.session.track_mover.RetryHelper"):
        track_mover.move_file_to_nat(fpath, recording_id)

        # Should not attempt NAT move when file is not found
        track_mover.tagger.move_file_to_nat.assert_not_called()


def test_track_mover_move_file_to_nat_success(track_mover: TrackMover) -> None:
    """Test successful file move to NAT."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file ready
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)
    track_mover.tagger.files.get.return_value = file_mock

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        # Mock retry_until to call the action function immediately if condition is met
        def mock_retry_until(condition_fn, action_fn, delay_ms):
            if condition_fn():
                action_fn()

        mock_retry_helper.retry_until.side_effect = mock_retry_until

        track_mover.move_file_to_nat(fpath, recording_id)

        # Should attempt NAT move when file is ready
        track_mover.tagger.move_file_to_nat.assert_called_once_with(file_mock, recording_id)


def test_track_mover_move_files_to_tracks_empty_list(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test moving files to tracks with empty list."""
    track_mover.move_files_to_tracks(mock_album, [])

    mock_album.run_when_loaded.assert_called_once()


def test_track_mover_move_files_to_tracks_multiple_files(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test moving multiple files to tracks."""
    track_specs = [
        (Path("/test/file1.mp3"), "recording-123"),
        (Path("/test/file2.mp3"), "recording-456"),
        (Path("/test/file3.mp3"), "recording-789"),
    ]

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_files_to_tracks(mock_album, track_specs)

        # Should schedule moves for all files
        assert mock_retry_helper.retry_until.call_count == 3


def test_track_mover_initialization() -> None:
    """Test TrackMover initialization."""
    tagger_mock = Mock()
    mover = TrackMover(tagger_mock)

    assert mover.tagger == tagger_mock


def test_track_mover_retry_until_condition_check(track_mover: TrackMover, mock_album: Mock) -> None:
    """Test that retry_until is called with correct condition function."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file ready
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)
    track_mover.tagger.files.get.return_value = file_mock

    # Mock track
    track_mock = Mock()
    track_mock.id = recording_id
    mock_album.tracks = [track_mock]

    # Mock the run_when_loaded to call the callback immediately
    def run_callback(callback):
        callback()

    mock_album.run_when_loaded.side_effect = run_callback

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_files_to_tracks(mock_album, [(fpath, recording_id)])

        # Verify retry_until was called with correct parameters
        mock_retry_helper.retry_until.assert_called_once()
        call_args = mock_retry_helper.retry_until.call_args

        # Check that condition function returns True when file and track are ready
        condition_fn = call_args[1]['condition_fn']
        assert condition_fn() is True

        # Check that action function is provided
        action_fn = call_args[1]['action_fn']
        assert callable(action_fn)

        # Check delay parameter
        assert call_args[1]['delay_ms'] == SessionConstants.FAST_RETRY_DELAY_MS


def test_track_mover_retry_until_condition_check_nat(track_mover: TrackMover) -> None:
    """Test that retry_until is called with correct condition function for NAT moves."""
    fpath = Path("/test/file.mp3")
    recording_id = "recording-123"

    # Mock file ready
    file_mock = Mock(spec=File)
    file_mock.state = 1  # Not PENDING (PENDING = 0)
    track_mover.tagger.files.get.return_value = file_mock

    with patch("picard.session.track_mover.RetryHelper") as mock_retry_helper:
        track_mover.move_file_to_nat(fpath, recording_id)

        # Verify retry_until was called with correct parameters
        mock_retry_helper.retry_until.assert_called_once()
        call_args = mock_retry_helper.retry_until.call_args

        # Check that condition function returns True when file is ready
        condition_fn = call_args[1]['condition_fn']
        assert condition_fn() is True

        # Check that action function is provided
        action_fn = call_args[1]['action_fn']
        assert callable(action_fn)

        # Check delay parameter
        assert call_args[1]['delay_ms'] == SessionConstants.DEFAULT_RETRY_DELAY_MS

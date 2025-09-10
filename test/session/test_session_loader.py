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

import picard.config as picard_config
from picard.metadata import Metadata
from picard.session.session_loader import SessionLoader

import pytest


@pytest.fixture
def session_loader() -> SessionLoader:
    """Provide a SessionLoader instance."""
    tagger_mock = Mock()
    return SessionLoader(tagger_mock)


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


def _write_session(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "session.mbps"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_session_loader_requests_allowed(tmp_path: Path, mock_single_shot, cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_no_mb_requests_on_load'] = False
    cfg.setting['session_safe_restore'] = False

    tagger = Mock()
    tagger.albums = {}

    loader = SessionLoader(tagger)

    data = {
        'version': 1,
        'options': {},
        'items': [],
        'unmatched_albums': ["album-123"],
        'expanded_albums': [],
    }
    path = _write_session(tmp_path, data)

    album_mock = Mock()
    album_mock.unmatched_files = Mock()
    album_mock.run_when_loaded = Mock(side_effect=lambda cb: cb())
    tagger.load_album.return_value = album_mock

    loader.load_from_path(path)

    tagger.load_album.assert_called_once_with("album-123")


def test_session_loader_requests_suppressed(tmp_path: Path, mock_single_shot, cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_no_mb_requests_on_load'] = True
    cfg.setting['session_safe_restore'] = False

    tagger = Mock()
    tagger.albums = {}

    loader = SessionLoader(tagger)

    data = {
        'version': 1,
        'options': {},
        'items': [],
        'unmatched_albums': ["album-123"],
        'expanded_albums': [],
    }
    path = _write_session(tmp_path, data)

    loader.load_from_path(path)

    tagger.load_album.assert_not_called()


def test_session_loader_cached_album_refresh_allowed(tmp_path: Path, mock_single_shot, cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_no_mb_requests_on_load'] = False
    cfg.setting['session_safe_restore'] = False

    tagger = Mock()
    album_mock = Mock()
    album_mock.unmatched_files = Mock()
    album_mock.run_when_loaded = Mock(side_effect=lambda cb: cb())
    tagger.albums = {"album-123": album_mock}

    loader = SessionLoader(tagger)

    data = {
        'version': 1,
        'options': {},
        'mb_cache': {"album-123": {"id": "album-123"}},
        'items': [],
        'expanded_albums': ["album-123"],
    }
    path = _write_session(tmp_path, data)

    loader.load_from_path(path)

    # With network allowed and cache present, album.load() should be scheduled
    assert album_mock.load.called


def test_session_loader_cached_album_no_refresh_when_suppressed(tmp_path: Path, mock_single_shot, cfg_options) -> None:
    cfg = picard_config.get_config()
    cfg.setting['session_no_mb_requests_on_load'] = True
    cfg.setting['session_safe_restore'] = False

    tagger = Mock()
    album_mock = Mock()
    album_mock.unmatched_files = Mock()
    album_mock.run_when_loaded = Mock(side_effect=lambda cb: cb())
    tagger.albums = {"album-123": album_mock}

    loader = SessionLoader(tagger)

    data = {
        'version': 1,
        'options': {},
        'mb_cache': {"album-123": {"id": "album-123"}},
        'items': [],
        'expanded_albums': ["album-123"],
    }
    path = _write_session(tmp_path, data)

    loader.load_from_path(path)

    assert not album_mock.load.called

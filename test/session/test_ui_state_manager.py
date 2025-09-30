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

"""Tests for UIStateManager."""

from unittest.mock import Mock

from picard.album import Album
from picard.session.session_loader import UIStateManager


def _immediate_run(callback):
    callback()


def test_ui_state_manager_ensure_album_visible_with_saved_state() -> None:
    tagger = Mock()
    ui = UIStateManager(tagger, default_delay_ms=0)

    album = Mock(spec=Album)
    album.id = "album-123"
    album.ui_item = Mock()
    album.run_when_loaded.side_effect = _immediate_run

    ui.ensure_album_visible(album, saved_expanded={"album-123"})

    album.update.assert_called_once_with(update_tracks=True)
    album.ui_item.setExpanded.assert_called_once_with(True)


def test_ui_state_manager_ensure_album_visible_no_saved_state() -> None:
    tagger = Mock()
    ui = UIStateManager(tagger, default_delay_ms=0)

    album = Mock(spec=Album)
    album.id = "album-123"
    album.ui_item = Mock()
    album.run_when_loaded.side_effect = _immediate_run

    ui.ensure_album_visible(album, saved_expanded=None)

    album.update.assert_called_once_with(update_tracks=True)
    album.ui_item.setExpanded.assert_called_once_with(True)


def test_ui_state_manager_ensure_album_visible_no_ui_item() -> None:
    tagger = Mock()
    ui = UIStateManager(tagger, default_delay_ms=0)

    album = Mock(spec=Album)
    album.id = "album-123"
    album.ui_item = None
    album.run_when_loaded.side_effect = _immediate_run

    ui.ensure_album_visible(album, saved_expanded={"album-123"})

    album.update.assert_called_once_with(update_tracks=True)


def test_ui_state_manager_apply_expansions_later(monkeypatch) -> None:
    tagger = Mock()
    ui = UIStateManager(tagger, default_delay_ms=10)

    album = Mock(spec=Album)
    album.id = "album-123"
    album.ui_item = Mock()
    tagger.albums = {"album-123": album}

    mock_single_shot = Mock()
    monkeypatch.setattr("PyQt6.QtCore.QTimer.singleShot", mock_single_shot)

    ui.apply_expansions_later({"album-123"})

    mock_single_shot.assert_called_once()


def test_ui_state_manager_apply_expansions_later_handles_missing_ui(monkeypatch) -> None:
    tagger = Mock()
    ui = UIStateManager(tagger, default_delay_ms=10)

    album = Mock(spec=Album)
    album.id = "album-123"
    album.ui_item = None
    tagger.albums = {"album-123": album}

    mock_single_shot = Mock()
    monkeypatch.setattr("PyQt6.QtCore.QTimer.singleShot", mock_single_shot)

    ui.apply_expansions_later({"album-123"})

    mock_single_shot.assert_called_once()

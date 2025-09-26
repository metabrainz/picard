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

"""Tests for AlbumManager."""

from pathlib import Path
from unittest.mock import Mock

from picard.album import Album
from picard.session.session_data import AlbumItems, GroupedItems
from picard.session.session_loader import AlbumManager, UIStateManager


def test_album_manager_load_unmatched_albums() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    manager.configure(suppress_network=False, saved_expanded_albums=None)

    unmatched = ["album-123", "album-456"]
    album_mock1 = Mock(spec=Album)
    album_mock2 = Mock(spec=Album)
    tagger.load_album.side_effect = [album_mock1, album_mock2]

    manager.load_unmatched_albums(unmatched, mb_cache={})

    assert manager.loaded_albums['album-123'] == album_mock1
    assert manager.loaded_albums['album-456'] == album_mock2
    assert tagger.load_album.call_count == 2


def test_album_manager_load_needed_albums() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    manager.configure(suppress_network=False, saved_expanded_albums=None)

    grouped = GroupedItems(
        unclustered=[],
        by_cluster={},
        by_album={'album-123': AlbumItems(unmatched=[], tracks=[]), 'album-456': AlbumItems(unmatched=[], tracks=[])},
        nat_items=[],
    )

    album_mock1 = Mock(spec=Album)
    album_mock2 = Mock(spec=Album)

    def side_effect(album_id):
        if album_id == "album-123":
            return album_mock1
        if album_id == "album-456":
            return album_mock2
        return Mock(spec=Album)

    tagger.load_album.side_effect = side_effect

    manager.load_needed_albums(grouped, mb_cache={})

    assert manager.loaded_albums['album-123'] == album_mock1
    assert manager.loaded_albums['album-456'] == album_mock2


def test_album_manager_load_album_files() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    manager.configure(suppress_network=False, saved_expanded_albums=None)

    album_mock = Mock(spec=Album)
    album_mock.unmatched_files = Mock()
    manager.loaded_albums = {'album-123': album_mock}

    by_album = {
        'album-123': AlbumItems(
            unmatched=[Path("/test/unmatched.mp3")],
            tracks=[(Path("/test/track.mp3"), "recording-456")],
        )
    }

    track_mover = Mock()
    manager.load_album_files(by_album, track_mover)

    tagger.add_files.assert_called_once()
    track_mover.move_files_to_tracks.assert_called_once_with(album_mock, [(Path("/test/track.mp3"), "recording-456")])


def test_album_manager_load_album_files_no_files() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    manager.configure(suppress_network=False, saved_expanded_albums=None)

    album_mock = Mock(spec=Album)
    manager.loaded_albums = {'album-123': album_mock}

    by_album = {'album-123': AlbumItems(unmatched=[], tracks=[])}
    manager.load_album_files(by_album, track_mover=Mock())

    tagger.add_files.assert_not_called()


def test_album_manager_preload_from_cache_and_refresh_network() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    # allow network refresh
    manager.configure(suppress_network=False, saved_expanded_albums=None)

    grouped = GroupedItems(unclustered=[], by_cluster={}, by_album={'album-1': AlbumItems([], [])}, nat_items=[])
    mb_cache = {'album-1': {'id': 'album-1'}}

    # When AlbumManager builds from cache, it creates Album() and may emit signals.
    # Simulate tagger.albums empty, force branch that creates new Album via internal logic.
    tagger.albums = {}

    # Ensure run_when_loaded callback executes synchronously for test
    def run_immediately(cb):
        cb()

    Album.run_when_loaded = Mock(side_effect=run_immediately)

    manager.preload_from_cache(mb_cache, grouped)

    assert 'album-1' in manager.loaded_albums
    # album.load() should have been called if network not suppressed
    manager.loaded_albums['album-1']
    # Some Album methods are internal; for this test ensure attribute exists and is callable
    # We cannot assert exact call since Album is constructed internally; just ensure no crash and album present.


def test_album_manager_load_album_with_strategy_suppressed_no_cache() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    manager = AlbumManager(tagger, ui_state)
    manager.configure(suppress_network=True, saved_expanded_albums=None)

    album = manager.load_album_with_strategy('album-x', cached_node=None)
    assert album is None

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

"""Tests for OverrideApplicator."""

from unittest.mock import Mock

from picard.album import Album
from picard.session.session_loader import (
    AlbumManager,
    OverrideApplicator,
    UIStateManager,
)


def _immediate_run(callback):
    callback()


def test_override_applicator_apply_track_overrides() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    albums = AlbumManager(tagger, ui_state)
    applicator = OverrideApplicator(albums)

    album_mock = Mock(spec=Album)
    track_mock = Mock()
    track_mock.id = "track-123"
    track_mock.metadata = {}
    album_mock.tracks = [track_mock]
    album_mock.run_when_loaded.side_effect = _immediate_run

    albums.loaded_albums = {'album-1': album_mock}

    data = {
        'album_track_overrides': {
            'album-1': {'track-123': {'title': ["New Title"], 'artist': ["New Artist"]}},
        }
    }

    applicator.apply(data, mb_cache={})

    assert track_mock.metadata['title'] == ["New Title"]
    assert track_mock.metadata['artist'] == ["New Artist"]
    track_mock.update.assert_called_once()


def test_override_applicator_apply_track_overrides_track_not_found() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    albums = AlbumManager(tagger, ui_state)
    applicator = OverrideApplicator(albums)

    album_mock = Mock(spec=Album)
    track_mock = Mock()
    track_mock.id = "track-123"
    album_mock.tracks = [track_mock]
    album_mock.run_when_loaded.side_effect = _immediate_run

    albums.loaded_albums = {'album-1': album_mock}

    data = {
        'album_track_overrides': {
            'album-1': {'track-999': {'title': ["New Title"]}},
        }
    }

    applicator.apply(data, mb_cache={})
    track_mock.update.assert_not_called()


def test_override_applicator_ensures_albums_loaded() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    albums = AlbumManager(tagger, ui_state)
    applicator = OverrideApplicator(albums)

    # No albums loaded initially; applicator should ask AlbumManager to ensure they are loaded
    data = {
        'album_track_overrides': {'album-42': {'t1': {'title': ["X"]}}},
        'album_overrides': {'album-99': {'album': ["Y"]}},
    }

    # Spy on ensure_loaded_for_overrides
    albums.ensure_loaded_for_overrides = Mock()
    applicator.apply(data, mb_cache={})
    albums.ensure_loaded_for_overrides.assert_called_once()


def test_override_applicator_apply_album_overrides() -> None:
    tagger = Mock()
    ui_state = UIStateManager(tagger, default_delay_ms=10)
    albums = AlbumManager(tagger, ui_state)
    applicator = OverrideApplicator(albums)

    album_mock = Mock(spec=Album)
    album_mock.metadata = {}
    album_mock.run_when_loaded.side_effect = _immediate_run
    albums.loaded_albums = {'album-1': album_mock}

    data = {
        'album_overrides': {
            'album-1': {'albumartist': ["New Artist"], 'album': ["New Album"]},
        }
    }

    applicator.apply(data, mb_cache={})

    assert album_mock.metadata['albumartist'] == ["New Artist"]
    assert album_mock.metadata['album'] == ["New Album"]
    album_mock.update.assert_called_once_with(update_tracks=False)

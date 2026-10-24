# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from unittest.mock import (
    MagicMock,
    patch,
)

from PyQt6 import QtCore

import pytest

from picard.ui.player.player import Player


# QtMultimedia is an optional dependency and, even when the Python module is
# installed, importing it can still fail at runtime if its native libraries are
# missing (e.g. libpulse.so on a headless CI runner). picard.ui.player.player
# guards its own import the same way, so Player stays importable; mirror that
# here and skip the whole module when QtMultimedia cannot be loaded. Note that
# pytest.importorskip() only turns a *missing module* into a skip — it would let
# a deeper ImportError (missing shared library) abort collection instead.
try:
    from PyQt6.QtMultimedia import QMediaPlayer as RealQMediaPlayer
except ImportError as e:
    RealQMediaPlayer = None
    _qtmultimedia_import_error = str(e)
else:
    _qtmultimedia_import_error = None

pytestmark = pytest.mark.skipif(
    RealQMediaPlayer is None,
    reason=f"PyQt6.QtMultimedia unavailable: {_qtmultimedia_import_error}",
)


def _is_empty_qurl(arg) -> bool:
    return isinstance(arg, QtCore.QUrl) and arg.isEmpty()


@pytest.fixture()
def player(qapp):
    """A Player whose internal QMediaPlayer and QAudioOutput are mocked.

    This keeps the test headless (no real multimedia backend) while letting us
    assert exactly how the Player drives the underlying QMediaPlayer.
    """
    with (
        patch('picard.ui.player.player.QMediaPlayer') as mock_media_player_cls,
        patch('picard.ui.player.player.QAudioOutput'),
    ):
        # Keep the real PlaybackState enum so the Player's state-change handler
        # can still compare against QMediaPlayer.PlaybackState.* correctly.
        mock_media_player_cls.PlaybackState = RealQMediaPlayer.PlaybackState
        mock_media_player = MagicMock()
        mock_media_player.isAvailable.return_value = True
        mock_media_player_cls.return_value = mock_media_player
        p = Player()
        # Expose the mocked QMediaPlayer for assertions.
        p._mock_media_player = mock_media_player
        yield p


def _source_cleared(mock_media_player) -> bool:
    """True if setSource was called with an empty QUrl (handle released)."""
    return any(call.args and _is_empty_qurl(call.args[0]) for call in mock_media_player.setSource.call_args_list)


def test_stop_clears_media_source_synchronously(player):
    """Player.stop() must drop the media source without waiting for a signal.

    Regression test for PICARD-3517: the file handle held by the internal
    player must be released synchronously when stop() is called, so that a
    subsequent save/move (which runs right after on a background thread) does
    not hit a Windows file lock. Previously setSource("") was moved out of
    stop() into the async playbackStateChanged handler, so the handle was not
    released in time.
    """
    current_file = MagicMock()
    current_file.filename = '/music/song.mp3'
    player._current_file = current_file
    player._playback_state = Player.PlaybackState.PLAYING

    player.stop()

    assert _source_cleared(player._mock_media_player), (
        "stop() did not clear the media source synchronously; "
        "the file handle would still be held when the save/move runs"
    )


def test_release_file_clears_media_source_synchronously(player):
    """release_file() for the held file must release it synchronously."""
    current_file = MagicMock()
    current_file.filename = '/music/song.mp3'
    player._current_file = current_file
    player._playback_state = Player.PlaybackState.PLAYING

    player.release_file('/music/song.mp3')

    assert _source_cleared(player._mock_media_player), "release_file() did not clear the media source synchronously"


def test_release_file_ignores_other_files(player):
    """release_file() must not touch playback when a different file is held."""
    current_file = MagicMock()
    current_file.filename = '/music/playing.mp3'
    player._current_file = current_file
    player._playback_state = Player.PlaybackState.PLAYING

    player.release_file('/music/other.mp3')

    player._mock_media_player.stop.assert_not_called()
    assert not _source_cleared(player._mock_media_player)


def test_end_of_track_clears_media_source(player):
    """The end-of-track path still clears the source via the state handler.

    When a track finishes and the queue is empty, the QMediaPlayer transitions
    to StoppedState while the Player is not in PLAYING state, so the handler is
    responsible for releasing the handle.
    """
    player._current_file = None
    player._playback_state = Player.PlaybackState.STOPPED

    player._on_playback_state_changed(RealQMediaPlayer.PlaybackState.StoppedState)

    assert _source_cleared(player._mock_media_player)


def test_unmapped_playback_state_is_ignored(player):
    """An unrecognised playback state must not raise or change state.

    QMediaPlayer only defines Stopped/Playing/Paused today, but the handler
    must not raise UnboundLocalError should it ever receive another value: it
    should leave the Player state untouched and emit no signal.
    """
    player._playback_state = Player.PlaybackState.PLAYING
    received = []
    player.playback_state_changed.connect(received.append)

    # A sentinel value matching none of the known QMediaPlayer states.
    player._on_playback_state_changed(object())

    assert player._playback_state == Player.PlaybackState.PLAYING
    assert received == []


def test_play_next_clears_source_when_queue_empty(player):
    """Reaching the end of the queue must drop the last file's handle.

    When the last track finishes, _play_next() is invoked with an empty queue
    and takes the IndexError branch. The QMediaPlayer is already stopped, so
    the stop() there may emit no further state change; the source must be
    cleared explicitly so the file handle is released and a subsequent
    save/move is not blocked on Windows (PICARD-3517).
    """
    player._current_file = MagicMock()
    player._media_queue.clear()

    player._play_next()

    assert player._current_file is None
    assert _source_cleared(player._mock_media_player)

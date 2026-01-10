# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2019-2023, 2026 Philipp Wolfer
# Copyright (C) 2019-2025 Laurent Monin
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

from collections import deque

from PyQt6 import QtCore
from PyQt6.QtMultimedia import (
    QAudioOutput,
    QMediaPlayer,
)

from picard import log
from picard.config import get_config
from picard.file import File
from picard.i18n import gettext as _
from picard.util import iter_files_from_objects

from .util import (
    get_linear_volume,
    get_logarithmic_volume,
)


MIN_PLAYBACK_RATE = 0.5
MAX_PLAYBACK_RATE = 1.5


class Player(QtCore.QObject):
    playback_available = QtCore.pyqtSignal(bool)
    error = QtCore.pyqtSignal(object, str)
    playback_state_changed = QtCore.pyqtSignal(QMediaPlayer.PlaybackState)
    duration_changed = QtCore.pyqtSignal(int)
    position_changed = QtCore.pyqtSignal(int)
    playback_rate_changed = QtCore.pyqtSignal(float)
    volume_changed = QtCore.pyqtSignal(float)
    media_changed = QtCore.pyqtSignal(File)

    def __init__(self, parent):
        super().__init__(parent)
        self._toolbar = None
        self._selected_objects = []
        self._current_file = None
        self._media_queue = deque()
        self.is_playing = False
        self.is_stopped = False
        self.is_paused = False
        player = QMediaPlayer(parent)
        self._player = player
        if player.isAvailable():
            output = QAudioOutput()
            self._audio_output = output
            player.setAudioOutput(output)
            log.debug("Internal player: available, QMediaPlayer set up")

            # Connect signals
            player.durationChanged.connect(self.duration_changed.emit)
            player.positionChanged.connect(self.position_changed.emit)
            player.playbackRateChanged.connect(self.playback_rate_changed.emit)
            player.errorOccurred.connect(self._on_error)
            player.playbackStateChanged.connect(self._on_playback_state_changed)
            output.volumeChanged.connect(self._on_volume_changed)

            # Init from config
            config = get_config()
            self.volume = config.persist['mediaplayer_volume'] / 100.0
            self.playback_rate = config.persist['mediaplayer_playback_rate']
        else:
            log.warning("Internal player: unavailable")
            self._audio_output = None

    def save_settings(self):
        config = get_config()
        config.persist['mediaplayer_playback_rate'] = self.playback_rate
        config.persist['mediaplayer_volume'] = int(self.volume * 100)

    @property
    def available(self):
        return self._player.isAvailable()

    @property
    def playback_state(self) -> QMediaPlayer.PlaybackState:
        return self._player.playbackState()

    @property
    def position(self) -> int:
        """Playback position in milliseconds"""
        return self._player.position()

    @position.setter
    def position(self, position: int):
        """Set the playback position in milliseconds"""
        self._player.setPosition(position)

    @property
    def volume(self) -> float:
        """Playback volume in logarithmic scale"""
        if self._audio_output:
            volume = self._audio_output.volume()
            return get_logarithmic_volume(volume)
        else:
            return 0.0

    @volume.setter
    def volume(self, volume: float):
        """Convert to linear scale and set the volume

        The value must be given in logarithmic scale as a value between 0.0 and 1.0.
        """
        linear_volume = get_linear_volume(volume)
        log.debug('Internal player: Set volume %f -> linear %f', volume, linear_volume)
        if self._audio_output:
            self._audio_output.setVolume(linear_volume)

    @property
    def playback_rate(self) -> float:
        return self._player.playbackRate()

    @playback_rate.setter
    def playback_rate(self, playback_rate: float):
        """Set the playback rate.
        The value mist be between MIN_PLAYBACK_RATE and MAX_PLAYBACK_RATE. If the
        playback rate is outside this range it will be adjusted accordingly
        """
        playback_rate = min(max(playback_rate, MIN_PLAYBACK_RATE), MAX_PLAYBACK_RATE)
        self._player.setPlaybackRate(playback_rate)

    @property
    def current_file(self) -> File | None:
        return self._current_file

    def set_objects(self, objects):
        self._selected_objects = objects
        self.playback_available.emit(bool(objects))

    def play(self):
        """Play selected tracks with an internal player"""
        self._media_queue = deque(iter_files_from_objects(self._selected_objects))
        self._play_next()

    def pause(self, is_paused: bool):
        """Toggle pause of an internal player"""
        if is_paused:
            self._player.pause()
        else:
            self._player.play()

    def play_next(self):
        if self.is_playing:
            # Stop will automatically play the next track if queue is not empty
            self._player.stop()

    def _play_next(self):
        try:
            file = self._current_file = self._media_queue.popleft()
            next_uri = QtCore.QUrl.fromLocalFile(file.filename)
            self._player.setSource(next_uri)
            self.media_changed.emit(file)
            self._player.play()
        except IndexError:
            self._current_file = None
            self._player.stop()

    def _on_playback_state_changed(self, state):
        self.is_stopped = state == QMediaPlayer.PlaybackState.StoppedState
        self.is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.is_paused = state == QMediaPlayer.PlaybackState.PausedState

        # if the track stopped, but we have more in the queue, continue with next track.
        if self.is_stopped and self._media_queue:
            self._play_next()
        else:
            self.playback_state_changed.emit(state)

    def _on_volume_changed(self, volume):
        self.volume_changed.emit(get_logarithmic_volume(volume))

    def _on_error(self, error):
        if error == QMediaPlayer.Error.FormatError:
            msg = _("Internal player: The format of a media resource isn't (fully) supported")
        elif error == QMediaPlayer.Error.AccessDeniedError:
            msg = _("Internal player: There are not the appropriate permissions to play a media resource")
        else:
            msg = _("Internal player: %(error)s, %(message)s") % {
                'error': error,
                'message': self._player.errorString() if self._player else str(error),
            }
        self.error.emit(error, msg)

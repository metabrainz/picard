# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2019-2023 Philipp Wolfer
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from collections import deque

from PyQt6 import QtCore

from picard import log
from picard.const.sys import IS_MACOS
from picard.i18n import gettext as _
from picard.util import iter_files_from_objects

from .widgets import PlayerToolbar


try:
    from PyQt6 import QtMultimedia
except ImportError as e:
    qt_multimedia_available = False
    qt_multimedia_errmsg = e.msg
else:
    qt_multimedia_available = True
    qt_multimedia_errmsg = None


def get_logarithmic_volume(player_value):
    """Return logarithmic scale volume to set slider position"""
    return QtMultimedia.QAudio.convertVolume(
        player_value,
        QtMultimedia.QAudio.VolumeScale.LinearVolumeScale,
        QtMultimedia.QAudio.VolumeScale.LogarithmicVolumeScale)


def get_linear_volume(slider_value):
    """Return linear scale volume from slider position"""
    return QtMultimedia.QAudio.convertVolume(
        slider_value,
        QtMultimedia.QAudio.VolumeScale.LogarithmicVolumeScale,
        QtMultimedia.QAudio.VolumeScale.LinearVolumeScale)


class Player(QtCore.QObject):
    error = QtCore.pyqtSignal(object, str)

    def __init__(self, parent):
        super().__init__(parent)
        self._player = None
        self._toolbar = None
        self._selected_objects = []
        self._media_queue = deque()
        self.is_playing = False
        self.is_stopped = False
        self.is_paused = False
        if qt_multimedia_available:
            log.debug("Internal player: QtMultimedia available, initializing QMediaPlayer")
            player = QtMultimedia.QMediaPlayer(parent)
            if player.isAvailable():
                output = QtMultimedia.QAudioOutput()
                player.setAudioOutput(output)
                self.state_changed = player.playbackStateChanged
                self._logarithmic_volume = get_logarithmic_volume(output.volume())
                log.debug("Internal player: available, QMediaPlayer set up")
                self._player = player
                self._audio_output = output
                self._player.playbackStateChanged.connect(self._on_playback_state_changed)
                self._player.errorOccurred.connect(self._on_error)
            else:
                log.warning("Internal player: unavailable")
        else:
            log.warning("Internal player: unavailable, %s", qt_multimedia_errmsg)

    @property
    def available(self):
        return self._player is not None

    @property
    def toolbar(self):
        return self._toolbar

    def volume(self):
        return int(self._logarithmic_volume * 100)

    def playback_rate(self):
        return self._player.playbackRate()

    def create_toolbar(self):
        self._toolbar = PlayerToolbar(self, parent=self.parent())
        return self._toolbar

    def set_objects(self, objects):
        self._selected_objects = objects
        self._toolbar.play_action.setEnabled(bool(objects))

    def play(self):
        """Play selected tracks with an internal player"""
        self._media_queue = deque(
            QtCore.QUrl.fromLocalFile(file.filename)
            for file in iter_files_from_objects(self._selected_objects)
        )
        self._play_next()

    def _play_next(self):
        try:
            next_track = self._media_queue.popleft()
            self._player.setSource(next_track)
            self._player.play()
        except IndexError:
            self._player.stop()

    def _on_playback_state_changed(self, state):
        self.is_stopped = state == QtMultimedia.QMediaPlayer.PlaybackState.StoppedState
        self.is_playing = state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState
        self.is_paused = state == QtMultimedia.QMediaPlayer.PlaybackState.PausedState
        if self.is_stopped:
            self._play_next()

    def pause(self, is_paused):
        """Toggle pause of an internal player"""
        if is_paused:
            self._player.pause()
        else:
            self._player.play()

    def set_volume(self, logarithmic_volume):
        """Convert to linear scale and set the volume

        The value must be given in logarithmic scale as a value between 0 and 100.
        """
        self._logarithmic_volume = logarithmic_volume / 100.
        linear_volume = get_linear_volume(self._logarithmic_volume)
        log.debug('Internal player: Set volume %f -> linear %f', logarithmic_volume, linear_volume)
        self._audio_output.setVolume(linear_volume)

    def set_position(self, position):
        self._player.setPosition(position)

    def set_playback_rate(self, playback_rate):
        player = self._player
        player.setPlaybackRate(playback_rate)
        if not IS_MACOS:
            # Playback rate changes do not affect the current media playback on
            # Linux and does work unreliable on Windows.
            # Force playback restart to have the rate change applied immediately.
            player_state = player.playbackState()
            if player_state != QtMultimedia.QMediaPlayer.PlaybackState.StoppedState:
                position = player.position()
                player.stop()
                player.setPosition(position)
                if player_state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
                    player.play()
                elif player_state == QtMultimedia.QMediaPlayer.PlaybackState.PausedState:
                    player.pause()

    def _on_error(self, error):
        if error == QtMultimedia.QMediaPlayer.Error.FormatError:
            msg = _("Internal player: The format of a media resource isn't (fully) supported")
        elif error == QtMultimedia.QMediaPlayer.Error.AccessDeniedError:
            msg = _("Internal player: There are not the appropriate permissions to play a media resource")
        else:
            msg = _("Internal player: %(error)s, %(message)s") % {
                'error': error,
                'message': self._player.errorString(),
            }
        self.error.emit(error, msg)

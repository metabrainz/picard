# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
# Copyright (C) 2019 Laurent Monin
# Copyright (C) 2019 Timur Enikeev
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

import os

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import (
    config,
    log,
)
from picard.util import format_time


try:
    from PyQt5 import QtMultimedia
except ImportError as e:
    qt_multimedia_available = False
    qt_multimedia_errmsg = e.msg
else:
    qt_multimedia_available = True


def get_logarithmic_volume(player_value):
    """Return logarithmic scale volume to set slider position"""
    logarithmic_volume = QtMultimedia.QAudio.convertVolume(
        player_value / 100.,
        QtMultimedia.QAudio.LinearVolumeScale,
        QtMultimedia.QAudio.LogarithmicVolumeScale)
    return QtCore.qRound(logarithmic_volume * 100)


def get_linear_volume(slider_value):
    """Return linear scale volume from slider position"""
    linear_volume = QtMultimedia.QAudio.convertVolume(
        slider_value / 100.,
        QtMultimedia.QAudio.LogarithmicVolumeScale,
        QtMultimedia.QAudio.LinearVolumeScale)
    return QtCore.qRound(linear_volume * 100)


class Player(QtCore.QObject):
    error = QtCore.pyqtSignal(object, str)

    def __init__(self, parent):
        super().__init__(parent)
        self._player = None
        self._toolbar = None
        self._selected_objects = []
        if qt_multimedia_available:
            player = QtMultimedia.QMediaPlayer(parent)
            self.state_changed = player.stateChanged
            availability = player.availability()
            if availability == QtMultimedia.QMultimedia.Available:
                self._player = player
                self._player.error.connect(self._on_error)
            elif availability == QtMultimedia.QMultimedia.ServiceMissing:
                log.warning("Internal player: unavailable, service is missing")
            else:
                log.warning("Internal player: unavailable, status=%d", availability)
        else:
            log.warning("Internal player: unavailable, %s", qt_multimedia_errmsg)

    @property
    def available(self):
        return self._player is not None

    @property
    def toolbar(self):
        return self._toolbar

    def volume(self):
        return self._player.volume()

    def playback_rate(self):
        return self._player.playbackRate()

    def create_toolbar(self):
        self._toolbar = PlayerToolbar(self.parent(), self)
        return self._toolbar

    def set_objects(self, objects):
        self._selected_objects = objects
        player_enabled = len(objects) > 0
        self._toolbar.play_action.setEnabled(player_enabled)

    def play(self):
        """Play selected tracks with an internal player"""
        self._player.stop()
        playlist = QtMultimedia.QMediaPlaylist(self)
        playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Sequential)
        playlist.addMedia([QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(file.filename))
                          for file in self.tagger.get_files_from_objects(self._selected_objects)])
        self._player.setPlaylist(playlist)
        self._player.play()

    def pause(self, is_paused):
        """Toggle pause of an internal player"""
        if is_paused:
            self._player.pause()
        else:
            self._player.play()

    def set_volume(self, slider_value):
        """Convert to linear scale and set"""
        self._player.setVolume(get_linear_volume(slider_value))

    def set_position(self, position):
        self._player.setPosition(position)

    def _on_error(self, error):
        if error == QtMultimedia.QMediaPlayer.FormatError:
            msg = _("Internal player: The format of a media resource isn't (fully) supported")
        elif error == QtMultimedia.QMediaPlayer.AccessDeniedError:
            msg = _("Internal player: There are not the appropriate permissions to play a media resource")
        elif error == QtMultimedia.QMediaPlayer.ServiceMissingError:
            msg = _("Internal player: A valid playback service was not found, playback cannot proceed")
        else:
            msg = _("Internal player: error, code=%d, msg=%s") % (error, self._player.errorString())
        self.error.emit(error, msg)


class PlayerToolbar(QtWidgets.QToolBar):
    def __init__(self, parent, player):
        super().__init__(_("Player"), parent)
        self.setObjectName("player_toolbar")

        self.player = player

        self.play_action = QtWidgets.QAction(self.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPlay), _("Play"), self)
        self.play_action.setStatusTip(_("Play selected files in an internal player"))
        self.play_action.setEnabled(False)
        self.play_action.triggered.connect(self.play)

        self.pause_action = QtWidgets.QAction(self.style().standardIcon(
            QtWidgets.QStyle.SP_MediaPause), _("Pause"), self)
        self.pause_action.setToolTip(_("Pause/resume"))
        self.pause_action.setStatusTip(_("Pause or resume playing with an internal player"))
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(False)
        self.pause_action.setEnabled(False)
        self.pause_action.triggered.connect(self.player.pause)
        self.player.state_changed.connect(self.pause_action.setEnabled)

        self._add_toolbar_action(self.play_action)
        self._add_toolbar_action(self.pause_action)

        self.progress_slider = QtWidgets.QSlider(self)
        self.progress_slider.setOrientation(QtCore.Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.player.set_position)
        self.media_name_label = QtWidgets.QLabel(self)
        self.media_name_label.setAlignment(QtCore.Qt.AlignCenter)

        slider_container = QtWidgets.QWidget(self)
        hbox = QtWidgets.QHBoxLayout(slider_container)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.position_label = QtWidgets.QLabel("0:00", self)
        self.duration_label = QtWidgets.QLabel(format_time(0), self)
        hbox.addWidget(self.position_label)
        hbox.addWidget(self.progress_slider)
        hbox.addWidget(self.duration_label)

        progress_widget = QtWidgets.QWidget(self)
        vbox = QtWidgets.QVBoxLayout(progress_widget)
        vbox.addWidget(slider_container)
        vbox.addWidget(self.media_name_label)
        self.addWidget(progress_widget)

        self.playback_speed_action = QtWidgets.QAction('', self)
        self.set_playback_rate(config.persist["mediaplayer_playback_rate"])
        self.playback_speed_action.triggered.connect(self.show_playback_rate_popover)
        self._add_toolbar_action(self.playback_speed_action)

        self.volume_slider = QtWidgets.QSlider(self)
        self.volume_slider.setOrientation(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.valueChanged.connect(self.player.set_volume)
        self.volume_slider.setValue(
            get_logarithmic_volume(config.persist["mediaplayer_volume"]))
        self.volume_label = QtWidgets.QLabel(_("Volume"), self)
        self.volume_widget = QtWidgets.QWidget(self)
        vbox = QtWidgets.QVBoxLayout(self.volume_widget)
        vbox.addWidget(self.volume_slider)
        vbox.addWidget(self.volume_label)
        self.addWidget(self.volume_widget)

        self.player._player.durationChanged.connect(self.on_duration_changed)
        self.player._player.positionChanged.connect(self.on_position_changed)
        self.player._player.currentMediaChanged.connect(self.on_media_changed)

    def _add_toolbar_action(self, action):
        self.addAction(action)
        widget = self.widgetForAction(action)
        widget.setFocusPolicy(QtCore.Qt.TabFocus)
        widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect)

    def play(self):
        self.player.play()
        self.pause_action.setChecked(False)

    def show_playback_rate_popover(self):
        parent = self.widgetForAction(self.playback_speed_action)
        current_rate = self.player._player.playbackRate()
        speed_popover = PlaybackRatePopover(parent, current_rate)
        speed_popover.value_changed.connect(self.set_playback_rate)
        speed_popover.show()

    def set_playback_rate(self, playback_rate):
        label = _('%1.1f ×') % playback_rate
        self.player._player.setPlaybackRate(playback_rate)
        self.playback_speed_action.setText(label)

    def on_duration_changed(self, duration):
        self.progress_slider.setMaximum(duration)
        self.duration_label.setText(format_time(duration))

    def on_position_changed(self, position):
        self.progress_slider.setValue(position)
        self.position_label.setText(format_time(position, display_zero=True))

    def on_media_changed(self, media):
        if media.isNull():
            self.progress_slider.setEnabled(False)
        else:
            url = media.canonicalUrl().toString()
            self.media_name_label.setText(os.path.basename(url))
            self.progress_slider.setEnabled(True)

    def setToolButtonStyle(self, style):
        super().setToolButtonStyle(style)
        if style == QtCore.Qt.ToolButtonTextUnderIcon:
            self.volume_label.show()
        else:
            self.volume_label.hide()


class PlaybackRatePopover(QtWidgets.QFrame):
    value_changed = QtCore.pyqtSignal(float)

    def __init__(self, parent, value):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)

        vbox = QtWidgets.QVBoxLayout(self)
        speed_label = QtWidgets.QLabel(_("Playback speed"), self)
        speed_label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(speed_label)
        speed_slider = QtWidgets.QSlider(self)
        speed_slider.setOrientation(QtCore.Qt.Horizontal)
        # In 0.1 steps from 0.5 to 1.5
        multiplier = 10.0
        speed_slider.setMinimum(5)
        speed_slider.setMaximum(15)
        speed_slider.setSingleStep(1)
        speed_slider.setPageStep(1)
        speed_slider.setTickInterval(1)
        speed_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        speed_slider.setValue(value * multiplier)
        speed_slider.valueChanged.connect(lambda v: self.value_changed.emit(v / multiplier))
        vbox.addWidget(speed_slider)

    def show(self):
        super().show()
        self._update_position()

    def _update_position(self):
        parent = self.parent()
        x = -(self.width() - parent.width()) / 2
        y = -self.height()
        pos = parent.mapToGlobal(QtCore.QPoint(x, y))
        self.move(pos)

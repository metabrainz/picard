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
    QtGui,
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


def get_text_width(font, text):
    metrics = QtGui.QFontMetrics(font)
    size = metrics.size(QtCore.Qt.TextSingleLine, text)
    return size.width()


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
        self.setAllowedAreas(QtCore.Qt.TopToolBarArea
            | QtCore.Qt.BottomToolBarArea
            | QtCore.Qt.NoToolBarArea)

        self.player = player
        self.media_name = ''

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
        self.progress_slider.setMinimumWidth(30)
        self.progress_slider.sliderMoved.connect(self.player.set_position)
        self.media_name_label = QtWidgets.QLabel(self)
        self.media_name_label.setAlignment(QtCore.Qt.AlignCenter)

        slider_container = QtWidgets.QWidget(self)
        hbox = QtWidgets.QHBoxLayout(slider_container)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.position_label = QtWidgets.QLabel("0:00", self)
        self.duration_label = QtWidgets.QLabel(format_time(0), self)
        min_duration_width = get_text_width(self.position_label.font(), "8:88")
        self.position_label.setMinimumWidth(min_duration_width)
        self.duration_label.setMinimumWidth(min_duration_width)
        hbox.addWidget(self.position_label)
        hbox.addWidget(self.progress_slider)
        hbox.addWidget(self.duration_label)

        progress_widget = QtWidgets.QWidget(self)
        vbox = QtWidgets.QVBoxLayout(progress_widget)
        vbox.addWidget(slider_container)
        vbox.addWidget(self.media_name_label)
        self.addWidget(progress_widget)

        volume = get_logarithmic_volume(config.persist["mediaplayer_volume"])
        self.volume_button = VolumeControlButton(self, volume)
        self.volume_button.volume_changed.connect(self.player.set_volume)
        self.volume_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.volume_button)

        playback_rate = config.persist["mediaplayer_playback_rate"]
        self.playback_rate_button = PlaybackRateButton(self, playback_rate)
        self.playback_rate_button.playback_rate_changed.connect(self.set_playback_rate)
        self.playback_rate_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.playback_rate_button)

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

    def set_playback_rate(self, playback_rate):
        self.player._player.setPlaybackRate(playback_rate)
        # Playback rate changes do not affect the current media playback.
        # Force playback restart to have the rate change applied immediately.
        player = self.player._player
        player_state = player.state()
        if player_state != QtMultimedia.QMediaPlayer.StoppedState:
            position = player.position()
            player.stop()
            player.setPosition(position)
            if player_state == QtMultimedia.QMediaPlayer.PlayingState:
                player.play()
            elif player_state == QtMultimedia.QMediaPlayer.PausedState:
                player.pause()

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
            self.set_media_name(os.path.basename(url))
            self.progress_slider.setEnabled(True)

    def setToolButtonStyle(self, style):
        super().setToolButtonStyle(style)
        self.playback_rate_button.setToolButtonStyle(style)
        self.volume_button.setToolButtonStyle(style)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_media_name(self.media_name)

    def set_media_name(self, media_name):
        self.media_name = media_name
        media_label = self.media_name_label
        metrics = QtGui.QFontMetrics(media_label.font())
        elidedText = metrics.elidedText(media_name,
                                        QtCore.Qt.ElideRight,
                                        media_label.width())
        media_label.setText(elidedText)


class Popover(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)

    def show(self):
        super().show()
        self.update_position()

    def update_position(self):
        parent = self.parent()
        x = -(self.width() - parent.width()) / 2
        y = -self.height()
        pos = parent.mapToGlobal(QtCore.QPoint(x, y))
        self.move(pos)


class SliderPopover(Popover):
    value_changed = QtCore.pyqtSignal(float)

    def __init__(self, parent, label, value):
        super().__init__(parent)
        vbox = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(label, self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self.label)

        self.slider = QtWidgets.QSlider(self)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(lambda v: self.value_changed.emit(v))
        vbox.addWidget(self.slider)


class PlaybackRateButton(QtWidgets.QToolButton):
    playback_rate_changed = QtCore.pyqtSignal(float)

    multiplier = 10.0

    def __init__(self, parent, playback_rate):
        super().__init__(parent)
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PM_ButtonMargin)
        min_width = get_text_width(self.font(), _('%1.1f ×') % 8.8)
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.set_playback_rate(playback_rate)
        self.clicked.connect(self.show_popover)

    def show_popover(self):
        slider_value = self.playback_rate * self.multiplier
        popover = SliderPopover(self, _('Playback speed'), slider_value)
        # In 0.1 steps from 0.5 to 1.5
        popover.slider.setMinimum(5)
        popover.slider.setMaximum(15)
        popover.slider.setSingleStep(1)
        popover.slider.setPageStep(1)
        popover.slider.setTickInterval(1)
        popover.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        playback_rate = value / self.multiplier
        self.set_playback_rate(playback_rate)
        self.playback_rate_changed.emit(self.playback_rate)

    def set_playback_rate(self, playback_rate):
        self.playback_rate = playback_rate
        label = _('%1.1f ×') % playback_rate
        self.setText(label)

    def event(self, event):
        if event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y()
            # Incrementing repeatadly in 0.1 steps would cause floating point
            # rounding issues. Do the calculation in whole numbers to prevent this.
            new_rate = int(self.playback_rate * 10)
            if delta > 0:
                new_rate += 1
            elif delta < 0:
                new_rate -= 1
            new_rate = min(max(new_rate, 5), 15) / 10.0
            if new_rate != self.playback_rate:
                self.set_playback_rate(new_rate)
                self.playback_rate_changed.emit(new_rate)
            return True

        return super().event(event)


class VolumeControlButton(QtWidgets.QToolButton):
    volume_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent, volume):
        super().__init__(parent)
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaVolume)
        self.setIcon(icon)
        self.set_volume(volume)
        margins = self.getContentsMargins()
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PM_ButtonMargin)
        min_width = get_text_width(self.font(), '888%')
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.clicked.connect(self.show_popover)

    def show_popover(self):
        popover = SliderPopover(self, _('Volume'), self.volume)
        popover.slider.setMinimum(0)
        popover.slider.setMaximum(100)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        self.set_volume(value)
        self.volume_changed.emit(self.volume)

    def set_volume(self, volume):
        self.volume = volume
        label = _('%d%%') % volume
        self.setText(label)

    def event(self, event):
        if event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y()
            volume = self.volume
            if delta > 0:
                volume += 3
            elif delta < 0:
                volume -= 3
            volume = min(max(volume, 0), 100)
            if volume != self.volume:
                self.set_volume(volume)
                self.volume_changed.emit(volume)
            return True

        return super().event(event)

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Timur Enikeev
# Copyright (C) 2019-2023 Philipp Wolfer
# Copyright (C) 2019-2024 Laurent Monin
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
import locale
import os

from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import get_config
from picard.const.sys import IS_MACOS
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import (
    format_time,
    icontheme,
    iter_files_from_objects,
)

from picard.ui.widgets import (
    ClickableSlider,
    ElidedLabel,
    SliderPopover,
)


try:
    from PySide6 import QtMultimedia
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


def get_text_width(font, text):
    metrics = QtGui.QFontMetrics(font)
    size = metrics.size(QtCore.Qt.TextFlag.TextSingleLine, text)
    return size.width()


class Player(QtCore.QObject):
    error = QtCore.Signal(object, str)

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


class PlayerToolbar(QtWidgets.QToolBar):
    def __init__(self, player, parent=None):
        super().__init__(_("Player"), parent=parent)
        self.setObjectName('player_toolbar')
        self.setAllowedAreas(QtCore.Qt.ToolBarArea.TopToolBarArea
            | QtCore.Qt.ToolBarArea.BottomToolBarArea
            | QtCore.Qt.ToolBarArea.NoToolBarArea)

        self.player = player
        self.player.state_changed.connect(self.playback_state_changed)

        self.play_action = QtGui.QAction(icontheme.lookup('play'), _("Play"), self)
        play_tip = _("Play selected files")
        self.play_action.setToolTip(play_tip)
        self.play_action.setStatusTip(play_tip)
        self.play_action.setEnabled(False)
        self.play_action.triggered.connect(self.play)

        self.pause_action = QtGui.QAction(icontheme.lookup('pause'), _("Pause"), self)
        pause_tip = _("Pause or resume current playback")
        self.pause_action.setToolTip(pause_tip)
        self.pause_action.setStatusTip(pause_tip)
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(False)
        self.pause_action.setEnabled(False)
        self.pause_action.toggled.connect(self.pause)

        self._add_toolbar_action(self.play_action)
        self._add_toolbar_action(self.pause_action)

        self.progress_widget = PlaybackProgressSlider(self.player, parent=self)
        self.addWidget(self.progress_widget)

        config = get_config()
        volume = config.persist['mediaplayer_volume']
        self.player.set_volume(volume)
        self.volume_button = VolumeControlButton(volume, parent=self)
        self.volume_button.volume_changed.connect(self.player.set_volume)
        self.volume_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.volume_button)

        playback_rate = config.persist['mediaplayer_playback_rate']
        self.player.set_playback_rate(playback_rate)
        self.playback_rate_button = PlaybackRateButton(playback_rate, parent=self)
        self.playback_rate_button.playback_rate_changed.connect(self.player.set_playback_rate)
        self.playback_rate_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.playback_rate_button)

    def playback_state_changed(self, state):
        self.pause_action.setEnabled(self.player.is_playing or self.player.is_paused)

    def _add_toolbar_action(self, action):
        self.addAction(action)
        widget = self.widgetForAction(action)
        widget.setFocusPolicy(QtCore.Qt.FocusPolicy.TabFocus)
        widget.setAttribute(QtCore.Qt.WidgetAttribute.WA_MacShowFocusRect)

    def pause(self, checked):
        if self.player.is_playing or self.player.is_paused:
            self.player.pause(checked)

    def play(self):
        self.player.play()
        self.pause_action.setChecked(False)

    def setToolButtonStyle(self, style):
        super().setToolButtonStyle(style)
        self.playback_rate_button.setToolButtonStyle(style)
        self.volume_button.setToolButtonStyle(style)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_popover_position()

    def _update_popover_position(self):
        popover_position = self._get_popover_position()
        self.playback_rate_button.popover_position = popover_position
        self.volume_button.popover_position = popover_position

    def _get_popover_position(self):
        if self.isFloating():
            return 'bottom'
        pos = self.mapToParent(QtCore.QPoint(0, 0))
        half_main_window_height = self.parent().height() / 2
        if pos.y() <= half_main_window_height:
            return 'bottom'
        else:
            return 'top'


class PlaybackProgressSlider(QtWidgets.QWidget):
    def __init__(self, player, parent=None):
        super().__init__(parent=parent)
        self.player = player
        self._position_update = False

        tool_font = QtWidgets.QApplication.font('QToolButton')

        self.progress_slider = ClickableSlider(parent=self)
        self.progress_slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setMinimumWidth(30)
        self.progress_slider.setSingleStep(1000)
        self.progress_slider.setPageStep(3000)
        self.progress_slider.valueChanged.connect(self.on_value_changed)
        self.media_name_label = ElidedLabel(self)
        self.media_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.media_name_label.setFont(tool_font)

        slider_container = QtWidgets.QWidget(parent=self)
        hbox = QtWidgets.QHBoxLayout(slider_container)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.position_label = QtWidgets.QLabel("0:00", self)
        self.duration_label = QtWidgets.QLabel(format_time(0), self)
        min_duration_width = get_text_width(self.position_label.font(), "8:88")
        self.position_label.setMinimumWidth(min_duration_width)
        self.duration_label.setMinimumWidth(min_duration_width)
        self.position_label.setFont(tool_font)
        self.duration_label.setFont(tool_font)
        hbox.addWidget(self.position_label)
        hbox.addWidget(self.progress_slider)
        hbox.addWidget(self.duration_label)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setSpacing(0)
        vbox.addWidget(slider_container)
        vbox.addWidget(self.media_name_label)

        self.player._player.durationChanged.connect(self.on_duration_changed)
        self.player._player.positionChanged.connect(self.on_position_changed)
        self.player._player.sourceChanged.connect(self.on_media_changed)

    def on_duration_changed(self, duration):
        self.progress_slider.setMaximum(duration)
        self.duration_label.setText(format_time(duration))

    def on_position_changed(self, position):
        self._position_update = True
        self.progress_slider.setValue(position)
        self._position_update = False
        self.position_label.setText(format_time(position, display_zero=True))

    def on_media_changed(self, media):
        if media.isEmpty():
            self.progress_slider.setEnabled(False)
        else:
            url = media.toString()
            self.media_name_label.setText(os.path.basename(url))
            self.progress_slider.setEnabled(True)

    def on_value_changed(self, value):
        if not self._position_update:  # Avoid circular events
            self.player.set_position(value)


class PlaybackRateButton(QtWidgets.QToolButton):
    playback_rate_changed = QtCore.Signal(float)

    multiplier = 10.0

    def __init__(self, playback_rate, parent=None):
        super().__init__(parent=parent)
        self.popover_position = 'bottom'
        self.rate_fmt = N_("%1.1f ×")
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_ButtonMargin)
        min_width = get_text_width(self.font(), _(self.rate_fmt) % 8.8)
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.set_playback_rate(playback_rate)
        self.clicked.connect(self.show_popover)
        tooltip = _("Change playback speed")
        self.setToolTip(tooltip)
        self.setStatusTip(tooltip)

    def show_popover(self):
        slider_value = self.playback_rate * self.multiplier
        popover = SliderPopover(
            self, self.popover_position, _("Playback speed"), slider_value)
        # In 0.1 steps from 0.5 to 1.5
        popover.slider.setMinimum(5)
        popover.slider.setMaximum(15)
        popover.slider.setSingleStep(1)
        popover.slider.setPageStep(1)
        popover.slider.setTickInterval(1)
        popover.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        playback_rate = value / self.multiplier
        self.set_playback_rate(playback_rate)
        self.playback_rate_changed.emit(self.playback_rate)

    def set_playback_rate(self, playback_rate):
        self.playback_rate = playback_rate
        label = locale.format_string(_(self.rate_fmt), playback_rate)
        self.setText(label)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        # Incrementing repeatedly in 0.1 steps would cause floating point
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


class VolumeControlButton(QtWidgets.QToolButton):
    volume_changed = QtCore.Signal(int)

    def __init__(self, volume, parent=None):
        super().__init__(parent=parent)
        self.popover_position = 'bottom'
        self.step = 3
        self.volume_fmt = N_("%d%%")
        self.set_volume(volume)
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_ButtonMargin)
        min_width = get_text_width(self.font(), _(self.volume_fmt) % 888)
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.clicked.connect(self.show_popover)
        tooltip = _("Change audio volume")
        self.setToolTip(tooltip)
        self.setStatusTip(tooltip)

    def show_popover(self):
        popover = SliderPopover(
            self, self.popover_position, _("Audio volume"), self.volume)
        popover.slider.setMinimum(0)
        popover.slider.setMaximum(100)
        popover.slider.setPageStep(self.step)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        self.set_volume(value)
        self.volume_changed.emit(self.volume)

    def set_volume(self, volume):
        self.volume = volume
        label = _(self.volume_fmt) % volume
        self.setText(label)
        self.update_icon()

    def update_icon(self):
        if self.volume == 0:
            icon = 'speaker-0'
        elif self.volume <= 33:
            icon = 'speaker-33'
        elif self.volume <= 66:
            icon = 'speaker-66'
        else:
            icon = 'speaker-100'
        icon = icontheme.lookup(icon)
        self.setIcon(icon)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        volume = self.volume
        if delta > 0:
            volume += self.step
        elif delta < 0:
            volume -= self.step
        volume = min(max(volume, 0), 100)
        if volume != self.volume:
            self.set_volume(volume)
            self.volume_changed.emit(volume)

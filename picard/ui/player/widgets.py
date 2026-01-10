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

import locale

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard.file import File
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.util import (
    IgnoreUpdatesContext,
    format_time,
    icontheme,
)

from .player import (
    MAX_PLAYBACK_RATE,
    MIN_PLAYBACK_RATE,
    Player,
)

from picard.ui.widgets import (
    ClickableSlider,
    ElidedLabel,
    SliderPopover,
)


def get_text_width(font, text):
    metrics = QtGui.QFontMetrics(font)
    size = metrics.size(QtCore.Qt.TextFlag.TextSingleLine, text)
    return size.width()


class PlayerToolbar(QtWidgets.QToolBar):
    def __init__(self, player: Player, parent=None):
        super().__init__(_("Player"), parent=parent)
        self.setObjectName('player_toolbar')
        self.setAllowedAreas(
            QtCore.Qt.ToolBarArea.TopToolBarArea
            | QtCore.Qt.ToolBarArea.BottomToolBarArea
            | QtCore.Qt.ToolBarArea.NoToolBarArea
        )

        self.player = player
        self.player.playback_state_changed.connect(self.playback_state_changed)

        self.play_action = QtGui.QAction(icontheme.lookup('play'), _("Play"), self)
        play_tip = _("Play selected files")
        self.play_action.setToolTip(play_tip)
        self.play_action.setStatusTip(play_tip)
        self.play_action.setEnabled(False)
        self.play_action.triggered.connect(self.play)
        self.player.playback_available.connect(self.play_action.setEnabled)

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

        self.volume_button = VolumeControlButton(self.player.volume, parent=self)
        self.volume_button.volume_changed.connect(self.set_volume)
        self.volume_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.volume_button)
        self.player.volume_changed.connect(self.volume_button.set_volume)

        self.playback_rate_button = PlaybackRateButton(self.player.playback_rate, parent=self)
        self.playback_rate_button.playback_rate_changed.connect(self.set_playback_rate)
        self.playback_rate_button.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(self.playback_rate_button)
        self.player.playback_rate_changed.connect(self.playback_rate_button.set_playback_rate)

    def set_volume(self, volume: float):
        self.player.volume = volume

    def set_playback_rate(self, playback_rate: float):
        self.player.playback_rate = playback_rate

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
    def __init__(self, player: Player, parent=None):
        super().__init__(parent=parent)
        self.player = player
        self._position_is_updating = IgnoreUpdatesContext()

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

        self.player.duration_changed.connect(self.on_duration_changed)
        self.player.position_changed.connect(self.on_position_changed)
        self.player.playback_state_changed.connect(self.on_playback_state_changed)
        self.player.media_changed.connect(self.on_media_changed)

    def on_playback_state_changed(self, state):
        if self.player.is_stopped:
            self.media_name_label.setText('')
            self.progress_slider.setEnabled(False)
            self.on_duration_changed(0)

    def on_duration_changed(self, duration):
        self.progress_slider.setMaximum(duration)
        self.duration_label.setText(format_time(duration))

    def on_position_changed(self, position):
        with self._position_is_updating:
            self.progress_slider.setValue(position)
        self.position_label.setText(format_time(position, display_zero=True))

    def on_media_changed(self, media: File):
        if not (media and media.filename):
            self.media_name_label.setText('')
            self.progress_slider.setEnabled(False)
        else:
            metadata = media.metadata
            artist = metadata.get('artist', _('Unknown Artist'))
            title = media.column('title')
            self.media_name_label.setText(f"{artist} - {title}")
            self.progress_slider.setEnabled(True)
            self.on_duration_changed(media.metadata.length)

    def on_value_changed(self, value):
        if not self._position_is_updating:  # Avoid circular events
            self.player.position = value


class PlaybackRateButton(QtWidgets.QToolButton):
    playback_rate_changed = QtCore.pyqtSignal(float)

    multiplier = 10.0

    def __init__(self, playback_rate, parent=None):
        super().__init__(parent=parent)
        self._is_updating = IgnoreUpdatesContext()
        self.popover_position = 'bottom'
        self._rate_fmt = N_("%1.1f ×")
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_ButtonMargin)
        min_width = get_text_width(self.font(), _(self._rate_fmt) % 8.8)
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.set_playback_rate(playback_rate)
        self.clicked.connect(self.show_popover)
        tooltip = _("Change playback speed")
        self.setToolTip(tooltip)
        self.setStatusTip(tooltip)

    def show_popover(self):
        slider_value = self._playback_rate * self.multiplier
        popover = SliderPopover(self, self.popover_position, _("Playback speed"), slider_value)
        # In 0.1 steps from 0.5 to 1.5
        popover.slider.setMinimum(int(MIN_PLAYBACK_RATE * self.multiplier))
        popover.slider.setMaximum(int(MAX_PLAYBACK_RATE * self.multiplier))
        popover.slider.setSingleStep(1)
        popover.slider.setPageStep(1)
        popover.slider.setTickInterval(1)
        popover.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        playback_rate = value / self.multiplier
        self.set_playback_rate(playback_rate)
        self.playback_rate_changed.emit(self._playback_rate)

    def set_playback_rate(self, playback_rate):
        self._playback_rate = playback_rate
        label = locale.format_string(_(self._rate_fmt), playback_rate)
        self.setText(label)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        # Incrementing repeatedly in 0.1 steps would cause floating point
        # rounding issues. Do the calculation in whole numbers to prevent this.
        new_rate = int(self._playback_rate * 10)
        if delta > 0:
            new_rate += 1
        elif delta < 0:
            new_rate -= 1
        new_rate = min(max(new_rate / 10.0, MIN_PLAYBACK_RATE), MAX_PLAYBACK_RATE)
        if new_rate != self._playback_rate:
            self.set_playback_rate(new_rate)
            self.playback_rate_changed.emit(new_rate)


class VolumeControlButton(QtWidgets.QToolButton):
    volume_changed = QtCore.pyqtSignal(float)

    def __init__(self, volume: float, parent=None):
        super().__init__(parent=parent)
        self.popover_position = 'bottom'
        self._step = 3
        self._volume_fmt = N_("%d%%")
        self.set_volume(volume)
        button_margin = self.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_ButtonMargin)
        min_width = get_text_width(self.font(), _(self._volume_fmt) % 888)
        self.setMinimumWidth(min_width + (2 * button_margin) + 2)
        self.clicked.connect(self.show_popover)
        tooltip = _("Change audio volume")
        self.setToolTip(tooltip)
        self.setStatusTip(tooltip)

    def show_popover(self):
        popover = SliderPopover(self, self.popover_position, _("Audio volume"), self._volume)
        popover.slider.setMinimum(0)
        popover.slider.setMaximum(100)
        popover.slider.setPageStep(self._step)
        popover.value_changed.connect(self.on_slider_value_changed)
        popover.show()

    def on_slider_value_changed(self, value):
        self._set_volume(value)
        self.volume_changed.emit(self._volume / 100.0)

    def set_volume(self, volume: float):
        self._set_volume(int(volume * 100))

    def _set_volume(self, volume: int):
        self._volume = volume
        label = _(self._volume_fmt) % self._volume
        self.setText(label)
        self.update_icon()

    def update_icon(self):
        if self._volume == 0:
            icon = 'speaker-0'
        elif self._volume <= 33:
            icon = 'speaker-33'
        elif self._volume <= 66:
            icon = 'speaker-66'
        else:
            icon = 'speaker-100'
        icon = icontheme.lookup(icon)
        self.setIcon(icon)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        volume = self._volume
        if delta > 0:
            volume += 1
        elif delta < 0:
            volume -= 1
        volume = min(max(volume, 0), 100)
        if volume != self._volume:
            self._set_volume(volume)
            self.volume_changed.emit(self._volume / 100.0)

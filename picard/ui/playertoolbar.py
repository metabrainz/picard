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

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from picard import (
    config,
    log,
)


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
        if qt_multimedia_available:
            player = QtMultimedia.QMediaPlayer(parent)
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

    def create_toolbar(self):
        self._toolbar = PlayerToolbar(self.parent(), self._player)
        return self._toolbar

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
        self._selected_objects = []

        self.play_action = QtWidgets.QAction(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay), _("Play"), self)
        self.play_action.setStatusTip(_("Play selected files in an internal player"))
        self.play_action.setEnabled(False)
        self.play_action.triggered.connect(self.play)

        self.pause_action = QtWidgets.QAction(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause), _("Pause"), self)
        self.pause_action.setToolTip(_("Pause/resume"))
        self.pause_action.setStatusTip(_("Pause or resume playing with an internal player"))
        self.pause_action.setCheckable(True)
        self.pause_action.setChecked(False)
        self.pause_action.setEnabled(False)
        self.pause_action.triggered.connect(self.pause)
        self.player.stateChanged.connect(self.pause_action.setEnabled)

        self._add_toolbar_action(self.play_action)
        self._add_toolbar_action(self.pause_action)
        self.volume_slider = QtWidgets.QSlider(self)
        self.volume_slider.setOrientation(QtCore.Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setValue(
            get_logarithmic_volume(int(config.persist["mediaplayer_volume"])))
        self.volume_label = QtWidgets.QLabel(_("Volume"), self)
        self.volume_widget = QtWidgets.QWidget(self)
        vbox = QtWidgets.QVBoxLayout(self.volume_widget)
        vbox.addWidget(self.volume_slider)
        vbox.addWidget(self.volume_label)
        self.addWidget(self.volume_widget)

    def _add_toolbar_action(self, action):
        self.addAction(action)
        widget = self.widgetForAction(action)
        widget.setFocusPolicy(QtCore.Qt.TabFocus)
        widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect)

    def set_objects(self, objects):
        self._selected_objects = objects

    def play(self):
        """Play selected tracks with an internal player"""
        self.player.stop()
        playlist = QtMultimedia.QMediaPlaylist(self)
        playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Sequential)
        playlist.addMedia([QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(file.filename))
                          for file in self.tagger.get_files_from_objects(self._selected_objects)])
        self.player.setPlaylist(playlist)
        self.player.play()
        self.pause_action.setChecked(False)

    def pause(self, is_paused):
        """Toggle pause of an internal player"""
        if is_paused:
            self.player.pause()
        else:
            self.player.play()

    def set_volume(self, slider_value):
        """Convert to linear scale and set"""
        self.player.setVolume(get_linear_volume(slider_value))

    def setToolButtonStyle(self, style):
        super().setToolButtonStyle(style)
        if style == QtCore.Qt.ToolButtonTextUnderIcon:
            self.volume_label.show()
        else:
            self.volume_label.hide()

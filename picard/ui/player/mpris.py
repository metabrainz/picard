# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Philipp Wolfer
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

from enum import Enum

from PyQt6.QtCore import (
    QCoreApplication,
    QMetaType,
    QObject,
    QUrl,
    pyqtClassInfo,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtDBus import (
    QDBusAbstractAdaptor,
    QDBusArgument,
    QDBusConnection,
    QDBusMessage,
    QDBusObjectPath,
)

from picard import (
    PICARD_APP_ID,
    PICARD_DISPLAY_NAME,
)
from picard.file import File

from .player import (
    MAX_PLAYBACK_RATE,
    MIN_PLAYBACK_RATE,
    Player,
)


MPRIS2_DBUS_BUS_NAME = 'org.mpris.MediaPlayer2.picard'
MPRIS2_DBUS_OBJECT_PATH = '/org/mpris/MediaPlayer2'
MPRIS2_DBUS_INTERFACE = 'org.mpris.MediaPlayer2'
MPRIS2_DBUS_INTERFACE_PLAYER = 'org.mpris.MediaPlayer2.Player'


class MPRIS2PlaybackStatus(Enum):
    Playing = 'Playing'
    Paused = 'Paused'
    Stopped = 'Stopped'


class MPRIS2LoopStatus(Enum):
    None_ = 'None'
    Track = 'Track'
    Playlist = 'Playlist'


class MPRIS2NowPlayingService:
    def __init__(self, player: Player):
        self._player = player
        self._mpris2_service = None

    def enable(self):
        if self._mpris2_service:
            # already enabled
            return

        dbus = QDBusConnection.sessionBus()
        self._mpris2_service = MPRIS2Service(dbus, self._player)
        dbus.registerService(MPRIS2_DBUS_BUS_NAME)
        dbus.registerObject(MPRIS2_DBUS_OBJECT_PATH, self._mpris2_service)

    def disable(self):
        if not self._mpris2_service:
            # not enabled, can't disable
            return

        dbus = QDBusConnection.sessionBus()
        dbus.unregisterObject(MPRIS2_DBUS_OBJECT_PATH, QDBusConnection.UnregisterMode.UnregisterTree)
        dbus.unregisterService(MPRIS2_DBUS_BUS_NAME)
        self._mpris2_service = None


class MPRIS2Service(QObject):
    """Implementation of the MPRIS 2 D-Bus Interface.

    See https://specifications.freedesktop.org/mpris/latest/index.html
    """

    def __init__(self, bus: QDBusConnection, player: Player):
        QObject.__init__(self)
        self._bus = bus
        self._player = player
        self._metadata = {}

        # Set up adaptors for DBus interfaces
        self._adaptor = MediaPlayer2Adaptor(self)
        self._adaptor_player = MediaPlayer2PlayerAdaptor(self, player)

        # Connect signals
        player.playback_available.connect(self.update_playback_available)
        player.media_changed.connect(self.update_metadata)
        player.playback_state_changed.connect(self.update_playback_state)
        player.volume_changed.connect(self.update_volume)
        player.playback_rate_changed.connect(self.update_playback_rate)

        # Set initial values
        self.update_metadata(player.current_file)
        self.update_playback_state(player.playback_state)

    def update_playback_available(self, can_play: bool):
        # This effects the availability of several properties
        self._emit_properties_changed(
            {
                'CanPlay': can_play,
                'CanPause': can_play,
                'CanSeek': can_play,
                'CanGoNext': can_play,
                'CanGoPrevious': can_play,
                'PlaybackStatus': self._player.playback_state.value,
            }
        )

    def update_playback_state(self, state: Player.PlaybackState):
        if state == Player.PlaybackState.PLAYING:
            self._playback_status = MPRIS2PlaybackStatus.Playing
        elif state == Player.PlaybackState.PAUSED:
            self._playback_status = MPRIS2PlaybackStatus.Paused
        else:
            self._playback_status = MPRIS2PlaybackStatus.Stopped

        self._emit_properties_changed({'PlaybackStatus': self._playback_status.value})

    def update_metadata(self, file: File | None):
        if not file:
            self._metadata = {}
            self._emit_properties_changed({'Metadata': self._metadata})
            return

        m = file.metadata
        front_image = m.images.get_front_image()
        art_url = ''
        if front_image and front_image.datahash:
            art_url = QUrl.fromLocalFile(front_image.datahash.filename).toString()
        # See https://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata/
        self._metadata = {
            'mpris:trackid': _get_mpris_id_for_file(file),
            'mpris:length': m.length * 1000,  # microseconds
            'mpris:artUrl': art_url,
            'xesam:album': m['album'],
            'xesam:albumArtist': _build_dbus_string_array(m.getall('albumartist')),
            'xesam:artist': _build_dbus_string_array(m.getall('artist')),
            'xesam:composer': _build_dbus_string_array(m.getall('composer')),
            'xesam:discNumber': file.discnumber,
            'xesam:genre': _build_dbus_string_array(m.getall('genre')),
            'xesam:title': m['title'],
            'xesam:trackNumber': file.tracknumber,
            'xesam:url': QUrl.fromLocalFile(file.filename).toString(),
            # It is not specified in the standard, but some players and MPRIS tools
            # support MBIDs. The format was defined by Rhythmbox.
            'xesam:musicBrainzTrackID': _build_dbus_string_array(m.getall('musicbrainz_recordingid')),
            'xesam:musicBrainzAlbumID': _build_dbus_string_array(m.getall('musicbrainz_albumid')),
            'xesam:musicBrainzArtistID': _build_dbus_string_array(m.getall('musicbrainz_artistid')),
            'xesam:musicBrainzAlbumArtistID': _build_dbus_string_array(m.getall('musicbrainz_albumartistid')),
        }
        self._emit_properties_changed({'Metadata': self._metadata})

    def update_volume(self, volume):
        self._emit_properties_changed({'Volume': volume})

    def update_playback_rate(self, rate):
        self._emit_properties_changed({'Rate': rate})

    def _emit_properties_changed(self, changed_props):
        object_path = MPRIS2_DBUS_OBJECT_PATH
        interface_name = MPRIS2_DBUS_INTERFACE_PLAYER
        msg = QDBusMessage.createSignal(object_path, 'org.freedesktop.DBus.Properties', 'PropertiesChanged')

        # The last argument (array of invalidated properties) must be explicitly an
        # array of strings (DBus type "as").
        invalidated_props = _build_dbus_string_array([])

        msg.setArguments(
            [
                interface_name,
                changed_props,  # dict of changed properties
                invalidated_props,  # array of invalidated properties
            ]
        )
        self._bus.send(msg)


@pyqtClassInfo('D-Bus Interface', MPRIS2_DBUS_INTERFACE)
class MediaPlayer2Adaptor(QDBusAbstractAdaptor):
    """See https://specifications.freedesktop.org/mpris/latest/Media_Player.html"""

    @pyqtProperty(bool)
    def CanQuit(self):
        return False

    @pyqtProperty(bool)
    def Fullscreen(self):
        return False

    @Fullscreen.setter
    def Fullscreen(self, value):
        raise NotImplementedError()

    @pyqtProperty(bool)
    def CanSetFullscreen(self):
        return False

    @pyqtProperty(bool)
    def CanRaise(self):
        return True

    @pyqtProperty(bool)
    def HasTrackList(self):
        return False

    @pyqtProperty(str)
    def Identity(self):
        return PICARD_DISPLAY_NAME

    @pyqtProperty(str)
    def DesktopEntry(self):
        return PICARD_APP_ID

    @pyqtProperty('QStringList')
    def SupportedUriSchemes(self):
        # Opening files for playback via MPRIS is not supported
        return []

    @pyqtProperty('QStringList')
    def SupportedMimeTypes(self):
        return []

    @pyqtSlot()
    def Raise(self):
        tagger = QCoreApplication.instance()
        tagger.bring_tagger_front()

    @pyqtSlot()
    def Quit(self):
        pass


@pyqtClassInfo('D-Bus Interface', MPRIS2_DBUS_INTERFACE_PLAYER)
class MediaPlayer2PlayerAdaptor(QDBusAbstractAdaptor):
    """See https://specifications.freedesktop.org/mpris/latest/Player_Interface.html"""

    # TODO: Actually trigger
    Seeked = pyqtSignal('qlonglong')

    def __init__(self, parent: MPRIS2Service, player: Player):
        super().__init__(parent)
        self._parent = parent
        self._player = player
        self._player.seeked.connect(self.Seeked.emit)

    @pyqtProperty(str)
    def PlaybackStatus(self):
        state = self._player.playback_state
        if state == Player.PlaybackState.PLAYING:
            return MPRIS2PlaybackStatus.Playing.value
        elif state == Player.PlaybackState.PAUSED:
            return MPRIS2PlaybackStatus.Paused.value
        else:
            return MPRIS2PlaybackStatus.Stopped.value

    @pyqtProperty(str)
    def LoopStatus(self):
        return MPRIS2LoopStatus.None_.value

    @LoopStatus.setter
    def LoopStatus(self, value):
        # Not supported
        pass

    @pyqtProperty(float)
    def Rate(self):
        return self._player.playback_rate

    @Rate.setter
    def Rate(self, value):
        # The player automatically limits the value to the allowed minimum / maximum
        self._player.playback_rate = value

    @pyqtProperty(bool)
    def Shuffle(self):
        return False

    @Shuffle.setter
    def Shuffle(self, value):
        # Not supported
        pass

    @pyqtProperty('QVariantMap')
    def Metadata(self):
        return self._parent._metadata

    @pyqtProperty(float)
    def Volume(self):
        return self._player.volume

    @Volume.setter
    def Volume(self, value):
        # Ensure the value is inside the range
        value = min(max(value, 0.0), 1.0)
        self._player.volume = value

    @pyqtProperty('qlonglong')
    def Position(self):
        return self._player.position * 1000  # convert milliseconds to microseconds

    @pyqtProperty(float)
    def MinimumRate(self):
        return MIN_PLAYBACK_RATE

    @pyqtProperty(float)
    def MaximumRate(self):
        return MAX_PLAYBACK_RATE

    @pyqtProperty(bool)
    def CanGoNext(self):
        return self._player.can_play

    @pyqtProperty(bool)
    def CanGoPrevious(self):
        return self._player.can_play

    @pyqtProperty(bool)
    def CanPlay(self):
        return self._player.can_play

    @pyqtProperty(bool)
    def CanPause(self):
        return self._player.can_play

    @pyqtProperty(bool)
    def CanSeek(self):
        return self._player.can_play

    @pyqtProperty(bool)
    def CanControl(self):
        return True

    @pyqtSlot()
    def Next(self):
        self._player.play_next()

    @pyqtSlot()
    def Previous(self):
        # Full previous track is not supported, but we can jump to
        # the start of the current track
        self._player.position = 0

    @pyqtSlot()
    def Pause(self):
        self._player.pause(True)

    @pyqtSlot()
    def PlayPause(self):
        self._player.pause(self._player.is_playing)

    @pyqtSlot()
    def Stop(self):
        self._player.stop()

    @pyqtSlot()
    def Play(self):
        self._player.play()

    @pyqtSlot('qlonglong')
    def Seek(self, offset: int):
        offset = int(offset / 1000.0)  # convert microseconds to milliseconds
        new_position = max(0, self._player.position + offset)
        if new_position <= self._player.duration:
            self._player.position = new_position
        else:
            self._player.play_next()

    @pyqtSlot(QDBusObjectPath, 'qlonglong')
    def SetPosition(self, track_id: QDBusObjectPath, position: int):
        current_track_id = _get_mpris_id_for_file(self._player.current_file)
        if track_id != current_track_id:
            return  # consider this request stale

        position = int(position / 1000.0)  # convert microseconds to milliseconds
        if position >= 0 and position <= self._player.duration:
            self._player.position = position

    @pyqtSlot(str)
    def OpenUri(self, uri: str):
        # Not supported
        pass


def _get_mpris_id_for_file(file: File | None) -> QDBusObjectPath | None:
    """Returns an MPRIS ID path for the given file."""
    if not file:
        return None
    # The MPRIS2 specification requires a valid DBus object ID
    return QDBusObjectPath(f'/org/musicbrainz/Picard/File/{hash(file)}')


def _build_dbus_string_array(list):
    """Converts a list into a DBus string array (type "as")."""
    string_array = QDBusArgument()
    string_array.beginArray(QMetaType(QMetaType.Type.QString.value))
    for s in list:
        string_array.add(str(s))
    string_array.endArray()
    return string_array

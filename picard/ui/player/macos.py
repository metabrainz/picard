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

from picard import log
from picard.coverart.image import CoverArtImage
from picard.file import File

from AppKit import (  # type: ignore[unresolved-import]
    NSCompositingOperationSourceOver,
    NSImage,
    NSMakeRect,
)
from MediaPlayer import (  # type: ignore[unresolved-import]
    MPMediaItemArtwork,
    MPMediaItemPropertyAlbumTitle,
    MPMediaItemPropertyAlbumTrackNumber,
    MPMediaItemPropertyArtist,
    MPMediaItemPropertyArtwork,
    MPMediaItemPropertyComposer,
    MPMediaItemPropertyDiscNumber,
    MPMediaItemPropertyGenre,
    MPMediaItemPropertyPlaybackDuration,
    MPMediaItemPropertyTitle,
    MPMusicPlaybackStatePaused,
    MPMusicPlaybackStatePlaying,
    MPMusicPlaybackStateStopped,
    MPNowPlayingInfoCenter,
    MPNowPlayingInfoPropertyElapsedPlaybackTime,
    MPNowPlayingInfoPropertyPlaybackRate,
    MPRemoteCommandCenter,
    MPRemoteCommandHandlerStatusSuccess,
)

from picard.ui.player.player import Player


class MacNowPlayingService:
    def __init__(self, player: Player):
        self._player = player
        self._enabled = False

        # The Remote Command center is used by the OS to send media player commands
        self.cmd_center = MPRemoteCommandCenter.sharedCommandCenter()

        # The Now Playing Info Center is used to notify macOS of what is playing
        self.info_center = MPNowPlayingInfoCenter.defaultCenter()

    def enable(self):
        if self._enabled:
            return

        self._enabled = True

        # Register commands
        cc = self.cmd_center
        self._cmd_play = cc.playCommand().addTargetWithHandler_(self.play)
        self._cmd_pause = cc.pauseCommand().addTargetWithHandler_(self.pause)
        self._cmd_toggle_pause = cc.togglePlayPauseCommand().addTargetWithHandler_(self.toggle_pause)
        self._cmd_next_track = cc.nextTrackCommand().addTargetWithHandler_(self.next_track)
        self._cmd_previous_track = cc.previousTrackCommand().addTargetWithHandler_(self.previous_track)
        self._cmd_skip_backward = cc.skipBackwardCommand().addTargetWithHandler_(self.skip_backward)
        self._cmd_skip_forward = cc.skipForwardCommand().addTargetWithHandler_(self.skip_forward)
        self._cmd_change_position = cc.changePlaybackPositionCommand().addTargetWithHandler_(self.change_position)
        self._cmd_change_playback_rate = cc.changePlaybackRateCommand().addTargetWithHandler_(self.change_playback_rate)

        # Connect media player events
        player = self._player
        player.playback_state_changed.connect(self.update_playback_state)
        player.media_changed.connect(self.update_now_playing_info)
        player.playback_rate_changed.connect(self.update_playback_rate)
        player.seeked.connect(self.update_playback_position)

        # Set current state
        if player.current_file:
            self.update_now_playing_info(player.current_file)
            self.update_playback_state(player.playback_state)

    def disable(self):
        if not self._enabled:
            return

        self._enabled = False

        # Disconnect media player events
        player = self._player
        player.playback_state_changed.disconnect(self.update_playback_state)
        player.media_changed.disconnect(self.update_now_playing_info)
        player.playback_rate_changed.disconnect(self.update_playback_rate)
        player.seeked.disconnect(self.update_playback_position)

        # Unregister commands
        cc = self.cmd_center
        cc.playCommand().removeTarget_(self._cmd_play)
        cc.pauseCommand().removeTarget_(self._cmd_pause)
        cc.togglePlayPauseCommand().removeTarget_(self._cmd_toggle_pause)
        cc.nextTrackCommand().removeTarget_(self._cmd_next_track)
        cc.previousTrackCommand().removeTarget_(self._cmd_previous_track)
        cc.skipForwardCommand().removeTarget_(self._cmd_skip_forward)
        cc.skipBackwardCommand().removeTarget_(self._cmd_skip_backward)
        cc.changePlaybackPositionCommand().removeTarget_(self._cmd_change_position)
        cc.changePlaybackRateCommand().removeTarget_(self._cmd_change_playback_rate)

        # Clear playback info
        self._clear_now_playing()

    def play(self, event):
        self._player.play()
        return MPRemoteCommandHandlerStatusSuccess

    def pause(self, event):
        self._player.pause(True)
        return MPRemoteCommandHandlerStatusSuccess

    def toggle_pause(self, event):
        self._player.pause(not self._player.is_paused)
        return MPRemoteCommandHandlerStatusSuccess

    def next_track(self, event):
        self._player.play_next()
        return MPRemoteCommandHandlerStatusSuccess

    def previous_track(self, event):
        # Full previous track is not supported, but we can jump to
        # the start of the current track
        self._player.position = 0
        return MPRemoteCommandHandlerStatusSuccess

    def change_playback_rate(self, event):
        self._player.playback_rate = event.playbackRate()
        return MPRemoteCommandHandlerStatusSuccess

    def skip_backward(self, event):
        interval = event.interval()  # seconds
        # the given interval is always positive, use negative
        # interval for skipping backwards
        self._skip_by_interval(-interval)
        return MPRemoteCommandHandlerStatusSuccess

    def skip_forward(self, event):
        interval = event.interval()  # seconds
        self._skip_by_interval(interval)
        return MPRemoteCommandHandlerStatusSuccess

    def change_position(self, event):
        position = int(event.positionTime() * 1000)  # convert seconds to milliseconds
        self._set_position(position)
        return MPRemoteCommandHandlerStatusSuccess

    def _skip_by_interval(self, interval_seconds: float):
        interval_ms = int(interval_seconds * 1000)
        new_position = self._player.position + interval_ms
        self._set_position(new_position)

    def _set_position(self, position):
        # clamp to track range, with a one second offset to the end to allow the
        # track to end naturally.
        position = min(max(0, position), self._player.duration - 1000)
        self._player.position = position

    def update_playback_state(self, state: Player.PlaybackState):
        if state == Player.PlaybackState.PLAYING:
            now_playing_state = MPMusicPlaybackStatePlaying
        elif state == Player.PlaybackState.PAUSED:
            now_playing_state = MPMusicPlaybackStatePaused
        else:
            now_playing_state = MPMusicPlaybackStateStopped

        self.info_center.setPlaybackState_(now_playing_state)

        info = {}
        self._set_info_playback_times(info)
        self._update_playback_info(info)

    def update_playback_position(self, position: int):
        info = {}
        self._set_info_playback_times(info)
        self._update_playback_info(info)

    def update_playback_rate(self, rate: float):
        info = {}
        self._set_info_playback_times(info)
        self._update_playback_info(info)

    def _update_playback_info(self, values: dict):
        info = self.info_center.nowPlayingInfo()
        if info is not None:
            info = dict(info)
            info.update(values)
            self.info_center.setNowPlayingInfo_(info)

    def update_now_playing_info(self, file: File | None):
        if not file:
            self._clear_now_playing()
            return

        m = file.metadata
        info = dict()

        # Set track information
        info[MPMediaItemPropertyTitle] = m['title']
        info[MPMediaItemPropertyArtist] = m['artist']
        info[MPMediaItemPropertyAlbumTitle] = m['album']
        info[MPMediaItemPropertyAlbumTrackNumber] = file.tracknumber
        info[MPMediaItemPropertyDiscNumber] = file.discnumber
        info[MPMediaItemPropertyComposer] = m['composer']
        info[MPMediaItemPropertyGenre] = m['genre']
        self._set_info_playback_times(info)

        # Set the cover art if available
        front_image = m.images.get_front_image()
        if front_image:
            try:
                art = _create_media_item_artwork(front_image)
                if art:
                    info[MPMediaItemPropertyArtwork] = art
            except OSError:
                log.warning('macOS Now Playing: Could not read cover art data for %r', front_image)

        # Set the metadata information for the 'Now Playing' service
        self.info_center.setNowPlayingInfo_(info)

    def _set_info_playback_times(self, info: dict):
        player = self._player
        info[MPNowPlayingInfoPropertyPlaybackRate] = player.playback_rate
        info[MPMediaItemPropertyPlaybackDuration] = player.duration / 1000.0  # in seconds
        if player.playback_state != Player.PlaybackState.STOPPED:
            info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = player.position / 1000.0  # in seconds

    def _clear_now_playing(self):
        self.info_center.setPlaybackState_(MPMusicPlaybackStateStopped)
        self.info_center.setNowPlayingInfo_(
            {
                MPNowPlayingInfoPropertyElapsedPlaybackTime: 0.0,
                MPNowPlayingInfoPropertyPlaybackRate: 0.0,
            }
        )


def _create_media_item_artwork(image: CoverArtImage) -> MPMediaItemArtwork | None:
    """Create a MPMediaItemArtwork from a CoverArtImage.

    May return None if the image has no data.
    May raise OSError if reading the image data fails.
    """
    if not image.datahash:
        return None

    data = image.datahash.data()
    img = NSImage.alloc().initWithData_(data)

    def resize(size):
        new = NSImage.alloc().initWithSize_(size)
        new.lockFocus()
        img.drawInRect_fromRect_operation_fraction_(
            NSMakeRect(0, 0, size.width, size.height),
            NSMakeRect(0, 0, *img.size()),
            NSCompositingOperationSourceOver,
            1.0,
        )
        new.unlockFocus()
        return new

    return MPMediaItemArtwork.alloc().initWithBoundsSize_requestHandler_(img.size(), resize)

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

from dataclasses import dataclass
from functools import partial
import time
from typing import TYPE_CHECKING

from PyQt6.QtNetwork import QNetworkReply

from picard import log
from picard.config import get_config
from picard.file import File
from picard.metadata import Metadata
from picard.util import throttle
from picard.webservice import WebService
from picard.webservice.api_helpers.listenbrainz import (
    ListenBrainzAPIHelper,
    ListenPayload,
    ListenSubmission,
    ListenType,
    TrackMetadata,
)

from picard.ui.player.player import Player


if TYPE_CHECKING:
    from picard.tagger import Tagger


MIN_PLAYBACK_SECONDS = 240


@dataclass
class PreparedSubmission:
    """Holds metadata and submission state for a track to be submitted to ListenBrainz."""

    metadata: Metadata
    start_time: int
    elapsed_seconds: int = 0
    submitted: bool = False

    @property
    def can_submit(self) -> bool:
        if self.submitted or self.metadata.length < 1000:
            return False
        duration = self.metadata.length / 1000
        elapsed = self.elapsed_seconds
        return elapsed >= MIN_PLAYBACK_SECONDS or elapsed >= duration / 2


class ListenBrainzSubmissionService:
    """Integrates with a Player instance to submit listened tracks to ListenBrainz."""

    def __init__(self, player: Player, webservice: WebService, tagger: 'Tagger'):
        self._player = player
        self._tagger = tagger
        self._enabled = False
        self._current: PreparedSubmission | None = None
        self._lbapi = ListenBrainzAPIHelper(webservice)

    def enable(self):
        if self._enabled:
            return

        self._enabled = True

        self._player.media_changed.connect(self.on_media_changed)
        self._player.playback_state_changed.connect(self.on_playback_state_changed)
        self._player.position_changed.connect(self.on_position_changed)

    def disable(self):
        if not self._enabled:
            return

        self._player.media_changed.disconnect(self.on_media_changed)
        self._player.playback_state_changed.disconnect(self.on_playback_state_changed)
        self._player.position_changed.disconnect(self.on_position_changed)

        self._enabled = False

    def on_media_changed(self, media: File | None):
        if self._current and self._current.can_submit:
            self._submit_listen(self._current)

        if media:
            self._current = PreparedSubmission(metadata=media.metadata, start_time=int(time.time()))
        else:
            self._current = None

    def on_playback_state_changed(self, state: Player.PlaybackState):
        if not self._current:
            return

        if state == Player.PlaybackState.PLAYING:
            self._submit_now_playing(self._current)

    @throttle(1000)
    def on_position_changed(self, position: int):
        if self._current:
            self._current.elapsed_seconds += 1
            if self._current.can_submit:
                self._submit_listen(self._current)

    def _submit_now_playing(self, submission: PreparedSubmission):
        config = get_config()
        token = config.setting['listenbrainz_token']
        listen = self._create_listen_submission(ListenType.PLAYING_NOW, submission)
        self._lbapi.submit_listen(token, listen, self._on_submit_now_playing_response)

    def _on_submit_now_playing_response(
        self, data, reply: QNetworkReply, error: QNetworkReply.NetworkError | Exception | None
    ):
        if error:
            log.error('ListenBrainz now playing failed: data=%s, error=%s', data, error)
            self._tagger.window.set_statusbar_message('ListenBrainz now playing failed')
        else:
            log.debug('ListenBrainz now playing successful: data=%s', data)

    def _submit_listen(self, submission: PreparedSubmission):
        config = get_config()
        token = config.setting['listenbrainz_token']
        listen = self._create_listen_submission(ListenType.SINGLE, submission)
        self._lbapi.submit_listen(token, listen, partial(self._on_submit_listen_response, submission))

    def _on_submit_listen_response(
        self,
        submission: PreparedSubmission,
        data,
        reply: QNetworkReply,
        error: QNetworkReply.NetworkError | Exception | None,
    ):
        if error:
            log.error('ListenBrainz submission failed: data=%s, error=%s', data, error)
            self._tagger.window.set_statusbar_message('ListenBrainz submission failed')
        else:
            submission.submitted = True
            log.debug('ListenBrainz submission successful: data=%s', data)

    def _create_listen_submission(self, type: ListenType, submission: PreparedSubmission) -> ListenSubmission:
        payload = ListenPayload(track_metadata=TrackMetadata.from_metadata(submission.metadata))
        if type != ListenType.PLAYING_NOW:
            payload.listened_at = submission.start_time
        return ListenSubmission(
            listen_type=type,
            payload=[payload],
        )

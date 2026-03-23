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

from typing import TYPE_CHECKING

from PyQt6.QtNetwork import QNetworkReply

from picard import log
from picard.config import get_config
from picard.file import File
from picard.metadata import Metadata
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


class ListenBrainzSubmissionService:
    def __init__(self, player: Player, webservice: WebService, tagger: 'Tagger'):
        self._player = player
        self._tagger = tagger
        self._enabled = False
        self._current_metadata = None
        self._lbapi = ListenBrainzAPIHelper(webservice)

    def enable(self):
        if self._enabled:
            return

        self._enabled = True

        self._player.media_changed.connect(self._on_media_changed)
        self._player.playback_state_changed.connect(self._on_playback_state_changed)

    def disable(self):
        if not self._enabled:
            return

        self._enabled = False

    def _on_media_changed(self, media: File | None):
        log.info('Media changed: %s', media)
        if media:
            self._current_metadata = media.metadata
        else:
            self._current_metadata = None

    def _on_playback_state_changed(self, state: Player.PlaybackState):
        log.info('Playback state changed: %s', state)
        if not self._current_metadata:
            return

        if state == Player.PlaybackState.PLAYING:
            self._submit_now_playing(self._current_metadata)

    def _on_submit_listen_response(
        self, data, reply: QNetworkReply, error: QNetworkReply.NetworkError | Exception | None
    ):
        if error:
            log.error('ListenBrainz submission failed: data=%s, error=%s', data, error)
            self._tagger.window.set_statusbar_message('ListenBrainz submission failed')
        else:
            log.info('ListenBrainz submission successful: data=%s', data)

    def _submit_now_playing(self, metadata: Metadata):
        config = get_config()
        token = config.setting['listenbrainz_token']
        listen = self._create_listen_submission(ListenType.PLAYING_NOW, metadata)
        self._lbapi.submit_listen(token, listen, self._on_submit_listen_response)

    def _create_listen_submission(self, type: ListenType, metadata: Metadata) -> ListenSubmission:
        return ListenSubmission(
            listen_type=type,
            payload=[ListenPayload(track_metadata=TrackMetadata.from_metadata(metadata))],
        )

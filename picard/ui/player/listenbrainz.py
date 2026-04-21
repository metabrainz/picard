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

from dataclasses import (
    asdict,
    dataclass,
)
from functools import partial
import json
from pathlib import Path
import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
)

from picard import log
from picard.config import get_config
from picard.const.appdirs import cache_folder
from picard.file import File
from picard.metadata import Metadata
from picard.util import (
    ReadWriteLockContext,
    throttle,
)
from picard.webservice import (
    ReplyHandler,
    WebService,
)
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


# Minimum playback time in seconds required to submit a listen
MIN_PLAYBACK_SECONDS = 240

# Number of listens to submit in a batch (for queued listens)
MAX_LISTENS_PER_IMPORT = 100

# If listen submission fails, retry after this many seconds
SUBMISSION_INTERVAL_SECONDS = 120


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
        self._queue = ListenQueue(self._lbapi)
        self._queue.load()
        tagger.register_cleanup(self._queue.save)

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
        payload = ListenPayload(track_metadata=TrackMetadata.from_metadata(submission.metadata))
        listen = ListenSubmission(listen_type=ListenType.PLAYING_NOW, payload=[payload])
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
        payload = ListenPayload(
            track_metadata=TrackMetadata.from_metadata(submission.metadata),
            listened_at=submission.start_time,
        )
        self._queue.add(payload)
        submission.submitted = True


class ListenQueue:
    def __init__(self, lbapi: ListenBrainzAPIHelper):
        self._lbapi = lbapi
        self._queue: list[ListenPayload] = []
        self._lock = ReadWriteLockContext()
        self._submitting = False
        self._timer = QTimer()
        self._timer.setInterval(SUBMISSION_INTERVAL_SECONDS * 1000)
        self._timer.timeout.connect(self.submit_batch)

    def load(self):
        cache_file = self.get_cache_file_path()
        if cache_file.exists():
            log.debug("Loading listen queue from %s", cache_file)
            with open(cache_file) as f:
                try:
                    with self._lock.lock_for_write():
                        self._queue = json.load(f, object_hook=from_json)
                        if count := len(self._queue):
                            log.debug("Loaded %d listens from queue", count)
                            self._schedule_submission()
                except json.JSONDecodeError as e:
                    log.error("Failed to load listen queue: %s", e)
                    self._queue = []

    def save(self):
        cache_file = self.get_cache_file_path()
        log.debug("Saving listen queue to %s", cache_file)
        with open(cache_file, 'w') as f:
            with self._lock.lock_for_write():
                data = [asdict(p) for p in self._queue]
                json.dump(data, f)

    def add(self, payload: ListenPayload):
        # Try to submit immediately, and queue if it fails
        submission = ListenSubmission(ListenType.SINGLE, [payload])
        self._submit(submission, partial(self._on_submit_listen_response, payload))

    def _on_submit_listen_response(
        self,
        payload: ListenPayload,
        data,
        reply: QNetworkReply,
        error: QNetworkReply.NetworkError | Exception | None,
    ):
        if error:
            status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if not status_code or int(status_code) in {401, 429} or int(status_code) >= 500:
                log.warning(
                    'Temporary ListenBrainz submission error (queued for retry): data=%s, error=%s', data, error
                )
                self._append(payload)
                self._schedule_submission()
            else:
                log.error('ListenBrainz submission failed: data=%s, error=%s', data, error)
        else:
            log.debug('ListenBrainz submission successful: data=%s', data)

    def submit_batch(self):
        if len(self._queue) == 0 or self._submitting:
            return
        log.debug("Submitting %d queued listens", len(self._queue))
        self._submitting = True  # avoid overlapping submissions
        with self._lock.lock_for_read():
            batch = self._queue[0:MAX_LISTENS_PER_IMPORT]
        submission = ListenSubmission(listen_type=ListenType.IMPORT, payload=batch)
        self._submit(submission, partial(self._on_submit_batch_response, batch))

    def _on_submit_batch_response(
        self,
        batch: list[ListenPayload],
        data,
        reply: QNetworkReply,
        error: QNetworkReply.NetworkError | Exception | None,
    ):
        self._submitting = False
        if error:
            log.error('ListenBrainz batch submission failed: data=%s, error=%s', data, error)
        else:
            log.debug('ListenBrainz batch submission successful: data=%s', data)
            self._remove_from_queue(batch)
            # Check whether there is more data in the queue and directly submit the next
            # batch. Otherwise suspend the submission timer.
            if self._queue:
                self.submit_batch()
            else:
                self._suspend_submission()

    def _submit(self, submission: ListenSubmission, callback: ReplyHandler):
        config = get_config()
        token = config.setting['listenbrainz_token']
        self._lbapi.submit_listen(token, submission, callback)

    def _append(self, payload: ListenPayload):
        log.debug(
            "Queuing for later submission %s: %s - %s",
            payload.listened_at,
            payload.track_metadata.artist_name,
            payload.track_metadata.track_name,
        )
        with self._lock.lock_for_write():
            self._queue.append(payload)

    def _remove_from_queue(self, batch: list[ListenPayload]):
        if not batch:
            return
        with self._lock.lock_for_write():
            # Remove given items from start of queue. Fail if the items differ
            count = len(batch)
            if self._queue[:count] == batch:
                self._queue = self._queue[count:]
            else:
                log.error(
                    "Failed removing items from listen queue, queued items differ from requested items: queued=%s, requested=%s",
                    self._queue[:count],
                    batch,
                )

    def get_cache_file_path(self) -> Path:
        return Path(cache_folder()) / "listenbrainz-queue.json"

    def _schedule_submission(self):
        if len(self._queue) > 0:
            log.debug("Batch listen submission scheduled to run in %d seconds", SUBMISSION_INTERVAL_SECONDS)
            self._timer.start(SUBMISSION_INTERVAL_SECONDS * 1000)

    def _suspend_submission(self):
        log.debug("Batch listen submission suspended")
        self._timer.stop()


def from_json(obj: dict):
    if 'artist_name' in obj and 'track_name' in obj:
        return TrackMetadata.from_dict(obj)
    elif 'track_metadata' in obj:
        return ListenPayload(obj['track_metadata'], obj.get('listened_at'))
    return obj

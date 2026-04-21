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

from unittest.mock import Mock

from PyQt6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
)

from test.picardtestcase import PicardTestCase

from picard.metadata import Metadata
from picard.webservice.api_helpers.listenbrainz import (
    ListenPayload,
    ListenSubmission,
    ListenType,
    TrackMetadata,
)

from picard.ui.player.listenbrainz import (
    ListenQueue,
    PreparedSubmission,
)


class TestPreparedSubmissionService(PicardTestCase):
    def test_can_submit(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        self.assertFalse(submission.can_submit)

    def test_can_submit_after_half_playback(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 9
        self.assertFalse(submission.can_submit)
        submission.elapsed_seconds = 10
        self.assertTrue(submission.can_submit)

    def test_can_submit_after_4_minutes(self):
        metadata = Metadata()
        metadata.length = 500000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 239
        self.assertFalse(submission.can_submit)
        submission.elapsed_seconds = 240
        self.assertTrue(submission.can_submit)

    def test_can_submit_not_if_submitted(self):
        metadata = Metadata()
        metadata.length = 20000  # milliseconds
        submission = PreparedSubmission(metadata, 0)
        submission.elapsed_seconds = 12
        self.assertTrue(submission.can_submit)
        submission.submitted = True
        self.assertFalse(submission.can_submit)

    def test_can_submit_not_zero_seconds(self):
        metadata = Metadata()
        submission = PreparedSubmission(metadata, 0)
        self.assertFalse(submission.can_submit)
        metadata.length = 999
        self.assertFalse(submission.can_submit)


class FakeListenBrainzAPIHelper:
    def __init__(self, data=None, status_code=200, error=None):
        self._data = data or {}
        self._status_code = status_code
        self._error = error
        self.submit_listen = Mock()
        self.submit_listen.side_effect = self._submit_listen

    def _submit_listen(self, token, listen, callback):
        reply = Mock()

        def get_attribute(code):
            if code == QNetworkRequest.Attribute.HttpStatusCodeAttribute:
                return self._status_code
            else:
                return None

        reply.attribute.side_effect = get_attribute
        callback(self._data, reply, self._error)


class TestListenQueue(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.set_config_values({"listenbrainz_token": "test_token"})

    def test_add(self):
        lbapi = FakeListenBrainzAPIHelper()
        queue = ListenQueue(lbapi)
        queue._on_submit_listen_response = Mock()
        payload = ListenPayload(track_metadata=TrackMetadata(artist_name="", track_name=""))
        queue.add(payload)
        lbapi.submit_listen.assert_called_once()
        args = lbapi.submit_listen.call_args.args
        self.assertEqual(args[0], "test_token")
        self.assertEqual(args[1], ListenSubmission(ListenType.SINGLE, [payload]))
        queue._on_submit_listen_response.assert_called_once()
        self.assertEqual([], queue._queue)

    def test_add_failure(self):
        lbapi = FakeListenBrainzAPIHelper(status_code=401, error=QNetworkReply.NetworkError.AuthenticationRequiredError)
        queue = ListenQueue(lbapi)
        payload = ListenPayload(track_metadata=TrackMetadata(artist_name="", track_name=""))
        queue.add(payload)
        self.assertEqual([payload], queue._queue)

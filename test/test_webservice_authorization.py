# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

from unittest.mock import (
    MagicMock,
    patch,
)

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import (
    QNetworkReply,
    QNetworkRequest,
)

from test.picardtestcase import PicardTestCase

from picard.webservice import (
    WebService,
    WSRequest,
)


def dummy_handler(*args, **kwargs):
    """Dummy handler method for tests"""


class WebServiceAuthorizationTest(PicardTestCase):
    """Tests for PICARD-1638: Show authorization required dialog only once."""

    def setUp(self):
        super().setUp()
        self.tmpdir = self.mktmpdir()
        self.patcher = patch('picard.webservice.appdirs.cache_folder', return_value=self.tmpdir)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.rc_patcher = patch('picard.webservice.ratecontrol')
        self.mock_ratecontrol = self.rc_patcher.start()
        self.addCleanup(self.rc_patcher.stop)
        self.set_config_values(
            {
                'use_proxy': False,
                'server_host': 'musicbrainz.org',
                'network_transfer_timeout_seconds': 30,
                'network_cache_size_bytes': 100 * 1000 * 1000,
            }
        )
        self.ws = WebService()
        # Mock timers since they can only be started in a QThread
        self.ws._timer_run_next_task = MagicMock()
        self.ws._timer_count_pending_requests = MagicMock()

    def _make_mblogin_request(self, url='http://musicbrainz.org/ws/2/release/1', handler=None):
        return WSRequest(
            method='GET',
            url=url,
            handler=handler or dummy_handler,
            mblogin=True,
        )

    def _make_reply(
        self, error=QNetworkReply.NetworkError.NoError, status_code=200, url='http://musicbrainz.org/ws/2/release/1'
    ):
        reply = MagicMock()
        reply.error.return_value = error
        reply.attribute.side_effect = lambda attr: {
            QNetworkRequest.Attribute.HttpStatusCodeAttribute: status_code,
            QNetworkRequest.Attribute.HttpReasonPhraseAttribute: 'Unauthorized' if status_code == 401 else 'OK',
            QNetworkRequest.Attribute.Http2WasUsedAttribute: False,
            QNetworkRequest.Attribute.RedirectionTargetAttribute: None,
            QNetworkRequest.Attribute.SourceIsFromCacheAttribute: False,
        }.get(attr)
        reply.request.return_value = MagicMock()
        reply.request.return_value.url.return_value = QUrl(url)
        reply.url.return_value = QUrl(url)
        reply.readAll.return_value = MagicMock(data=MagicMock(return_value=b''))
        reply.errorString.return_value = 'Authorization required'
        return reply

    def test_401_mblogin_queues_request(self):
        """A 401 on an mblogin request should queue it for retry."""
        request = self._make_mblogin_request()
        reply = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
        )
        self.ws._active_requests[reply] = request

        self.ws._handle_reply(reply, request)

        self.assertIn(request, self.ws._awaiting_authorization)
        self.assertTrue(self.ws._authorization_pending)

    def test_401_mblogin_emits_signal_once(self):
        """The authorization_required signal should only be emitted once
        even when multiple requests get 401."""
        signal_spy = MagicMock()
        self.ws.authorization_required.connect(signal_spy)

        for i in range(5):
            request = self._make_mblogin_request(url=f'http://musicbrainz.org/ws/2/release/{i}')
            reply = self._make_reply(
                error=QNetworkReply.NetworkError.AuthenticationRequiredError,
                status_code=401,
                url=f'http://musicbrainz.org/ws/2/release/{i}',
            )
            self.ws._active_requests[reply] = request
            self.ws._handle_reply(reply, request)

        # Signal emitted only once
        signal_spy.assert_called_once()
        # All 5 requests queued
        self.assertEqual(len(self.ws._awaiting_authorization), 5)

    def test_401_non_mblogin_not_queued(self):
        """A 401 on a non-mblogin request should NOT be queued."""
        handler = MagicMock()
        request = WSRequest(
            method='GET',
            url='http://musicbrainz.org/ws/2/release/1',
            handler=handler,
            mblogin=False,
        )
        reply = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
        )
        self.ws._active_requests[reply] = request

        self.ws._handle_reply(reply, request)

        self.assertEqual(len(self.ws._awaiting_authorization), 0)
        # Handler should have been called with the error
        handler.assert_called_once()

    def test_retry_authorized_requests(self):
        """After login, queued requests should be retried via add_request."""
        requests = []
        for i in range(3):
            request = self._make_mblogin_request(url=f'http://musicbrainz.org/ws/2/release/{i}')
            requests.append(request)

        self.ws._awaiting_authorization = list(requests)
        self.ws._authorization_pending = True

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws.retry_authorized_requests()

        self.assertEqual(mock_add_request.call_count, 3)
        for i, request in enumerate(requests):
            self.assertEqual(mock_add_request.call_args_list[i][0][0], request)
        self.assertEqual(self.ws._awaiting_authorization, [])
        self.assertFalse(self.ws._authorization_pending)

    def test_discard_authorized_requests(self):
        """Declining auth should discard queued requests and call handlers with error."""
        handlers = []
        requests = []
        for i in range(3):
            handler = MagicMock()
            handlers.append(handler)
            request = self._make_mblogin_request(
                url=f'http://musicbrainz.org/ws/2/release/{i}',
                handler=handler,
            )
            requests.append(request)

        self.ws._awaiting_authorization = list(requests)
        self.ws._authorization_pending = True

        self.ws.discard_authorized_requests()

        self.assertEqual(self.ws._awaiting_authorization, [])
        self.assertFalse(self.ws._authorization_pending)
        # Each handler should have been called with the auth error
        for handler in handlers:
            handler.assert_called_once()
            args = handler.call_args[0]
            self.assertEqual(args[0], b'')
            self.assertEqual(args[2], QNetworkReply.NetworkError.AuthenticationRequiredError)
            # The reply-like object should provide errorString()
            self.assertEqual(args[1].errorString(), 'Authorization required')

    def test_authorization_pending_reset_allows_new_signal(self):
        """After discard/retry, a new 401 should emit the signal again."""
        signal_spy = MagicMock()
        self.ws.authorization_required.connect(signal_spy)

        # First 401
        request1 = self._make_mblogin_request(url='http://musicbrainz.org/ws/2/release/1')
        reply1 = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
            url='http://musicbrainz.org/ws/2/release/1',
        )
        self.ws._active_requests[reply1] = request1
        self.ws._handle_reply(reply1, request1)
        self.assertEqual(signal_spy.call_count, 1)

        # Discard (user clicked No)
        self.ws.discard_authorized_requests()

        # New 401 should emit signal again
        request2 = self._make_mblogin_request(url='http://musicbrainz.org/ws/2/release/2')
        reply2 = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
            url='http://musicbrainz.org/ws/2/release/2',
        )
        self.ws._active_requests[reply2] = request2
        self.ws._handle_reply(reply2, request2)
        self.assertEqual(signal_spy.call_count, 2)

    def test_401_handler_not_called_when_queued(self):
        """When a 401 mblogin request is queued, the handler should NOT be called."""
        handler = MagicMock()
        request = self._make_mblogin_request(handler=handler)
        reply = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
        )
        self.ws._active_requests[reply] = request

        self.ws._handle_reply(reply, request)

        handler.assert_not_called()

    def test_stop_clears_authorization_queue(self):
        """Calling stop() should clear the authorization queue."""
        request = self._make_mblogin_request()
        self.ws._awaiting_authorization = [request]
        self.ws._authorization_pending = True

        self.ws.stop()

        self.assertEqual(self.ws._awaiting_authorization, [])
        self.assertFalse(self.ws._authorization_pending)

    def test_401_stale_request_retried_immediately_if_now_authorized(self):
        """A 401 on a request that had no token should be retried immediately
        if the user has since logged in (race condition fix)."""
        # Simulate: user is now authorized
        self.ws.oauth_manager = MagicMock()
        self.ws.oauth_manager.is_authorized.return_value = True

        # Request that went out WITHOUT a token (has_auth is False)
        request = self._make_mblogin_request()
        self.assertFalse(request.has_auth)

        reply = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
        )
        self.ws._active_requests[reply] = request

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_reply(reply, request)

        # Should be retried immediately, NOT queued
        mock_add_request.assert_called_once_with(request)
        self.assertEqual(len(self.ws._awaiting_authorization), 0)
        self.assertFalse(self.ws._authorization_pending)

    def test_401_with_auth_token_queued_even_if_authorized(self):
        """A 401 on a request that DID have a token should be queued
        (the token itself was rejected, re-auth needed)."""
        # Simulate: user is still "authorized" (has refresh token)
        self.ws.oauth_manager = MagicMock()
        self.ws.oauth_manager.is_authorized.return_value = True

        # Request that went out WITH a token (has_auth is True)
        request = self._make_mblogin_request()
        request.access_token = 'expired-token'
        self.assertTrue(request.has_auth)

        reply = self._make_reply(
            error=QNetworkReply.NetworkError.AuthenticationRequiredError,
            status_code=401,
        )
        self.ws._active_requests[reply] = request

        signal_spy = MagicMock()
        self.ws.authorization_required.connect(signal_spy)

        self.ws._handle_reply(reply, request)

        # Should be queued, not retried
        self.assertIn(request, self.ws._awaiting_authorization)
        signal_spy.assert_called_once()

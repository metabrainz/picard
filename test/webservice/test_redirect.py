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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


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


# HTTP status codes
HTTP_MOVED_PERMANENTLY = 301
HTTP_FOUND = 302
HTTP_SEE_OTHER = 303
HTTP_TEMPORARY_REDIRECT = 307
HTTP_PERMANENT_REDIRECT = 308


class WebServiceRedirectTest(PicardTestCase):
    """Tests for PICARD-816: Picard does not handle 301 redirects as it should."""

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

    def _make_reply(self, request_url, redirect_target, status_code=HTTP_MOVED_PERMANENTLY):
        """Build a mock QNetworkReply representing a redirect response."""
        reply = MagicMock()
        reply.error.return_value = QNetworkReply.NetworkError.NoError
        reply.attribute.side_effect = lambda attr: {
            QNetworkRequest.Attribute.HttpStatusCodeAttribute: status_code,
            QNetworkRequest.Attribute.HttpReasonPhraseAttribute: 'Moved Permanently',
            QNetworkRequest.Attribute.Http2WasUsedAttribute: False,
            QNetworkRequest.Attribute.RedirectionTargetAttribute: QUrl(redirect_target),
            QNetworkRequest.Attribute.SourceIsFromCacheAttribute: False,
        }.get(attr)
        inner_request = MagicMock()
        inner_request.url.return_value = QUrl(request_url)
        reply.request.return_value = inner_request
        reply.url.return_value = QUrl(request_url)
        reply.readAll.return_value = MagicMock(data=MagicMock(return_value=b''))
        return reply

    def test_301_redirect_is_followed(self):
        """A 301 reply should enqueue a follow-up request to the new location.

        This is the baseline behavior that already works.
        """
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://beta.musicbrainz.org/ws/2/release/abc'
        request = WSRequest(method='GET', url=old_url, handler=dummy_handler)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_MOVED_PERMANENTLY)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        mock_add_request.assert_called_once()
        follow_up = mock_add_request.call_args[0][0]
        self.assertEqual(follow_up.url().toString(), new_url)

    def test_301_permanent_redirect_is_remembered(self):
        """PICARD-816: after a 301, a later request to the old URL should be
        rewritten to the new location instead of hitting the old URL again.

        A 301 is *permanent*: the client is expected to remember the new
        location and stop requesting the old one. Picard currently re-issues
        the redirect every single time, so this test fails until the permanent
        mapping is cached and applied.
        """
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://beta.musicbrainz.org/ws/2/release/abc'

        # First request: server answers with 301 -> new_url.
        first_request = WSRequest(method='GET', url=old_url, handler=dummy_handler)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_MOVED_PERMANENTLY)
        with patch.object(self.ws, 'add_request'):
            self.ws._handle_redirect(reply, first_request, QUrl(new_url))

        # Second, independent request to the SAME old URL. Because the 301 was
        # permanent, it should already target the new location when sent.
        second_request = WSRequest(method='GET', url=old_url, handler=dummy_handler)
        self.ws._apply_known_redirects(second_request)

        self.assertEqual(
            second_request.url().toString(),
            new_url,
            "A permanent (301) redirect should be remembered and applied to later requests",
        )

    def test_302_temporary_redirect_is_not_remembered(self):
        """A 302 (temporary) redirect must NOT be cached: later requests to the
        old URL should still go to the old URL."""
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://tmp.musicbrainz.org/ws/2/release/abc'

        first_request = WSRequest(method='GET', url=old_url, handler=dummy_handler)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_FOUND)
        with patch.object(self.ws, 'add_request'):
            self.ws._handle_redirect(reply, first_request, QUrl(new_url))

        second_request = WSRequest(method='GET', url=old_url, handler=dummy_handler)
        self.ws._apply_known_redirects(second_request)

        self.assertEqual(
            second_request.url().toString(),
            old_url,
            "A temporary (302) redirect must not be remembered",
        )

    def test_307_preserves_method_and_body(self):
        """PICARD-816: a 307 Temporary Redirect must preserve the original
        method and request body. Picard re-issued everything as GET and dropped
        the body, which corrupts a redirected POST/PUT."""
        old_url = 'https://musicbrainz.org/ws/2/submit'
        new_url = 'https://other.musicbrainz.org/ws/2/submit'
        payload = '<xml>data</xml>'
        request = WSRequest(
            method='POST',
            url=old_url,
            handler=dummy_handler,
            data=payload,
            request_mimetype='application/xml',
        )
        reply = self._make_reply(old_url, new_url, status_code=HTTP_TEMPORARY_REDIRECT)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertEqual(follow_up.method, 'POST', "307 must preserve the HTTP method")
        self.assertEqual(follow_up.data, payload, "307 must preserve the request body")
        self.assertEqual(follow_up.request_mimetype, 'application/xml')

    def test_308_preserves_method_and_body(self):
        """A 308 Permanent Redirect must also preserve method and body."""
        old_url = 'https://musicbrainz.org/ws/2/submit'
        new_url = 'https://other.musicbrainz.org/ws/2/submit'
        payload = '<xml>data</xml>'
        request = WSRequest(
            method='PUT',
            url=old_url,
            handler=dummy_handler,
            data=payload,
            request_mimetype='application/xml',
        )
        reply = self._make_reply(old_url, new_url, status_code=HTTP_PERMANENT_REDIRECT)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertEqual(follow_up.method, 'PUT')
        self.assertEqual(follow_up.data, payload)

    def test_303_downgrades_to_get(self):
        """A 303 See Other must change the method to GET and drop the body,
        per HTTP semantics."""
        old_url = 'https://musicbrainz.org/ws/2/submit'
        new_url = 'https://other.musicbrainz.org/ws/2/result'
        request = WSRequest(
            method='POST',
            url=old_url,
            handler=dummy_handler,
            data='<xml>data</xml>',
            request_mimetype='application/xml',
        )
        reply = self._make_reply(old_url, new_url, status_code=HTTP_SEE_OTHER)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertEqual(follow_up.method, 'GET', "303 must downgrade to GET")
        self.assertIsNone(follow_up.data, "303 must drop the request body")

    def test_multi_hop_redirect_loop_detected(self):
        """PICARD-816: a multi-hop redirect loop (A -> B -> A) must be detected.

        The old self-redirect check only caught an immediate A -> A loop. A
        request that bounces A -> B -> A would otherwise redirect forever."""
        url_a = 'https://a.musicbrainz.org/resource'
        url_b = 'https://b.musicbrainz.org/resource'

        captured = []

        def capture_handler(document, reply, error):
            captured.append(error)

        # Hop 1: request to A redirects to B.
        request_a = WSRequest(method='GET', url=url_a, handler=capture_handler)
        reply_a = self._make_reply(url_a, url_b, status_code=HTTP_FOUND)
        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply_a, request_a, QUrl(url_b))
        request_b = mock_add_request.call_args[0][0]

        # Hop 2: B redirects back to A, which is already in the chain -> loop.
        reply_b = self._make_reply(url_b, url_a, status_code=HTTP_FOUND)
        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply_b, request_b, QUrl(url_a))

        self.assertFalse(
            mock_add_request.called,
            "A multi-hop redirect loop must not enqueue another request",
        )
        self.assertEqual(
            captured,
            [QNetworkReply.NetworkError.TooManyRedirectsError],
            "A multi-hop loop should report TooManyRedirectsError to the handler",
        )

    def test_same_origin_redirect_keeps_authentication(self):
        """A redirect that stays on the same origin keeps the mblogin flag, so
        authenticated MusicBrainz requests still work across e.g. an http->https
        upgrade on the same host."""
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://musicbrainz.org/ws/2/release/xyz'
        request = WSRequest(method='GET', url=old_url, handler=dummy_handler, mblogin=True)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_FOUND)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertTrue(follow_up.mblogin, "Same-origin redirect must keep authentication")

    def test_cross_origin_redirect_drops_authentication(self):
        """RFC 9110 15.4: credentials must not be forwarded across an origin
        boundary. A redirect to a different host must drop the mblogin flag."""
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://evil.example.com/ws/2/release/abc'
        request = WSRequest(method='GET', url=old_url, handler=dummy_handler, mblogin=True)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_FOUND)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertFalse(follow_up.mblogin, "Cross-origin redirect must drop authentication")

    def test_cross_scheme_redirect_drops_authentication(self):
        """A redirect that changes the scheme (https -> http) is cross-origin and
        must drop authentication."""
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'http://musicbrainz.org/ws/2/release/abc'
        request = WSRequest(method='GET', url=old_url, handler=dummy_handler, mblogin=True)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_FOUND)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertFalse(follow_up.mblogin, "Cross-scheme redirect must drop authentication")

    def test_same_origin_default_port_keeps_authentication(self):
        """An explicit default port must be treated as the same origin as an
        implicit one (https://host and https://host:443)."""
        old_url = 'https://musicbrainz.org/ws/2/release/abc'
        new_url = 'https://musicbrainz.org:443/ws/2/release/xyz'
        request = WSRequest(method='GET', url=old_url, handler=dummy_handler, mblogin=True)
        reply = self._make_reply(old_url, new_url, status_code=HTTP_FOUND)

        with patch.object(self.ws, 'add_request') as mock_add_request:
            self.ws._handle_redirect(reply, request, QUrl(new_url))

        follow_up = mock_add_request.call_args[0][0]
        self.assertTrue(follow_up.mblogin, "Explicit default port must count as same origin")

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

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2022, 2025-2026 Laurent Monin
# Copyright (C) 2019, 2022, 2024-2025 Philipp Wolfer
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


from io import BytesIO
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.browser.server import (
    RequestHandler,
    clean_header,
)
from picard.const import METABRAINZ_OAUTH_SCOPES
from picard.debug_opts import DebugOpt
from picard.oauth import OAuthInvalidStateError


class BrowserIntegrationTest(PicardTestCase):
    def test_clean_header(self):
        bad_header = "foo\nSome-Header: bar"
        self.assertEqual("fooSome-Header bar", clean_header(bad_header))


class RequestHandlerAuthTest(PicardTestCase):
    """Tests for PICARD-3398: Pending request stuck if authentication gets cancelled."""

    def setUp(self):
        super().setUp()
        self.set_config_values({'server_host': 'musicbrainz.org'})
        self.callback = MagicMock()
        self.oauth_manager = MagicMock()
        self.oauth_manager.verify_state.return_value = self.callback
        self.tagger.webservice.oauth_manager = self.oauth_manager
        self.patch_tagger_instance('picard.browser.server')

    def _make_handler(self, path):
        """Create a RequestHandler instance without starting a real HTTP server."""
        handler = RequestHandler.__new__(RequestHandler)
        handler.server_version = 'Test'
        handler.sys_version = ''
        handler.path = path
        handler.headers = {'origin': None}
        handler.wfile = BytesIO()
        handler.requestline = f'GET {path} HTTP/1.1'
        handler.command = 'GET'
        handler.request_version = 'HTTP/1.1'
        handler.responses = {}
        handler.client_address = ('127.0.0.1', 0)
        return handler

    @patch('picard.browser.server.to_main')
    def test_auth_cancelled_calls_callback(self, mock_to_main):
        """When auth is cancelled (error=access_denied), the callback should be
        called with successful=False so pending requests are released."""
        handler = self._make_handler('/auth?error=access_denied&state=valid_state')

        handler._handle_get()

        self.oauth_manager.verify_state.assert_called_once_with('valid_state')
        mock_to_main.assert_called_once_with(self.callback, successful=False, error_msg='access_denied')
        response = handler.wfile.getvalue()
        self.assertIn(b'Authentication cancelled', response)
        self.assertIn(b'<!doctype html>', response)

    @patch('picard.browser.server.to_main')
    def test_auth_cancelled_with_error_description(self, mock_to_main):
        """When auth error includes error_description, it should be in the callback."""
        handler = self._make_handler(
            '/auth?error=access_denied&error_description=The+user+denied+the+request&state=valid_state'
        )

        handler._handle_get()

        mock_to_main.assert_called_once_with(self.callback, successful=False, error_msg='The user denied the request')

    @patch('picard.browser.server.to_main')
    def test_auth_success_still_works(self, mock_to_main):
        """Ensure normal auth success flow is not broken."""
        handler = self._make_handler('/auth?code=auth_code_123&state=valid_state')

        handler._handle_get()

        self.oauth_manager.verify_state.assert_called_once_with('valid_state')
        mock_to_main.assert_called_once()
        self.callback.assert_not_called()
        # The code exchange must request the same prefixed scopes as the
        # authorization request; a mismatch yields a token without the
        # expected permissions (e.g. collection access fails with 401).
        self.assertEqual(mock_to_main.call_args.kwargs['scopes'], METABRAINZ_OAUTH_SCOPES)
        self.assertIn('musicbrainz:collection', mock_to_main.call_args.kwargs['scopes'])
        response = handler.wfile.getvalue()
        self.assertIn(b'Authentication successful', response)
        self.assertIn(b'<!doctype html>', response)

    @subtest_cases(
        "path",
        [
            '/auth?code=auth_code_123&state=bad',
            '/auth?error=access_denied&state=bad',
        ],
    )
    def test_auth_invalid_state(self, path):
        """An invalid state should return 400 regardless of code or error."""
        self.oauth_manager.verify_state.side_effect = OAuthInvalidStateError()
        self.oauth_manager.verify_state.reset_mock()
        handler = self._make_handler(path)

        handler._handle_get()

        self.oauth_manager.verify_state.assert_called_once_with('bad')
        self.callback.assert_not_called()
        response = handler.wfile.getvalue()
        self.assertIn(b'400', response)
        self.assertIn(b'<!doctype html>', response)
        self.assertIn(b'Authentication error', response)

    def test_auth_no_code_no_error(self):
        """When auth has neither code nor error, return 400 with a styled page."""
        handler = self._make_handler('/auth?state=valid_state')

        handler._handle_get()

        response = handler.wfile.getvalue()
        self.assertIn(b'400', response)
        self.assertIn(b'<!doctype html>', response)
        self.assertIn(b'Authentication error', response)

    def test_favicon_serves_svg_logo(self):
        """The browser's implicit /favicon.ico request is served the Picard logo."""
        handler = self._make_handler('/favicon.ico')

        handler._handle_get()

        response = handler.wfile.getvalue()
        self.assertIn(b'200', response)
        self.assertIn(b'image/svg+xml', response)
        self.assertIn(b'<svg', response)


class RequestHandlerAccessLogTest(PicardTestCase):
    """The per-request access log must not leak OAuth callback parameters.

    The stdlib BaseHTTPRequestHandler access log emits the full request line,
    including the query string. For the /auth callback that query contains the
    raw OAuth authorization code and state. That access line is now gated behind
    the opt-in DebugOpt.BROWSER, so it is silent on a normal --debug run and the
    code never reaches the log by default.
    """

    def setUp(self):
        super().setUp()
        DebugOpt.set_registry(set())

    def _make_handler(self):
        handler = RequestHandler.__new__(RequestHandler)
        handler.client_address = ('127.0.0.1', 0)
        return handler

    def test_access_log_silent_by_default(self):
        handler = self._make_handler()
        # assertNoLogs raises if any record is emitted on 'main'.
        with self.assertNoLogs('main', level='DEBUG'):
            handler.log_message('%s', 'GET /auth?code=SECRETCODE&state=abc HTTP/1.1')

    def test_access_log_enabled_by_debug_opt(self):
        DebugOpt.BROWSER.enabled = True
        handler = self._make_handler()
        with self.assertLogs('main', level='DEBUG') as cm:
            handler.log_message('%s', 'GET /auth?code=SECRETCODE&state=abc HTTP/1.1')
        output = '\n'.join(cm.output)
        # When the dev explicitly opts in, the full request line is logged.
        self.assertIn('SECRETCODE', output)

    def test_error_log_always_emitted(self):
        # Genuine request errors must still surface regardless of the opt; they
        # do not carry the OAuth code.
        handler = self._make_handler()
        with self.assertLogs('main', level='DEBUG') as cm:
            handler.log_error('%s', 'Bad request')
        self.assertIn('Bad request', '\n'.join(cm.output))

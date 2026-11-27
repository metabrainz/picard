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

"""Log in to MusicBrainz and out, without the GUI.

The login uses OAuth (see :class:`picard.oauth.OAuthManager`): the user opens
the URL of :func:`start_login` in a browser and authorizes Picard, and the
browser is redirected to Picard on the loopback address with a code, which is
exchanged for the tokens. Once the tokens are known, the name of the user is
fetched and the user's collections are loaded. (MusicBrainz no longer offers
the "out of band" flow, where it showed the code for the user to copy.)

The redirect is received by the browser integration of the GUI when it runs,
otherwise by :class:`LoginRedirectReceiver`; both complete the login with
:func:`receive_login_redirect`. When the browser runs on another machine and
could not reach Picard, the address it was redirected to can be given by hand
to :func:`finish_login_redirect`.

A frontend decides how the URL is opened; the GUI opens a browser, a console
prints the URL.

Every ``callback`` is called with ``(successful, error_msg)`` when it is done.
"""

from collections.abc import Callable
from functools import partial
from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer,
)
from socketserver import BaseServer
import threading
from typing import (
    Any,
    NamedTuple,
)
from urllib.parse import (
    parse_qs,
    urlparse,
)

from picard import log
from picard.browser import auth_responses
from picard.browser.ports import create_listening_server
from picard.collection import load_user_collections
from picard.const import (
    BROWSER_INTEGRATION_LOCALIP,
    METABRAINZ_OAUTH_SCOPES,
)
from picard.oauth import (
    OAuthInvalidStateError,
    OAuthManager,
)
from picard.services import services
from picard.util.thread import to_main


LoginCallback = Callable[[bool, str | None], Any]


def _oauth_manager() -> OAuthManager:
    return services().webservice.oauth_manager


def start_login(callback: LoginCallback) -> str:
    """Begin a login, and return the URL the user has to open to authorize Picard.

    ``callback`` is called when the login completes, once the redirect of the
    browser is received (see :func:`receive_login_redirect`). The redirect URI
    of the OAuth manager has to be set first: the address the redirect is
    received at.
    """
    return _oauth_manager().get_authorization_url(METABRAINZ_OAUTH_SCOPES, partial(_authorization_finished, callback))


def logout(callback: LoginCallback) -> None:
    """Log out: revoke the authorization on MusicBrainz, and forget the user's collections.

    The whole authorization is revoked, so every Picard using it is logged out.
    """
    _oauth_manager().revoke_tokens(partial(_logout_finished, callback))


def _authorization_finished(callback: LoginCallback, successful: bool = False, error_msg: str | None = None) -> None:
    if successful:
        _oauth_manager().fetch_username(partial(_login_finished, callback))
    else:
        callback(False, error_msg)


def _login_finished(callback: LoginCallback, successful: bool, error_msg: str | None) -> None:
    if successful:
        load_user_collections()
    callback(successful, error_msg)


def _logout_finished(callback: LoginCallback, successful: bool, error_msg: str | None) -> None:
    if successful:
        load_user_collections()
    callback(successful, error_msg)


class LoginRedirect(NamedTuple):
    """The query the browser was redirected with at the end of a login."""

    state: str
    code: str = ''
    error: str = ''
    error_description: str = ''


def parse_login_redirect(query: str) -> 'LoginRedirect | None':
    """The redirect in ``query``, the query of the ``/auth`` request the browser was sent to.

    Returns None when it has no ``state``, or neither a ``code`` nor an ``error``.
    """
    args = parse_qs(query)

    def value(key: str) -> str:
        return args.get(key, [''])[0]

    if not value('state') or not (value('code') or value('error')):
        return None
    return LoginRedirect(value('state'), value('code'), value('error'), value('error_description'))


def finish_login_redirect(redirect: LoginRedirect) -> None:
    """Complete a login begun by :func:`start_login` with a redirect given by hand.

    For a browser that could not reach Picard (it runs on another machine); a
    redirect that reaches Picard is handled by :func:`receive_login_redirect`.
    The callback given to :func:`start_login` is called when it is done. It must
    be the same process: the URL and the code are bound to secrets kept in
    memory (PKCE, and the state).

    Raises :class:`~picard.oauth.OAuthInvalidStateError` if the redirect is not
    that of a login begun in this process (or was already used).
    """
    authorization_finished = _oauth_manager().verify_state(redirect.state)
    _complete_login(redirect, authorization_finished)


def receive_login_redirect(query: str) -> tuple[int, str]:
    """Handle the redirect of the browser at the end of a login, as an HTTP server receives it.

    ``query`` is the query of the ``/auth`` request. Returns the status and the
    HTML page to answer with. It is meant to be called in the thread of the
    server: the state is checked at once, so that the browser is told when the
    redirect is not that of a login begun by this Picard, and the login is
    completed on the main thread. Used by the browser integration and by
    :class:`LoginRedirectReceiver`.
    """
    redirect = parse_login_redirect(query)
    if redirect is None:
        # The endpoint was likely called by something other than the redirect of MusicBrainz.
        log.warning("Login: invalid OAuth callback parameters")
        return 400, auth_responses.error_page()
    try:
        authorization_finished = _oauth_manager().verify_state(redirect.state)
    except OAuthInvalidStateError:
        # An invalid state often means a different Picard instance is
        # responding (e.g. Picard was restarted during the login).
        log.warning("Login: invalid OAuth state parameter")
        return 400, auth_responses.error_page()
    to_main(_complete_login, redirect, authorization_finished)
    if redirect.code:
        return 200, auth_responses.success_page()
    log.info("Login: authorization denied: %s", redirect.error_description or redirect.error)
    return 200, auth_responses.cancelled_page(redirect.error, redirect.error_description)


def _complete_login(redirect: LoginRedirect, authorization_finished: Callable[..., Any]) -> None:
    """Exchange the code of a redirect whose state was verified, or report the refusal."""
    if redirect.code:
        _oauth_manager().exchange_authorization_code(redirect.code, METABRAINZ_OAUTH_SCOPES, authorization_finished)
    else:
        authorization_finished(successful=False, error_msg=redirect.error_description or redirect.error)


class LoginRedirectReceiver:
    """Receive the redirect of the browser at the end of a login, on the loopback address.

    It answers the ``/auth`` redirect only (see :func:`receive_login_redirect`,
    which completes the login), unlike the browser integration of the GUI, and
    stops once it got the redirect of the login. It listens on a port of the
    range of the browser integration (see :mod:`picard.browser.ports`).
    """

    PATH = '/auth'

    def __init__(self) -> None:
        self._server: HTTPServer | None = None

    @property
    def is_running(self) -> bool:
        return self._server is not None

    @property
    def redirect_uri(self) -> 'str | None':
        """The address the browser is to be redirected to, or None if it is not running."""
        if self._server is None:
            return None
        return f'http://{BROWSER_INTEGRATION_LOCALIP}:{self._server.server_address[1]}{self.PATH}'

    def start(self) -> bool:
        """Listen on the first free port of the range; return whether one was found."""
        self.stop()
        self._server = create_listening_server(HTTPServer, BROWSER_INTEGRATION_LOCALIP, self._make_handler())
        if self._server is None:
            log.warning("Login: no free port to receive the redirect of the browser")
            return False
        log.debug("Login: waiting for the redirect of the browser on port %d", self._server.server_address[1])
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return True

    def stop(self) -> None:
        server, self._server = self._server, None
        if server is not None:
            server.shutdown()
            server.server_close()

    def _stop_server(self, server: BaseServer) -> None:
        """Stop ``server`` if it is still the one listening (not one started since)."""
        if self._server is server:
            self.stop()

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path != receiver.PATH:
                    self._respond(404, auth_responses.error_page())
                    return
                status, page = receive_login_redirect(parsed.query)
                if status == 200:
                    # The redirect of the login: nothing more to receive. The
                    # server cannot be shut down from its own thread. Queued
                    # before the answer, so it is when the browser has the page.
                    to_main(receiver._stop_server, self.server)
                self._respond(status, page)

            def _respond(self, status: int, content: str) -> None:
                self.send_response(status)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Cache-Control', 'max-age=0')
                self.end_headers()
                self.wfile.write(content.encode())

            def log_message(self, format: str, *args: Any) -> None:
                # The request line holds the authorization code: never log it.
                pass

        return Handler

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
the URL of :func:`start_login` in a browser and authorizes Picard. Then either
MusicBrainz shows a code, which :func:`finish_login` exchanges for the tokens
(the "out of band" flow, when the redirect URI is not set), or the browser is
redirected to the browser integration of Picard, which completes the login
itself. Once the tokens are known, the name of the user is fetched and the
user's collections are loaded.

A frontend decides how the URL is opened and the code asked for; the GUI opens
a browser and shows a dialog, a console prints the URL.

The redirect of the browser is handled by :func:`receive_login_redirect`, for
the HTTP server that receives it.

Every ``callback`` is called with ``(successful, error_msg)`` when it is done.
"""

from collections.abc import Callable
from functools import partial
from typing import (
    Any,
    NamedTuple,
)
from urllib.parse import parse_qs

from picard import log
from picard.browser import auth_responses
from picard.collection import load_user_collections
from picard.const import METABRAINZ_OAUTH_SCOPES
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

    ``callback`` is called when the login completes: after :func:`finish_login`,
    or when the browser integration receives the redirect of the browser.
    """
    return _oauth_manager().get_authorization_url(METABRAINZ_OAUTH_SCOPES, partial(_authorization_finished, callback))


def finish_login(authorization_code: str, callback: LoginCallback) -> None:
    """Complete a login begun by :func:`start_login` with the code MusicBrainz showed.

    It must be the same process: the URL and the code are bound to a secret
    kept in memory (PKCE).
    """
    _oauth_manager().exchange_authorization_code(
        authorization_code,
        METABRAINZ_OAUTH_SCOPES,
        partial(_authorization_finished, callback),
    )


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


def receive_login_redirect(query: str) -> tuple[int, str]:
    """Handle the redirect of the browser at the end of a login, as an HTTP server receives it.

    ``query`` is the query of the ``/auth`` request. Returns the status and the
    HTML page to answer with. It is meant to be called in the thread of the
    server: the state is checked at once, so that the browser is told when the
    redirect is not that of a login begun by this Picard, and the login is
    completed on the main thread.
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

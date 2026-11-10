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

Every ``callback`` is called with ``(successful, error_msg)`` when it is done.
"""

from collections.abc import Callable
from functools import partial
from typing import Any

from picard.collection import load_user_collections
from picard.const import METABRAINZ_OAUTH_SCOPES
from picard.services import services


LoginCallback = Callable[[bool, str | None], Any]


def start_login(callback: LoginCallback) -> str:
    """Begin a login, and return the URL the user has to open to authorize Picard.

    ``callback`` is called when the login completes: after :func:`finish_login`,
    or when the browser integration receives the redirect of the browser.
    """
    oauth_manager = services().webservice.oauth_manager
    return oauth_manager.get_authorization_url(METABRAINZ_OAUTH_SCOPES, partial(_authorization_finished, callback))


def finish_login(authorization_code: str, callback: LoginCallback) -> None:
    """Complete a login begun by :func:`start_login` with the code MusicBrainz showed.

    It must be the same process: the URL and the code are bound to a secret
    kept in memory (PKCE).
    """
    oauth_manager = services().webservice.oauth_manager
    oauth_manager.exchange_authorization_code(
        authorization_code,
        METABRAINZ_OAUTH_SCOPES,
        partial(_authorization_finished, callback),
    )


def logout(callback: LoginCallback) -> None:
    """Log out: revoke the authorization on MusicBrainz, and forget the user's collections.

    The whole authorization is revoked, so every Picard using it is logged out.
    """
    services().webservice.oauth_manager.revoke_tokens(partial(_logout_finished, callback))


def _authorization_finished(callback: LoginCallback, successful: bool = False, error_msg: str | None = None) -> None:
    if successful:
        services().webservice.oauth_manager.fetch_username(partial(_login_finished, callback))
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

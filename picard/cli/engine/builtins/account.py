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

"""The commands on the MusicBrainz account: ``login`` and ``logout``.

MusicBrainz sends the browser back to Picard at the end of a login, on the
loopback address. ``login`` listens there (as the browser integration of the
GUI does) and prints the address to open; once Picard is authorized in the
browser, ``login`` again finishes it. When the browser runs on another machine
(over ssh) the redirect cannot reach Picard: the page fails to load, and its
address, given to ``login <address>``, finishes the login just the same.

The tokens are kept in the configuration, as the GUI does, so a login of the
GUI is used as it is, and the other way round.
"""

from typing import Any
from urllib.parse import urlparse

from picard import mblogin
from picard.browser.ports import port_range
from picard.cli.engine.builtins.helpers import (
    TIMEOUT_SHORT,
    arg_joined,
    drain,
    join_notes,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import EngineSession
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.const import BROWSER_INTEGRATION_LOCALIP
from picard.oauth import OAuthInvalidStateError
from picard.services import services


class _PendingLogin:
    """A login begun by ``login`` and not finished yet: the address to open, and what receives the redirect.

    The address is kept: asking MusicBrainz for another one would make the first
    one useless (each is bound to a new secret).
    """

    def __init__(self) -> None:
        self.receiver = mblogin.LoginRedirectReceiver()
        self.url: str | None = None
        self.outcome: dict[str, Any] = {}

    def start(self) -> str:
        """Begin the login and return the address to open."""
        self.outcome.clear()
        oauth_manager = _oauth_manager()
        if self.receiver.start():
            oauth_manager.redirect_uri = self.receiver.redirect_uri
        else:
            # Nothing can listen: the address of the failed redirect has to be given by hand.
            oauth_manager.redirect_uri = f'http://{BROWSER_INTEGRATION_LOCALIP}:{port_range()[0]}/auth'
        self.url = mblogin.start_login(self._finished)
        return self.url

    def _finished(self, successful: bool, error_msg: 'str | None') -> None:
        self.outcome.update(successful=successful, error=error_msg)

    def end(self) -> None:
        self.receiver.stop()
        self.url = None


# The login being made. One per process, as the OAuth state it relies on.
_pending = _PendingLogin()


def _oauth_manager():
    return services().webservice.oauth_manager


def _account_item(status: str, **data: Any) -> EngineItemResult:
    """An item for the account, which has no handle."""
    return EngineItemResult(handle='', status=status, data=data)


def _waiting(url: str, notes: 'list[str] | None' = None) -> EngineResult:
    message = (
        "open this address and authorize Picard, then run 'login' again; if the browser "
        "could not reach Picard (another machine), give the address it shows: login <address>"
    )
    return EngineResult(
        items=[_account_item('authorization_required', url=url)],
        message=join_notes([message, *(notes or [])]),
    )


def _redirect_in(text: str) -> 'mblogin.LoginRedirect | None':
    """The redirect in ``text``: the address the browser was sent to, or its query."""
    text = text.strip()
    query = urlparse(text).query if '://' in text else text.lstrip('?')
    return mblogin.parse_login_redirect(query)


def _finish(session: EngineSession, redirect: mblogin.LoginRedirect) -> EngineResult:
    """Finish the pending login with ``redirect``, and say how it went."""
    try:
        mblogin.finish_login_redirect(redirect)
    except OAuthInvalidStateError:
        return EngineResult(
            items=[_account_item('login_failed', error="this is not the address of the login begun with 'login'")]
        )
    notes: list[str] = []
    drain(session, TIMEOUT_SHORT, notes)
    return _report(join_notes(notes))


def _report(message: str = '') -> EngineResult:
    """How the pending login went: a timeout while it is not done yet."""
    outcome = _pending.outcome
    if not outcome:
        return EngineResult(items=[_account_item('timeout')], message=message)
    _pending.end()
    if not outcome['successful']:
        error = outcome['error'] or "the login failed"
        return EngineResult(items=[_account_item('login_failed', error=error)], message=message)
    return EngineResult(items=[_account_item('logged_in', username=_oauth_manager().username)], message=message)


@command(
    'login',
    usage='login [address]',
    help="Log in to MusicBrainz.",
    args=('address',),
    arg_kinds=('',),
)
def _cmd_login(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Log in to MusicBrainz, to use the collections.

    'login' prints an address: open it in a browser and authorize Picard there.
    MusicBrainz then sends the browser back to Picard; run 'login' again to finish.

    If the browser runs on another machine (Picard is used over ssh, say), it
    cannot reach Picard and shows an error page instead. Copy the address of that
    page, which starts with http://127.0.0.1, and give it: 'login <address>'. Use
    quotes if your shell needs them. It has to be the same session.

    The tokens are stored in the configuration, as the GUI does: logging in here
    logs in every Picard that uses the same configuration, and a login made by the
    GUI is used as it is. 'logout' revokes them for all of them.

    The result is logged_in (with the name of the user), authorization_required
    (with the address to open), login_failed or timeout.

    Examples:
      login
      login 'http://127.0.0.1:8000/auth?code=...&state=...'
    """
    text = arg_joined(args.get('address'))
    if text:
        redirect = _redirect_in(text)
        if redirect is None:
            return EngineResult.failure("login: not the address the browser was sent to (it has a code and a state)")
        if _pending.url is None:
            return EngineResult.failure("login: no login begun in this session; run 'login' first")
        return _finish(session, redirect)

    if _oauth_manager().is_logged_in():
        _pending.end()
        return EngineResult(items=[_account_item('logged_in', username=_oauth_manager().username)])
    if _pending.url is None:
        return _waiting(_pending.start())
    # If the browser came back, the receiver completes the login on the main
    # thread: let it run (the shell does not while it waits for a command).
    notes: list[str] = []
    drain(session, TIMEOUT_SHORT, notes)
    if _pending.outcome:
        return _report(join_notes(notes))
    # The browser has not come back yet.
    return _waiting(_pending.url, notes)


@command(
    'logout',
    usage='logout',
    help="Log out of MusicBrainz.",
    destructive=True,
)
def _cmd_logout(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Log out of MusicBrainz.

    The authorization is revoked on MusicBrainz, so every Picard that uses it is
    logged out, the GUI included: that is why the console asks to confirm.

    The result is logged_out, not_logged_in, logout_failed or timeout.
    """
    if not _oauth_manager().is_authorized():
        return EngineResult(items=[_account_item('not_logged_in')])

    outcome: dict[str, Any] = {}

    def finished(successful: bool, error_msg: 'str | None') -> None:
        outcome.update(successful=successful, error=error_msg)

    notes: list[str] = []
    mblogin.logout(finished)
    drain(session, TIMEOUT_SHORT, notes)
    message = join_notes(notes)
    if not outcome:
        return EngineResult(items=[_account_item('timeout')], message=message)
    if not outcome['successful']:
        error = outcome['error'] or "the logout failed"
        return EngineResult(items=[_account_item('logout_failed', error=error)], message=message)
    return EngineResult(items=[_account_item('logged_out')], message=message)

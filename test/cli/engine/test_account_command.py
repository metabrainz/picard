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

"""``login`` and ``logout``."""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.cli.engine.helpers import EngineCommandTestCase

from picard import mblogin
from picard.browser.ports import port_range
from picard.cli.engine.builtins import account
from picard.oauth import OAuthInvalidStateError


class AccountCommandTestCase(EngineCommandTestCase):
    def setUp(self):
        super().setUp()
        self.oauth = MagicMock()
        self.oauth.is_logged_in.return_value = False
        self.oauth.is_authorized.return_value = False
        self.oauth.username = 'alice'
        patcher = patch('picard.cli.engine.builtins.account._oauth_manager', return_value=self.oauth)
        patcher.start()
        self.addCleanup(patcher.stop)
        # The real parsing of a redirect; the rest of the login is faked.
        self.mblogin = MagicMock()
        self.mblogin.parse_login_redirect = mblogin.parse_login_redirect
        self.mblogin.LoginRedirect = mblogin.LoginRedirect
        self.mblogin.start_login.return_value = _URL
        patcher = patch('picard.cli.engine.builtins.account.mblogin', self.mblogin)
        patcher.start()
        self.addCleanup(patcher.stop)
        # A fresh pending login for each test, with a fake receiver.
        pending = account._PendingLogin()
        self.receiver = MagicMock()
        self.receiver.start.return_value = True
        self.receiver.redirect_uri = 'http://127.0.0.1:8001/auth'
        pending.receiver = self.receiver
        patcher = patch.object(account, '_pending', pending)
        patcher.start()
        self.addCleanup(patcher.stop)

    def login_callback(self):
        return self.mblogin.start_login.call_args.args[0]

    def browser_comes_back(self, successful=True, error_msg=None):
        """The receiver got the redirect: the next run of the event loop completes the login."""

        def run_until_idle(timeout=None):
            self.login_callback()(successful, error_msg)
            return True

        self.session._app.run_until_idle.side_effect = run_until_idle

    def answer(self, successful=True, error_msg=None):
        """A redirect given by hand: its code is exchanged, then the callback of the login is called."""

        def finish(redirect):
            self.login_callback()(successful, error_msg)

        self.mblogin.finish_login_redirect.side_effect = finish


_URL = 'https://metabrainz.org/oauth2/authorize?x=1'
_REDIRECT = 'http://127.0.0.1:8001/auth?code=abc123&state=xyz'


class LoginCommandTest(AccountCommandTestCase):
    def test_begins_a_login(self):
        result = self.run_command('login')
        self.assertTrue(result.ok, result.error)
        item = result.items[0]
        self.assertEqual('authorization_required', item.status)
        self.assertEqual(_URL, item.data['url'])
        self.assertIn("run 'login' again", result.message)
        self.receiver.start.assert_called_once()
        # The browser is to come back to the receiver.
        self.assertEqual('http://127.0.0.1:8001/auth', self.oauth.redirect_uri)

    def test_no_free_port_still_gives_an_address(self):
        self.receiver.start.return_value = False
        result = self.run_command('login')
        self.assertEqual('authorization_required', result.items[0].status)
        self.assertEqual(f'http://127.0.0.1:{port_range()[0]}/auth', self.oauth.redirect_uri)

    def test_again_before_the_browser_came_back_gives_the_same_address(self):
        self.run_command('login')
        result = self.run_command('login')
        self.assertEqual('authorization_required', result.items[0].status)
        self.assertEqual(_URL, result.items[0].data['url'])
        self.mblogin.start_login.assert_called_once()
        # The event loop ran, so that a received redirect would have completed the login.
        self.session._app.run_until_idle.assert_called()

    def test_again_after_the_browser_came_back_logs_in(self):
        self.run_command('login')
        self.browser_comes_back()
        result = self.run_command('login')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('logged_in', result.items[0].status)
        self.assertEqual('alice', result.items[0].data['username'])
        self.mblogin.finish_login_redirect.assert_not_called()
        self.receiver.stop.assert_called()

    def test_refused_in_the_browser(self):
        self.run_command('login')
        self.browser_comes_back(successful=False, error_msg='access_denied')
        item = self.run_command('login').items[0]
        self.assertEqual('login_failed', item.status)
        self.assertEqual('access_denied', item.data['error'])
        # A new login can be begun.
        self.session._app.run_until_idle.side_effect = None
        self.mblogin.start_login.reset_mock()
        self.run_command('login')
        self.mblogin.start_login.assert_called_once()

    def test_the_address_of_the_failed_redirect_logs_in(self):
        for text in (_REDIRECT, f"'{_REDIRECT}'", 'code=abc123&state=xyz', '?code=abc123&state=xyz'):
            with self.subTest(text=text):
                self.mblogin.finish_login_redirect.reset_mock()
                self.run_command('login')  # begun again after the previous subtest
                self.answer()
                result = self.run_command(f'login {text}')
                self.assertTrue(result.ok, result.error)
                self.assertEqual('logged_in', result.items[0].status)
                self.mblogin.finish_login_redirect.assert_called_once_with(mblogin.LoginRedirect('xyz', 'abc123'))

    def test_an_address_without_a_login_begun(self):
        result = self.run_command(f'login {_REDIRECT}')
        self.assertFalse(result.ok)
        self.assertIn("run 'login' first", result.error)

    def test_not_a_redirect(self):
        self.run_command('login')
        for text in ('abc123', 'https://musicbrainz.org/'):
            with self.subTest(text=text):
                result = self.run_command(f'login {text}')
                self.assertFalse(result.ok)
                self.assertIn('not the address', result.error)
        self.mblogin.finish_login_redirect.assert_not_called()

    def test_the_address_of_another_login(self):
        self.run_command('login')
        self.mblogin.finish_login_redirect.side_effect = OAuthInvalidStateError
        item = self.run_command(f'login {_REDIRECT}').items[0]
        self.assertEqual('login_failed', item.status)
        self.assertIn("not the address of the login", item.data['error'])

    def test_refused(self):
        self.run_command('login')
        self.answer(successful=False, error_msg='access_denied')
        item = self.run_command(f'login {_REDIRECT}').items[0]
        self.assertEqual('login_failed', item.status)
        self.assertEqual('access_denied', item.data['error'])

    def test_failure_without_a_reason(self):
        self.run_command('login')
        self.answer(successful=False)
        self.assertTrue(self.run_command(f'login {_REDIRECT}').items[0].data['error'])

    def test_timeout_then_done(self):
        self.run_command('login')
        self.session._app.run_until_idle.return_value = False
        result = self.run_command(f'login {_REDIRECT}')
        self.assertEqual('timeout', result.items[0].status)
        self.assertIn('timed out', result.message)
        # The answer came later: the next 'login' reports it.
        self.login_callback()(True, None)
        self.session._app.run_until_idle.return_value = True
        self.assertEqual('logged_in', self.run_command('login').items[0].status)

    def test_already_logged_in(self):
        self.oauth.is_logged_in.return_value = True
        result = self.run_command('login')
        self.assertEqual('logged_in', result.items[0].status)
        self.assertEqual('alice', result.items[0].data['username'])
        self.mblogin.start_login.assert_not_called()


class LogoutCommandTest(AccountCommandTestCase):
    def test_is_destructive(self):
        self.assertTrue(self.reg.get('logout').destructive)

    def test_logs_out(self):
        self.oauth.is_authorized.return_value = True
        self.mblogin.logout.side_effect = lambda callback: callback(True, None)
        result = self.run_command('logout')
        self.assertTrue(result.ok, result.error)
        self.assertEqual('logged_out', result.items[0].status)

    def test_not_logged_in(self):
        result = self.run_command('logout')
        self.assertEqual('not_logged_in', result.items[0].status)
        self.mblogin.logout.assert_not_called()

    def test_failed(self):
        self.oauth.is_authorized.return_value = True
        self.mblogin.logout.side_effect = lambda callback: callback(False, 'server error')
        item = self.run_command('logout').items[0]
        self.assertEqual('logout_failed', item.status)
        self.assertEqual('server error', item.data['error'])

    def test_timeout(self):
        self.oauth.is_authorized.return_value = True
        self.session._app.run_until_idle.return_value = False
        self.assertEqual('timeout', self.run_command('logout').items[0].status)

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

"""The MusicBrainz login sequence, without the GUI (picard.mblogin)."""

from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard import mblogin
from picard.const import METABRAINZ_OAUTH_SCOPES
from picard.oauth import OAuthInvalidStateError


class MBLoginTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.oauth = MagicMock()
        self.oauth.get_authorization_url.return_value = 'https://musicbrainz.org/oauth2/authorize?x'
        self.tagger.webservice = MagicMock(oauth_manager=self.oauth)
        patcher = patch('picard.mblogin.load_user_collections')
        self.load_user_collections = patcher.start()
        self.addCleanup(patcher.stop)
        self.callback = MagicMock()

    def _authorized(self, successful=True, error_msg=None):
        """Answer the request for the tokens: the exchange of a code, or the redirect of the browser."""
        if self.oauth.exchange_authorization_code.called:
            on_done = self.oauth.exchange_authorization_code.call_args.args[2]
        else:
            on_done = self.oauth.get_authorization_url.call_args.args[1]
        on_done(successful=successful, error_msg=error_msg)

    def _username_fetched(self, successful=True, error_msg=None):
        on_done = self.oauth.fetch_username.call_args.args[0]
        on_done(successful=successful, error_msg=error_msg)

    def test_start_login_gives_the_url_to_open(self):
        url = mblogin.start_login(self.callback)
        self.assertEqual('https://musicbrainz.org/oauth2/authorize?x', url)
        self.assertEqual(METABRAINZ_OAUTH_SCOPES, self.oauth.get_authorization_url.call_args.args[0])
        self.callback.assert_not_called()

    def test_finish_login_exchanges_the_code(self):
        mblogin.start_login(self.callback)
        mblogin.finish_login('the-code', self.callback)
        args = self.oauth.exchange_authorization_code.call_args.args
        self.assertEqual(('the-code', METABRAINZ_OAUTH_SCOPES), args[:2])

    def test_a_login_fetches_the_username_then_the_collections(self):
        mblogin.start_login(self.callback)
        mblogin.finish_login('the-code', self.callback)
        self._authorized()
        self.oauth.fetch_username.assert_called_once()
        self.callback.assert_not_called()
        self._username_fetched()
        self.load_user_collections.assert_called_once_with()
        self.callback.assert_called_once_with(True, None)

    def test_the_redirect_of_the_browser_completes_a_login_too(self):
        # With a redirect URI, the browser integration calls the state's callback itself.
        mblogin.start_login(self.callback)
        self._authorized()
        self._username_fetched()
        self.callback.assert_called_once_with(True, None)

    def test_a_refused_code_is_reported(self):
        mblogin.start_login(self.callback)
        mblogin.finish_login('bad-code', self.callback)
        self._authorized(successful=False, error_msg='invalid_grant')
        self.oauth.fetch_username.assert_not_called()
        self.load_user_collections.assert_not_called()
        self.callback.assert_called_once_with(False, 'invalid_grant')

    def test_a_failure_to_get_the_username_is_reported(self):
        mblogin.start_login(self.callback)
        mblogin.finish_login('the-code', self.callback)
        self._authorized()
        self._username_fetched(successful=False, error_msg='no user')
        self.load_user_collections.assert_not_called()
        self.callback.assert_called_once_with(False, 'no user')

    def test_logout_revokes_then_forgets_the_collections(self):
        mblogin.logout(self.callback)
        on_done = self.oauth.revoke_tokens.call_args.args[0]
        on_done(successful=True, error_msg=None)
        self.load_user_collections.assert_called_once_with()
        self.callback.assert_called_once_with(True, None)

    def test_a_failed_logout_is_reported(self):
        mblogin.logout(self.callback)
        on_done = self.oauth.revoke_tokens.call_args.args[0]
        on_done(successful=False, error_msg='offline')
        self.load_user_collections.assert_not_called()
        self.callback.assert_called_once_with(False, 'offline')


class ParseLoginRedirectTest(PicardTestCase):
    def test_a_code(self):
        for query in ('code=abc&state=xyz', 'state=xyz&code=abc'):
            with self.subTest(query=query):
                self.assertEqual(mblogin.LoginRedirect('xyz', 'abc'), mblogin.parse_login_redirect(query))

    def test_a_refusal(self):
        redirect = mblogin.parse_login_redirect('error=access_denied&error_description=No&state=xyz')
        self.assertEqual(mblogin.LoginRedirect('xyz', '', 'access_denied', 'No'), redirect)

    def test_not_a_redirect(self):
        for query in ('', 'abc', 'code=abc', 'state=xyz', 'foo=bar&state=xyz'):
            with self.subTest(query=query):
                self.assertIsNone(mblogin.parse_login_redirect(query))


class ReceiveLoginRedirectTest(PicardTestCase):
    """What the browser integration and the receiver do with the redirect of a login."""

    def setUp(self):
        super().setUp()
        self.oauth = MagicMock()
        self.tagger.webservice = MagicMock(oauth_manager=self.oauth)
        self.authorization_finished = MagicMock()
        self.oauth.verify_state.return_value = self.authorization_finished
        # What is to run on the main thread, run when the test says so.
        self.on_main = []
        patcher = patch('picard.mblogin.to_main', side_effect=lambda *call, **kwargs: self.on_main.append(call))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_on_main(self):
        for func, *args in self.on_main:
            func(*args)

    def test_a_code_is_exchanged_on_the_main_thread(self):
        status, page = mblogin.receive_login_redirect('code=abc&state=xyz')
        self.assertEqual(200, status)
        self.assertIn('Authentication successful', page)
        # The state is checked at once, the code exchanged on the main thread.
        self.oauth.verify_state.assert_called_once_with('xyz')
        self.oauth.exchange_authorization_code.assert_not_called()
        self.run_on_main()
        self.oauth.exchange_authorization_code.assert_called_once_with(
            'abc', METABRAINZ_OAUTH_SCOPES, self.authorization_finished
        )

    def test_a_refusal_is_reported(self):
        status, page = mblogin.receive_login_redirect('error=access_denied&error_description=No&state=xyz')
        self.assertEqual(200, status)
        self.assertIn('Authentication cancelled', page)
        self.run_on_main()
        self.authorization_finished.assert_called_once_with(successful=False, error_msg='No')
        self.oauth.exchange_authorization_code.assert_not_called()

    def test_an_unknown_state_is_an_error_page(self):
        # Not reported as successful: the login would not happen.
        self.oauth.verify_state.side_effect = OAuthInvalidStateError
        for query in ('code=abc&state=nope', 'error=access_denied&state=nope'):
            with self.subTest(query=query):
                status, page = mblogin.receive_login_redirect(query)
                self.assertEqual(400, status)
                self.assertIn('Authentication error', page)
        self.assertEqual([], self.on_main)

    def test_not_a_redirect_is_an_error_page(self):
        for query in ('', 'foo=bar', 'state=xyz', 'code=abc'):
            with self.subTest(query=query):
                self.assertEqual(400, mblogin.receive_login_redirect(query)[0])
        self.oauth.verify_state.assert_not_called()
        self.assertEqual([], self.on_main)

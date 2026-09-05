# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022, 2025 Laurent Monin
# Copyright (C) 2024 Philipp Wolfer
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

from test.picardtestcase import PicardTestCase

from picard.oauth import (
    OAuthManager,
    base64url_encode,
    redact_token,
    s256_encode,
)


class RedactTokenTest(PicardTestCase):
    def test_redacts_to_stable_partial_hash(self):
        token = 'super-secret-refresh-token'
        redacted = redact_token(token)
        # Never contains the raw token.
        self.assertNotIn(token, redacted)
        # Format is <token:xxxxxxxx> with an 8-char hex digest.
        self.assertRegex(redacted, r'^<token:[0-9a-f]{8}>$')
        # Stable: the same token always redacts to the same value.
        self.assertEqual(redacted, redact_token(token))

    def test_different_tokens_redact_differently(self):
        self.assertNotEqual(redact_token('token-a'), redact_token('token-b'))

    def test_empty_and_none_are_marked_absent(self):
        self.assertEqual(redact_token(None), '<none>')
        self.assertEqual(redact_token(''), '<none>')


class OAuthManagerTest(PicardTestCase):
    def test_query_data(self):
        params = {
            'a&b': 'a b',
            'c d': 'c&d',
            'e=f': 'e=f',
            '': '',
        }
        data = OAuthManager._query_data(params)
        self.assertEqual(data, "a%26b=a+b&c+d=c%26d&e%3Df=e%3Df")

    def test_s256_encode(self):
        code_verifier = b'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
        code_challenge = s256_encode(code_verifier)
        self.assertEqual(b'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM', code_challenge)

    def test_base64url_encode(self):
        b = bytes(
            [
                116,
                24,
                223,
                180,
                151,
                153,
                224,
                37,
                79,
                250,
                96,
                125,
                216,
                173,
                187,
                186,
                22,
                212,
                37,
                77,
                105,
                214,
                191,
                240,
                91,
                88,
                5,
                88,
                83,
                132,
                141,
                121,
            ]
        )
        encoded = base64url_encode(b)
        self.assertEqual(b'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk', encoded)


class RefreshAccessTokenTest(PicardTestCase):
    def _manager(self):
        self.set_config_values(
            persist={
                'oauth_refresh_token': 'old-refresh-token',
                'oauth_refresh_token_scopes': 'profile tag',
                'oauth_access_token': '',
                'oauth_access_token_expires': 0,
            }
        )
        manager = OAuthManager(webservice=None)
        # on_refresh_access_token_finished expects a pending refresh state
        manager._refreshing = True
        manager._refresh_callbacks = []
        return manager

    def test_refresh_persists_rotated_refresh_token(self):
        # The authorization server rotates the refresh token on every use.
        # Picard must persist the new token, otherwise the next refresh will
        # send an already-revoked token and the user gets logged out.
        manager = self._manager()
        data = {
            'access_token': 'new-access-token',
            'expires_in': 3600,
            'refresh_token': 'new-refresh-token',
        }
        manager.on_refresh_access_token_finished(data, http=None, error=None)
        self.assertEqual('new-refresh-token', manager.refresh_token)
        # Scopes must be preserved across a refresh.
        self.assertEqual('profile tag', manager.refresh_token_scopes)
        self.assertEqual('new-access-token', manager.access_token)

    def test_refresh_keeps_existing_token_when_none_returned(self):
        # A server that does not rotate refresh tokens omits refresh_token in
        # the response; the existing token must be kept.
        manager = self._manager()
        data = {
            'access_token': 'new-access-token',
            'expires_in': 3600,
        }
        manager.on_refresh_access_token_finished(data, http=None, error=None)
        self.assertEqual('old-refresh-token', manager.refresh_token)
        self.assertEqual('new-access-token', manager.access_token)

    def test_tokens_are_not_logged_in_cleartext(self):
        # Debug logs are frequently attached to bug reports; token values must
        # never appear there. Only their redacted partial hash may be logged.
        manager = self._manager()
        manager.webservice = MagicMock()
        with self.assertLogs('main', level='DEBUG') as cm:
            manager.set_refresh_token('secret-refresh-value', 'profile tag')
            manager.set_access_token('secret-access-value', 3600)
            manager._refreshing = False
            manager.refresh_access_token(callback=lambda **k: None)
        output = '\n'.join(cm.output)
        self.assertNotIn('secret-refresh-value', output)
        self.assertNotIn('secret-access-value', output)
        # The redacted marker should be present so the log stays useful.
        self.assertIn('<token:', output)

    def test_authorization_code_is_not_logged_in_cleartext(self):
        # The authorization code is a short-lived secret; it must not be logged.
        manager = self._manager()
        manager.webservice = MagicMock()
        manager._OAuthManager__code_verifier = 'test-verifier'
        with self.assertLogs('main', level='DEBUG') as cm:
            manager.exchange_authorization_code('secret-auth-code', 'profile tag', callback=lambda **k: None)
        output = '\n'.join(cm.output)
        self.assertNotIn('secret-auth-code', output)
        self.assertIn('<token:', output)


class AuthorizationUrlTest(PicardTestCase):
    def _manager(self):
        manager = OAuthManager(webservice=None)
        manager.redirect_uri = 'http://127.0.0.1:8000/auth'
        return manager

    def test_url_includes_ui_locales(self):
        with patch('picard.oauth.get_locale_bcp47', return_value='fr-FR'):
            url = self._manager().get_authorization_url('profile', callback=lambda **k: None)
        self.assertIn('ui_locales=fr-FR', url)

    def test_url_omits_ui_locales_when_unavailable(self):
        with patch('picard.oauth.get_locale_bcp47', return_value=''):
            url = self._manager().get_authorization_url('profile', callback=lambda **k: None)
        self.assertNotIn('ui_locales', url)

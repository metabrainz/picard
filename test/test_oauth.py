# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from unittest.mock import Mock

from test.picardtestcase import PicardTestCase

from picard.oauth import (
    OAuthManager,
    base64url_encode,
    s256_encode,
)


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
        b = bytes([116, 24, 223, 180, 151, 153, 224, 37, 79, 250, 96, 125, 216, 173,
            187, 186, 22, 212, 37, 77, 105, 214, 191, 240, 91, 88, 5, 88, 83,
            132, 141, 121])
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
        callback = Mock()
        manager.on_refresh_access_token_finished(callback, data, http=None, error=None)
        self.assertEqual('new-refresh-token', manager.refresh_token)
        # Scopes must be preserved across a refresh.
        self.assertEqual('profile tag', manager.refresh_token_scopes)
        self.assertEqual('new-access-token', manager.access_token)
        callback.assert_called_once_with(access_token='new-access-token')

    def test_refresh_keeps_existing_token_when_none_returned(self):
        # A server that does not rotate refresh tokens omits refresh_token in
        # the response; the existing token must be kept.
        manager = self._manager()
        data = {
            'access_token': 'new-access-token',
            'expires_in': 3600,
        }
        callback = Mock()
        manager.on_refresh_access_token_finished(callback, data, http=None, error=None)
        self.assertEqual('old-refresh-token', manager.refresh_token)
        self.assertEqual('new-access-token', manager.access_token)
        callback.assert_called_once_with(access_token='new-access-token')

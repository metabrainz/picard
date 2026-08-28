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


from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.oauth import (
    OAuthManager,
    _get_ui_locales,
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


class GetUiLocalesTest(PicardTestCase):
    def test_uses_configured_ui_language(self):
        self.set_config_values({'ui_language': 'fr'})
        self.assertEqual('fr', _get_ui_locales())

    def test_converts_posix_to_bcp47(self):
        self.set_config_values({'ui_language': 'pt_BR'})
        self.assertEqual('pt-BR', _get_ui_locales())

    def test_falls_back_to_system_locale(self):
        self.set_config_values({'ui_language': ''})
        with patch('picard.oauth.QLocale') as mock_qlocale:
            mock_qlocale.system.return_value.name.return_value = 'de_DE'
            self.assertEqual('de-DE', _get_ui_locales())

    def test_empty_for_c_locale(self):
        self.set_config_values({'ui_language': ''})
        with patch('picard.oauth.QLocale') as mock_qlocale:
            mock_qlocale.system.return_value.name.return_value = 'C'
            self.assertEqual('', _get_ui_locales())


class AuthorizationUrlTest(PicardTestCase):
    def _manager(self):
        manager = OAuthManager(webservice=None)
        manager.redirect_uri = 'http://127.0.0.1:8000/auth'
        return manager

    def test_url_includes_ui_locales(self):
        self.set_config_values({'ui_language': 'fr'})
        url = self._manager().get_authorization_url('profile', callback=lambda **k: None)
        self.assertIn('ui_locales=fr', url)

    def test_url_omits_ui_locales_when_unavailable(self):
        self.set_config_values({'ui_language': ''})
        with patch('picard.oauth.QLocale') as mock_qlocale:
            mock_qlocale.system.return_value.name.return_value = 'C'
            url = self._manager().get_authorization_url('profile', callback=lambda **k: None)
        self.assertNotIn('ui_locales', url)

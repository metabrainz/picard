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

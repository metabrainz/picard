# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020-2022, 2025 Laurent Monin
# Copyright (C) 2016 barami
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2020 Philipp Wolfer
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


from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.util import parse_amazon_url


class ParseAmazonUrlTest(PicardTestCase):
    @subtest_cases(
        "url,expected",
        [
            ('http://www.amazon.com/dp/020530902X', {'asin': '020530902X', 'host': 'amazon.com'}),
            ('http://ec1.amazon.co.jp/gp/product/020530902X', {'asin': '020530902X', 'host': 'ec1.amazon.co.jp'}),
            (
                'http://amazon.com/Dark-Side-Moon-Pink-Floyd/dp/B004ZN9RWK/ref=sr_1_1?s=music&ie=UTF8&qid=1372605047&sr=1-1&keywords=pink+floyd+dark+side+of+the+moon',
                {'asin': 'B004ZN9RWK', 'host': 'amazon.com'},
            ),
            ('https://www.amazon.co.jp/gp/product/B00005FMYV', {'asin': 'B00005FMYV', 'host': 'amazon.co.jp'}),
            # An ASIN starting with a letter other than B is not valid
            ('http://www.amazon.com/dp/A20530902X', None),
            # An ASIN must be upper case
            ('http://www.amazon.com/dp/020530902x', None),
            # Unknown url scheme
            ('httpsa://www.amazon.co.jp/gp/product/B00005FMYV', None),
        ],
    )
    def test_parse_amazon_url(self, url, expected):
        self.assertEqual(parse_amazon_url(url), expected)

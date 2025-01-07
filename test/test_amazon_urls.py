# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018, 2020-2022 Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from test.picardtestcase import PicardTestCase

from picard.util import parse_amazon_url


class ParseAmazonUrlTest(PicardTestCase):

    def test_1(self):
        url = 'http://www.amazon.com/dp/020530902X'
        expected = {'asin': '020530902X', 'host': 'amazon.com'}
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_2(self):
        url = 'http://ec1.amazon.co.jp/gp/product/020530902X'
        expected = {'asin': '020530902X', 'host': 'ec1.amazon.co.jp'}
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_3(self):
        url = 'http://amazon.com/Dark-Side-Moon-Pink-Floyd/dp/B004ZN9RWK/ref=sr_1_1?s=music&ie=UTF8&qid=1372605047&sr=1-1&keywords=pink+floyd+dark+side+of+the+moon'
        expected = {'asin': 'B004ZN9RWK', 'host': 'amazon.com'}
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_4(self):
        url = 'https://www.amazon.co.jp/gp/product/B00005FMYV'
        expected = {'asin': 'B00005FMYV', 'host': 'amazon.co.jp'}
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_incorrect_asin_1(self):
        url = 'http://www.amazon.com/dp/A20530902X'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_incorrect_asin_2(self):
        url = 'http://www.amazon.com/dp/020530902x'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_incorrect_url_scheme(self):
        url = 'httpsa://www.amazon.co.jp/gp/product/B00005FMYV'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

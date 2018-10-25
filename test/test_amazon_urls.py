# -*- coding: utf-8 -*-

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
        #incorrect ASIN
        url = 'http://www.amazon.com/dp/A20530902X'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_5(self):
        #incorrect ASIN
        url = 'http://www.amazon.com/dp/020530902x'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_6(self):
        url = 'https://www.amazon.co.jp/gp/product/B00005FMYV'
        expected = {'asin': 'B00005FMYV', 'host': 'amazon.co.jp'}
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

    def test_7(self):
        #incorrect url scheme
        url = 'httpsa://www.amazon.co.jp/gp/product/B00005FMYV'
        expected = None
        r = parse_amazon_url(url)
        self.assertEqual(r, expected)

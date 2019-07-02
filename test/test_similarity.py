# -*- coding: utf-8 -*-

from test.picardtestcase import PicardTestCase

from picard.similarity import (
    similarity,
    similarity2,
)


class SimilarityTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(similarity("K!", "K!"), 1.0)
        self.assertEqual(similarity("BBB", "AAA"), 0.0)
        self.assertAlmostEqual(similarity("ABC", "ABB"), 0.7, 1)


class Similarity2Test(PicardTestCase):
    def test_1(self):
        a = b = "a b c"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_2(self):
        a = "a b c"
        b = "A,B•C"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_3(self):
        a = "a b c"
        b = ",A, B •C•"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_4(self):
        a = "a b c"
        b = "c a b"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_5(self):
        a = "a b c"
        b = "a b d"
        self.assertAlmostEqual(similarity2(a, b), 0.6, 1)

    def test_6(self):
        a = "a b c"
        b = "a f d"
        self.assertAlmostEqual(similarity2(a, b), 0.3, 1)

    def test_7(self):
        a = "abc"
        b = "def"
        self.assertEqual(similarity2(a, b), 0.0)

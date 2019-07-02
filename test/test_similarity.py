# -*- coding: utf-8 -*-

from test.picardtestcase import PicardTestCase

from picard.similarity import similarity


class SimilarityTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(similarity("K!", "K!"), 1.0)
        self.assertEqual(similarity("BBB", "AAA"), 0.0)
        self.assertAlmostEqual(similarity("ABC", "ABB"), 0.7, 1)

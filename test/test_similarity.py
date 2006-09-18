import unittest
from picard.similarity import similarity, raw_similarity

class SimilarityTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(similarity("K!", "K!"), 1.0)
        self.failUnlessEqual(similarity("BBB", "AAA"), 0.0)
        self.failUnlessAlmostEqual(similarity("ABC", "ABB"), 0.7, 1)


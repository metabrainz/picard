import unittest
from picard.similarity import similarity

class SimilarityTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(similarity(u"K!", u"K!"), 1.0)
        self.failUnlessEqual(similarity(u"BBB", u"AAA"), 0.0)
        self.failUnlessAlmostEqual(similarity(u"ABC", u"ABB"), 0.7, 1)


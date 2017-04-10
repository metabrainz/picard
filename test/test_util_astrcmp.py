# -*- coding: utf-8 -*-

import os
import os.path
import unittest
from picard.util.astrcmp import astrcmp_py

try:
    from picard.util._astrcmp import astrcmp as astrcmp_c
except ImportError:
    astrcmp_c = "astrcmp_c() not available"


class AstrcmpBase(object):
    func = None

    def test_astrcmp(self):
        astrcmp = self.__class__.func
        # if C version of astrcmp() isn't available, astrcmp_c contains a
        # string, which is used as a reason for the skip
        if isinstance(astrcmp, str):
            raise unittest.SkipTest(astrcmp)
        self.assertAlmostEqual(0.0, astrcmp(u"", u""))
        self.assertAlmostEqual(0.0, astrcmp(u"a", u""))
        self.assertAlmostEqual(0.0, astrcmp(u"", u"a"))
        self.assertAlmostEqual(1.0, astrcmp(u"a", u"a"))
        self.assertAlmostEqual(0.0, astrcmp(u"a", u"b"))
        self.assertAlmostEqual(0.0, astrcmp(u"ab", u"ba"))
        self.assertAlmostEqual(0.7083333333333333, astrcmp(u"The Great Gig in the Sky", u"Great Gig In The sky"))


class AstrcmpCTest(AstrcmpBase, unittest.TestCase):
    func = astrcmp_c


class AstrcmpPyTest(AstrcmpBase, unittest.TestCase):
    func = astrcmp_py

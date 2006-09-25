# -*- coding: utf-8 -*-

import os.path
import unittest
from picard import util


class UnaccentTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(util.unaccent(u"Lukáš"), u"Lukas")
        self.failUnlessEqual(util.unaccent(u"Björk"), u"Bjork")
        self.failUnlessEqual(util.unaccent(u"Trentemøller"), u"Trentemoller")
        self.failUnlessEqual(util.unaccent(u"小室哲哉"), u"小室哲哉")

    def test_incorrect(self):
        self.failIfEqual(util.unaccent(u"Björk"), u"Björk")
        self.failIfEqual(util.unaccent(u"小室哲哉"), u"Tetsuya Komuro")


class ReplaceNonAsciiTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(util.replace_non_ascii(u"Lukáš"), u"Luk__")
        self.failUnlessEqual(util.replace_non_ascii(u"Björk"), u"Bj_rk")
        self.failUnlessEqual(util.replace_non_ascii(u"Trentemøller"), u"Trentem_ller")
        self.failUnlessEqual(util.replace_non_ascii(u"小室哲哉"), u"____")

    def test_incorrect(self):
        self.failIfEqual(util.replace_non_ascii(u"Lukáš"), u"Lukáš")
        self.failIfEqual(util.replace_non_ascii(u"Lukáš"), u"Luk____")


class ReplaceWin32IncompatTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(util.replace_win32_incompat("c:\\test\\te\"st2"),
                             "c__test_te_st2")

    def test_incorrect(self):
        self.failIfEqual(util.replace_win32_incompat("c:\\test\\te\"st2"),
                             "c:\\test\\te\"st2")


class SanitizeDateTest(unittest.TestCase):

    def test_correct(self):
        self.failUnlessEqual(util.sanitize_date("2006--"), "2006")
        self.failUnlessEqual(util.sanitize_date("2006--02"), "2006")
        self.failUnlessEqual(util.sanitize_date("2006   "), "2006")
        self.failUnlessEqual(util.sanitize_date("2006 02"), "")
        self.failUnlessEqual(util.sanitize_date("2006.02"), "")
        self.failUnlessEqual(util.sanitize_date("2006-02"), "2006-02")

    def test_incorrect(self):
        self.failIfEqual(util.sanitize_date("2006--02"), "2006-02")
        self.failIfEqual(util.sanitize_date("2006.03.02"), "2006-03-02")

class ShortFilenameTest(unittest.TestCase):

    def test_short(self):
        fn = util.make_short_filename("/home/me/", os.path.join("a1234567890", "b1234567890"), 255)
        self.failUnlessEqual(fn, os.path.join("a1234567890", "b1234567890"))

    def test_long(self):
        fn = util.make_short_filename("/home/me/", os.path.join("a1234567890", "b1234567890"), 20)
        self.failUnlessEqual(fn, os.path.join("a123456", "b1"))

    def test_long_2(self):
        fn = util.make_short_filename("/home/me/", os.path.join("a1234567890", "b1234567890"), 22)
        self.failUnlessEqual(fn, os.path.join("a12345678", "b1"))

    def test_too_long(self):
        self.failUnlessRaises(IOError, util.make_short_filename, "/home/me/", os.path.join("a1234567890", "b1234567890"), 10)


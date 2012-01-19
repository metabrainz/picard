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
        self.failUnlessEqual(util.unaccent(u"Ænima"), u"AEnima")
        self.failUnlessEqual(util.unaccent(u"ænima"), u"aenima")

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
        self.failUnlessEqual(util.replace_win32_incompat("c:\\test\\te\"st/2"),
                             "c_\\test\\te_st/2")
        self.failUnlessEqual(util.replace_win32_incompat("A\"*:<>?|b"),
                             "A_______b")

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

    def test_whitespace(self):
        fn = util.make_short_filename("/home/me/", os.path.join("a1234567890   ", "  b1234567890  "), 22)
        self.failUnlessEqual(fn, os.path.join("a12345678", "b1"))


class TranslateArtistTest(unittest.TestCase):

    def test_latin(self):
        self.failUnlessEqual(u"Jean Michel Jarre", util.translate_from_sortname(u"Jean Michel Jarre", u"Jarre, Jean Michel"))
        self.failIfEqual(u"Jarre, Jean Michel", util.translate_from_sortname(u"Jean Michel Jarre", u"Jarre, Jean Michel"))

    def test_kanji(self):
        self.failUnlessEqual(u"Tetsuya Komuro", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))
        self.failIfEqual(u"Komuro, Tetsuya", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))
        self.failIfEqual(u"小室哲哉", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))

    def test_kanji2(self):
        self.failUnlessEqual(u"Ayumi Hamasaki & Keiko", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))
        self.failIfEqual(u"浜崎あゆみ & KEIKO", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))
        self.failIfEqual(u"Hamasaki, Ayumi & Keiko", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))

    def test_cyrillic(self):
        self.failUnlessEqual(U"Pyotr Ilyich Tchaikovsky", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))
        self.failIfEqual(u"Tchaikovsky, Pyotr Ilyich", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))
        self.failIfEqual(u"Пётр Ильич Чайковский", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))

		
class FormatTimeTest(unittest.TestCase):

	def test(self):
		self.failUnlessEqual("?:??", util.format_time(0))
		self.failUnlessEqual("3:00", util.format_time(179750))
		self.failUnlessEqual("3:00", util.format_time(179500))
		self.failUnlessEqual("2:59", util.format_time(179499))
		

class LoadReleaseTypeScoresTest(unittest.TestCase):

    def test_valid(self):
        release_type_score_config = "Album 1.0 Single 0.5 EP 0.5 Compilation 0.5 Soundtrack 0.5 Spokenword 0.5 Interview 0.2 Audiobook 0.0 Live 0.5 Remix 0.4 Other 0.0"
        release_type_scores = util.load_release_type_scores(release_type_score_config)
        self.assertEqual(1.0, release_type_scores["Album"])
        self.assertEqual(0.5, release_type_scores["Single"])
        self.assertEqual(0.2, release_type_scores["Interview"])
        self.assertEqual(0.0, release_type_scores["Audiobook"])
        self.assertEqual(0.4, release_type_scores["Remix"])

    def test_invalid(self):
        release_type_score_config = "Album 1.0 Other"
        release_type_scores = util.load_release_type_scores(release_type_score_config)
        self.assertEqual(1.0, release_type_scores["Album"])
        self.assertEqual(0.0, release_type_scores["Other"])


class SaveReleaseTypeScoresTest(unittest.TestCase):

    def test(self):
        expected = "Album 1.00 Single 0.50 Other 0.00"
        scores = {"Album": 1.0, "Single": 0.5, "Other": 0.0}
        saved_scores = util.save_release_type_scores(scores)
        self.assertTrue("Album 1.00" in saved_scores)
        self.assertTrue("Single 0.50" in saved_scores)
        self.assertTrue("Other 0.00" in saved_scores)
        self.assertEqual(6, len(saved_scores.split()))


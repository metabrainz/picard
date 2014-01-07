# -*- coding: utf-8 -*-

import os.path
import unittest
from picard import util


class UnaccentTest(unittest.TestCase):

    def test_correct(self):
        self.assertEqual(util.unaccent(u"Lukáš"), u"Lukas")
        self.assertEqual(util.unaccent(u"Björk"), u"Bjork")
        self.assertEqual(util.unaccent(u"Trentemøller"), u"Trentemoller")
        self.assertEqual(util.unaccent(u"小室哲哉"), u"小室哲哉")
        self.assertEqual(util.unaccent(u"Ænima"), u"AEnima")
        self.assertEqual(util.unaccent(u"ænima"), u"aenima")

    def test_incorrect(self):
        self.assertNotEqual(util.unaccent(u"Björk"), u"Björk")
        self.assertNotEqual(util.unaccent(u"小室哲哉"), u"Tetsuya Komuro")


class ReplaceNonAsciiTest(unittest.TestCase):

    def test_correct(self):
        self.assertEqual(util.replace_non_ascii(u"Lukáš"), u"Luk__")
        self.assertEqual(util.replace_non_ascii(u"Björk"), u"Bj_rk")
        self.assertEqual(util.replace_non_ascii(u"Trentemøller"), u"Trentem_ller")
        self.assertEqual(util.replace_non_ascii(u"小室哲哉"), u"____")

    def test_incorrect(self):
        self.assertNotEqual(util.replace_non_ascii(u"Lukáš"), u"Lukáš")
        self.assertNotEqual(util.replace_non_ascii(u"Lukáš"), u"Luk____")


class ReplaceWin32IncompatTest(unittest.TestCase):

    def test_correct(self):
        self.assertEqual(util.replace_win32_incompat("c:\\test\\te\"st/2"),
                             "c_\\test\\te_st/2")
        self.assertEqual(util.replace_win32_incompat("A\"*:<>?|b"),
                             "A_______b")

    def test_incorrect(self):
        self.assertNotEqual(util.replace_win32_incompat("c:\\test\\te\"st2"),
                             "c:\\test\\te\"st2")


class SanitizeDateTest(unittest.TestCase):

    def test_correct(self):
        self.assertEqual(util.sanitize_date("2006--"), "2006")
        self.assertEqual(util.sanitize_date("2006--02"), "2006")
        self.assertEqual(util.sanitize_date("2006   "), "2006")
        self.assertEqual(util.sanitize_date("2006 02"), "")
        self.assertEqual(util.sanitize_date("2006.02"), "")
        self.assertEqual(util.sanitize_date("2006-02"), "2006-02")

    def test_incorrect(self):
        self.assertNotEqual(util.sanitize_date("2006--02"), "2006-02")
        self.assertNotEqual(util.sanitize_date("2006.03.02"), "2006-03-02")


class TranslateArtistTest(unittest.TestCase):

    def test_latin(self):
        self.assertEqual(u"Jean Michel Jarre", util.translate_from_sortname(u"Jean Michel Jarre", u"Jarre, Jean Michel"))
        self.assertNotEqual(u"Jarre, Jean Michel", util.translate_from_sortname(u"Jean Michel Jarre", u"Jarre, Jean Michel"))

    def test_kanji(self):
        self.assertEqual(u"Tetsuya Komuro", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))
        self.assertNotEqual(u"Komuro, Tetsuya", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))
        self.assertNotEqual(u"小室哲哉", util.translate_from_sortname(u"小室哲哉", u"Komuro, Tetsuya"))

    def test_kanji2(self):
        self.assertEqual(u"Ayumi Hamasaki & Keiko", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))
        self.assertNotEqual(u"浜崎あゆみ & KEIKO", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))
        self.assertNotEqual(u"Hamasaki, Ayumi & Keiko", util.translate_from_sortname(u"浜崎あゆみ & KEIKO", u"Hamasaki, Ayumi & Keiko"))

    def test_cyrillic(self):
        self.assertEqual(U"Pyotr Ilyich Tchaikovsky", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))
        self.assertNotEqual(u"Tchaikovsky, Pyotr Ilyich", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))
        self.assertNotEqual(u"Пётр Ильич Чайковский", util.translate_from_sortname(u"Пётр Ильич Чайковский", u"Tchaikovsky, Pyotr Ilyich"))


class FormatTimeTest(unittest.TestCase):

    def test(self):
        self.assertEqual("?:??", util.format_time(0))
        self.assertEqual("3:00", util.format_time(179750))
        self.assertEqual("3:00", util.format_time(179500))
        self.assertEqual("2:59", util.format_time(179499))


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


class HiddenPathTest(unittest.TestCase):

    def test(self):
        self.assertEqual(util.is_hidden_path('/a/.b/c.mp3'), True)
        self.assertEqual(util.is_hidden_path('/a/b/c.mp3'), False)
        self.assertEqual(util.is_hidden_path('/a/.b/.c.mp3'), True)
        self.assertEqual(util.is_hidden_path('/a/b/.c.mp3'), True)
        self.assertEqual(util.is_hidden_path('c.mp3'), False)
        self.assertEqual(util.is_hidden_path('.c.mp3'), True)
        self.assertEqual(util.is_hidden_path('/a/./c.mp3'), False)
        self.assertEqual(util.is_hidden_path('/a/./.c.mp3'), True)
        self.assertEqual(util.is_hidden_path('/a/../c.mp3'), False)
        self.assertEqual(util.is_hidden_path('/a/../.c.mp3'), True)

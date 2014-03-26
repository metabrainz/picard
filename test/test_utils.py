# -*- coding: utf-8 -*-

import os.path
import unittest
from picard import util


class ReplaceWin32IncompatTest(unittest.TestCase):

    def test_correct(self):
        self.assertEqual(util.replace_win32_incompat("c:\\test\\te\"st/2"),
                             "c-\\test\\te'st/2")
        self.assertEqual(util.replace_win32_incompat("A\"*:<>?|: b"),
                             "A'_-{}__ - b")

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

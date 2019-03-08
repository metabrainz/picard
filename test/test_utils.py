# -*- coding: utf-8 -*-

import builtins
import os.path
from test.picardtestcase import PicardTestCase
import unittest

from picard import util
from picard.const.sys import IS_WIN
from picard.util import imageinfo

# ensure _() is defined
if '_' not in builtins.__dict__:
    builtins.__dict__['_'] = lambda a: a


class ReplaceWin32IncompatTest(PicardTestCase):

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_correct_absolute_win32(self):
        self.assertEqual(util.replace_win32_incompat("c:\\test\\te\"st/2"),
                             "c:\\test\\te_st/2")
        self.assertEqual(util.replace_win32_incompat("c:\\test\\d:/2"),
                             "c:\\test\\d_/2")

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_correct_absolute_non_win32(self):
        self.assertEqual(util.replace_win32_incompat("/test/te\"st/2"),
                             "/test/te_st/2")
        self.assertEqual(util.replace_win32_incompat("/test/d:/2"),
                             "/test/d_/2")

    def test_correct_relative(self):
        self.assertEqual(util.replace_win32_incompat("A\"*:<>?|b"),
                             "A_______b")
        self.assertEqual(util.replace_win32_incompat("d:tes<t"),
                             "d_tes_t")

    def test_incorrect(self):
        self.assertNotEqual(util.replace_win32_incompat("c:\\test\\te\"st2"),
                             "c:\\test\\te\"st2")


class SanitizeDateTest(PicardTestCase):

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


class TranslateArtistTest(PicardTestCase):

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


class FormatTimeTest(PicardTestCase):

    def test(self):
        self.assertEqual("?:??", util.format_time(0))
        self.assertEqual("3:00", util.format_time(179750))
        self.assertEqual("3:00", util.format_time(179500))
        self.assertEqual("2:59", util.format_time(179499))
        self.assertEqual("59:59", util.format_time(3599499))
        self.assertEqual("1:00:00", util.format_time(3599500))
        self.assertEqual("1:02:59", util.format_time(3779499))


class HiddenFileTest(PicardTestCase):

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test(self):
        self.assertTrue(util.is_hidden('/a/b/.c.mp3'))
        self.assertTrue(util.is_hidden('/a/.b/.c.mp3'))
        self.assertFalse(util.is_hidden('/a/.b/c.mp3'))


class TagsTest(PicardTestCase):

    def test_display_tag_name(self):
        dtn = util.tags.display_tag_name
        self.assertEqual(dtn('tag'), 'tag')
        self.assertEqual(dtn('tag:desc'), 'tag [desc]')
        self.assertEqual(dtn('tag:'), 'tag')
        self.assertEqual(dtn('originalyear'), 'Original Year')
        self.assertEqual(dtn('originalyear:desc'), 'Original Year [desc]')
        self.assertEqual(dtn('~length'), 'Length')
        self.assertEqual(dtn('~lengthx'), '~lengthx')
        self.assertEqual(dtn(''), '')


class LinearCombinationTest(PicardTestCase):

    def test_0(self):
        parts = []
        self.assertEqual(util.linear_combination_of_weights(parts), 0.0)

    def test_1(self):
        parts = [(1.0, 1), (1.0, 1), (1.0, 1)]
        self.assertEqual(util.linear_combination_of_weights(parts), 1.0)

    def test_2(self):
        parts = [(0.0, 1), (0.0, 0), (1.0, 0)]
        self.assertEqual(util.linear_combination_of_weights(parts), 0.0)

    def test_3(self):
        parts = [(0.0, 1), (1.0, 1)]
        self.assertEqual(util.linear_combination_of_weights(parts), 0.5)

    def test_4(self):
        parts = [(0.5, 4), (1.0, 1)]
        self.assertEqual(util.linear_combination_of_weights(parts), 0.6)

    def test_5(self):
        parts = [(0.95, 100), (0.05, 399), (0.0, 1), (1.0, 0)]
        self.assertEqual(util.linear_combination_of_weights(parts), 0.2299)

    def test_6(self):
        parts = [(-0.5, 4)]
        self.assertRaises(ValueError, util.linear_combination_of_weights, parts)

    def test_7(self):
        parts = [(0.5, -4)]
        self.assertRaises(ValueError, util.linear_combination_of_weights, parts)

    def test_8(self):
        parts = [(1.5, 4)]
        self.assertRaises(ValueError, util.linear_combination_of_weights, parts)

    def test_9(self):
        parts = ((1.5, 4))
        self.assertRaises(TypeError, util.linear_combination_of_weights, parts)


class AlbumArtistFromPathTest(PicardTestCase):

    def test_album_artist_from_path(self):
        aafp = util.album_artist_from_path
        file_1 = r"/10cc/Original Soundtrack/02 I'm Not in Love.mp3"
        file_2 = r"/10cc - Original Soundtrack/02 I'm Not in Love.mp3"
        file_3 = r"/Original Soundtrack/02 I'm Not in Love.mp3"
        file_4 = r"/02 I'm Not in Love.mp3"
        self.assertEqual(aafp(file_1, '', ''), ('Original Soundtrack', '10cc'))
        self.assertEqual(aafp(file_2, '', ''), ('Original Soundtrack', '10cc'))
        self.assertEqual(aafp(file_3, '', ''), ('Original Soundtrack', ''))
        self.assertEqual(aafp(file_4, '', ''), ('', ''))
        self.assertEqual(aafp(file_1, 'album', ''), ('album', ''))
        self.assertEqual(aafp(file_2, 'album', ''), ('album', ''))
        self.assertEqual(aafp(file_3, 'album', ''), ('album', ''))
        self.assertEqual(aafp(file_4, 'album', ''), ('album', ''))
        self.assertEqual(aafp(file_1, '', 'artist'), ('Original Soundtrack', 'artist'))
        self.assertEqual(aafp(file_2, '', 'artist'), ('Original Soundtrack', 'artist'))
        self.assertEqual(aafp(file_3, '', 'artist'), ('Original Soundtrack', 'artist'))
        self.assertEqual(aafp(file_4, '', 'artist'), ('', 'artist'))
        self.assertEqual(aafp(file_1, 'album', 'artist'), ('album', 'artist'))
        self.assertEqual(aafp(file_2, 'album', 'artist'), ('album', 'artist'))
        self.assertEqual(aafp(file_3, 'album', 'artist'), ('album', 'artist'))
        self.assertEqual(aafp(file_4, 'album', 'artist'), ('album', 'artist'))


class ImageInfoTest(PicardTestCase):

    def test_gif(self):
        file = os.path.join('test', 'data', 'mb.gif')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                (140, 96, 'image/gif', '.gif', 5806)
            )

    def test_png(self):
        file = os.path.join('test', 'data', 'mb.png')

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                (140, 96, 'image/png', '.png', 11137)
            )

    def test_jpeg(self):
        file = os.path.join('test', 'data', 'mb.jpg',)

        with open(file, 'rb') as f:
            self.assertEqual(
                imageinfo.identify(f.read()),
                (140, 96, 'image/jpeg', '.jpg', 8550)
            )

    def test_not_enough_data(self):
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, "x")
        self.assertRaises(imageinfo.NotEnoughData, imageinfo.identify, "x")

    def test_invalid_data(self):
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, "x" * 20)
        self.assertRaises(imageinfo.UnrecognizedFormat,
                          imageinfo.identify, "x" * 20)

    def test_invalid_png_data(self):
        data = '\x89PNG\x0D\x0A\x1A\x0A' + "x" * 20
        self.assertRaises(imageinfo.IdentificationError,
                          imageinfo.identify, data)
        self.assertRaises(imageinfo.UnrecognizedFormat,
                          imageinfo.identify, data)

class CompareBarcodesTest(unittest.TestCase):

    def test_same(self):
        self.assertTrue(util.compare_barcodes('0727361379704', '0727361379704'))
        self.assertTrue(util.compare_barcodes('727361379704', '727361379704'))
        self.assertTrue(util.compare_barcodes('727361379704', '0727361379704'))
        self.assertTrue(util.compare_barcodes('0727361379704', '727361379704'))
        self.assertTrue(util.compare_barcodes(None, None))
        self.assertTrue(util.compare_barcodes('', ''))
        self.assertTrue(util.compare_barcodes(None, ''))
        self.assertTrue(util.compare_barcodes('', None))

    def test_not_same(self):
        self.assertFalse(util.compare_barcodes('0727361379704', '0727361379705'))
        self.assertFalse(util.compare_barcodes('727361379704', '1727361379704'))
        self.assertFalse(util.compare_barcodes('0727361379704', None))
        self.assertFalse(util.compare_barcodes(None, '0727361379704'))


class MbidValidateTest(unittest.TestCase):

    def test_ok(self):
        self.assertTrue(util.mbid_validate('2944824d-4c26-476f-a981-be849081942f'))
        self.assertTrue(util.mbid_validate('2944824D-4C26-476F-A981-be849081942f'))
        self.assertFalse(util.mbid_validate(''))
        self.assertFalse(util.mbid_validate('Z944824d-4c26-476f-a981-be849081942f'))
        self.assertFalse(util.mbid_validate('22944824d-4c26-476f-a981-be849081942f'))
        self.assertFalse(util.mbid_validate('2944824d-4c26-476f-a981-be849081942ff'))
        self.assertFalse(util.mbid_validate('2944824d-4c26.476f-a981-be849081942f'))

    def test_not_ok(self):
        self.assertRaises(TypeError, util.mbid_validate, 123)
        self.assertRaises(TypeError, util.mbid_validate, None)

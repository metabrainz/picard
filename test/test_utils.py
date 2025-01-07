# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2010 fatih
# Copyright (C) 2010-2011, 2014, 2018-2024 Philipp Wolfer
# Copyright (C) 2012, 2014, 2018 Wieland Hoffmann
# Copyright (C) 2013 Ionuț Ciocîrlan
# Copyright (C) 2013-2014, 2018-2024 Laurent Monin
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2016 Frederik “Freso” S. Olesen
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2017 Shen-Ta Hsieh
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021 Vladislav Karbovskii
# Copyright (C) 2024 Arnab Chakraborty
# Copyright (C) 2024 ShubhamBhut
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from collections import namedtuple
from collections.abc import Iterator
import os
import re
import subprocess  # nosec: B404
from tempfile import NamedTemporaryFile
import unittest
from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    get_test_data_path,
)

from picard import util
from picard.const import MUSICBRAINZ_SERVERS
from picard.const.sys import (
    IS_MACOS,
    IS_WIN,
)
from picard.i18n import gettext as _
from picard.util import (
    IgnoreUpdatesContext,
    album_artist_from_path,
    any_exception_isinstance,
    build_qurl,
    detect as charset_detect,
    detect_file_encoding,
    encoded_queryargs,
    extract_year_from_date,
    find_best_match,
    is_absolute_path,
    iter_exception_chain,
    iter_files_from_objects,
    iter_unique,
    limited_join,
    make_filename_from_title,
    normpath,
    pattern_as_regex,
    sort_by_similarity,
    system_supports_long_paths,
    titlecase,
    tracknum_and_title_from_filename,
    tracknum_from_filename,
    uniqify,
    wildcards_to_regex_pattern,
    win_prefix_longpath,
)


class ReplaceWin32IncompatTest(PicardTestCase):

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_correct_absolute_win32(self):
        self.assertEqual(util.replace_win32_incompat('c:\\test\\te"st/2'),
                             'c:\\test\\te_st/2')
        self.assertEqual(util.replace_win32_incompat('c:\\test\\d:/2'),
                             'c:\\test\\d_/2')

    @unittest.skipUnless(not IS_WIN, 'non-windows test')
    def test_correct_absolute_non_win32(self):
        self.assertEqual(util.replace_win32_incompat('/test/te"st/2'),
                             '/test/te_st/2')
        self.assertEqual(util.replace_win32_incompat('/test/d:/2'),
                             '/test/d_/2')

    def test_correct_relative(self):
        self.assertEqual(util.replace_win32_incompat('A"*:<>?|b'),
                             'A_______b')
        self.assertEqual(util.replace_win32_incompat('d:tes<t'),
                             'd_tes_t')

    def test_incorrect(self):
        self.assertNotEqual(util.replace_win32_incompat('c:\\test\\te"st2'),
                             'c:\\test\\te"st2')

    def test_custom_replacement_char(self):
        self.assertEqual(util.replace_win32_incompat('A"*:<>?|b', repl='+'),
                             "A+++++++b")

    def test_custom_replacement_map(self):
        input = 'foo*:<>?|"'
        replacments = {
            '*': 'A',
            ':': 'B',
            '<': 'C',
            '>': 'D',
            '?': 'E',
            '|': 'F',
            '"': 'G',
        }
        replaced = util.replace_win32_incompat(input, replacements=replacments)
        self.assertEqual('fooABCDEFG', replaced)

    def test_partial_replacement_map(self):
        input = 'foo*:<>?|"'
        replacments = {
            '*': 'A',
            '<': 'C',
        }
        replaced = util.replace_win32_incompat(input, repl='-', replacements=replacments)
        self.assertEqual('fooA-C----', replaced)

    def test_empty_string_replacement_map(self):
        input = 'foo:bar'
        replacments = {
            ':': '',
        }
        replaced = util.replace_win32_incompat(input, replacements=replacments)
        self.assertEqual('foobar', replaced)


class MakeFilenameTest(PicardTestCase):
    def test_filename_from_title(self):
        self.assertEqual(make_filename_from_title(), _("No Title"))
        self.assertEqual(make_filename_from_title(""), _("No Title"))
        self.assertEqual(make_filename_from_title(" "), _("No Title"))
        self.assertEqual(make_filename_from_title(default="New Default"), "New Default")
        self.assertEqual(make_filename_from_title("", "New Default"), "New Default")
        self.assertEqual(make_filename_from_title("/"), "_")

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_filename_from_title_win32(self):
        self.assertEqual(make_filename_from_title("\\"), "_")
        self.assertEqual(make_filename_from_title(":"), "_")

    @unittest.skipUnless(not IS_WIN, "non-windows test")
    def test_filename_from_title_non_win32(self):
        self.assertEqual(make_filename_from_title(":"), ":")


class ExtractYearTest(PicardTestCase):
    def test_string(self):
        self.assertEqual(extract_year_from_date(""), None)
        self.assertEqual(extract_year_from_date(2020), None)
        self.assertEqual(extract_year_from_date("2020"), 2020)
        self.assertEqual(extract_year_from_date('2020-02-28'), 2020)
        self.assertEqual(extract_year_from_date('2015.02'), 2015)
        self.assertEqual(extract_year_from_date('2015; 2015'), None)
        self.assertEqual(extract_year_from_date('20190303201903032019030320190303'), None)
        # test for the format as supported by ID3 (https://id3.org/id3v2.4.0-structure): yyyy-MM-ddTHH:mm:ss
        self.assertEqual(extract_year_from_date('2020-07-21T13:00:00'), 2020)

    def test_mapping(self):
        self.assertEqual(extract_year_from_date({}), None)
        self.assertEqual(extract_year_from_date({'year': 'abc'}), None)
        self.assertEqual(extract_year_from_date({'year': '2020'}), 2020)
        self.assertEqual(extract_year_from_date({'year': 2020}), 2020)
        self.assertEqual(extract_year_from_date({'year': '2020-02-28'}), None)


class SanitizeDateTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(util.sanitize_date(""), "")
        self.assertEqual(util.sanitize_date("0"), "")
        self.assertEqual(util.sanitize_date("0000"), "")
        self.assertEqual(util.sanitize_date("2006"), "2006")
        self.assertEqual(util.sanitize_date("2006--"), "2006")
        self.assertEqual(util.sanitize_date("2006-00-02"), "2006-00-02")
        self.assertEqual(util.sanitize_date("2006   "), "2006")
        self.assertEqual(util.sanitize_date("2006 02"), "")
        self.assertEqual(util.sanitize_date("2006.02"), "")
        self.assertEqual(util.sanitize_date("2006-02"), "2006-02")
        self.assertEqual(util.sanitize_date("2006-02-00"), "2006-02")
        self.assertEqual(util.sanitize_date("2006-00-00"), "2006")
        self.assertEqual(util.sanitize_date("2006-02-23"), "2006-02-23")
        self.assertEqual(util.sanitize_date("2006-00-23"), "2006-00-23")
        self.assertEqual(util.sanitize_date("0000-00-23"), "0000-00-23")
        self.assertEqual(util.sanitize_date("0000-02"), "0000-02")
        self.assertEqual(util.sanitize_date("--23"), "0000-00-23")

    def test_incorrect(self):
        self.assertNotEqual(util.sanitize_date("2006--02"), "2006")
        self.assertNotEqual(util.sanitize_date("2006.03.02"), "2006-03-02")


class SanitizeFilenameTest(PicardTestCase):

    def test_replace_slashes(self):
        self.assertEqual(util.sanitize_filename("AC/DC"), "AC_DC")

    def test_custom_replacement(self):
        self.assertEqual(util.sanitize_filename("AC/DC", "|"), "AC|DC")

    def test_win_compat(self):
        self.assertEqual(util.sanitize_filename("AC\\/DC", win_compat=True), "AC__DC")

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_replace_backslashes(self):
        self.assertEqual(util.sanitize_filename("AC\\DC"), "AC_DC")

    @unittest.skipIf(IS_WIN, "non-windows test")
    def test_keep_backslashes(self):
        self.assertEqual(util.sanitize_filename("AC\\DC"), "AC\\DC")


class TranslateArtistTest(PicardTestCase):

    def test_latin(self):
        self.assertEqual("thename", util.translate_from_sortname("thename", "sort, name"))

    def test_kanji(self):
        self.assertEqual("Tetsuya Komuro", util.translate_from_sortname("小室哲哉", "Komuro, Tetsuya"))
        # see _reverse_sortname(), cases with 3 or 4 chunks
        self.assertEqual("c b a", util.translate_from_sortname("小室哲哉", "a, b, c"))
        self.assertEqual("b a, d c", util.translate_from_sortname("小室哲哉", "a, b, c, d"))

    def test_kanji2(self):
        self.assertEqual("Ayumi Hamasaki & Keiko", util.translate_from_sortname("浜崎あゆみ & KEIKO", "Hamasaki, Ayumi & Keiko"))

    def test_cyrillic(self):
        self.assertEqual("Pyotr Ilyich Tchaikovsky", util.translate_from_sortname("Пётр Ильич Чайковский", "Tchaikovsky, Pyotr Ilyich"))


class FormatTimeTest(PicardTestCase):

    def test(self):
        self.assertEqual("?:??", util.format_time(0))
        self.assertEqual("0:00", util.format_time(0, display_zero=True))
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

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_windows(self):
        from ctypes import windll
        with NamedTemporaryFile() as f:
            self.assertFalse(util.is_hidden(f.name), "%s expected not to be hidden" % f.name)
            windll.kernel32.SetFileAttributesW(f.name, 2)
            self.assertTrue(util.is_hidden(f.name), "%s expected to be hidden" % f.name)

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_macos(self):
        with NamedTemporaryFile() as f:
            self.assertFalse(util.is_hidden(f.name), "%s expected not to be hidden" % f.name)
            subprocess.run(('SetFile', '-a', 'V', f.name))  # nosec: B603
            self.assertTrue(util.is_hidden(f.name), "%s expected to be hidden" % f.name)


class TagsTest(PicardTestCase):

    def test_display_tag_name(self):
        dtn = util.tags.display_tag_name
        self.assertEqual(dtn('tag'), 'tag')
        self.assertEqual(dtn('tag:desc'), 'tag [desc]')
        self.assertEqual(dtn('tag:'), 'tag')
        self.assertEqual(dtn('tag:de:sc'), 'tag [de:sc]')
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
        aafp = album_artist_from_path
        file_1 = r"/10cc/Original Soundtrack/02 I'm Not in Love.mp3"
        file_2 = r"/10cc - Original Soundtrack/02 I'm Not in Love.mp3"
        file_3 = r"/Original Soundtrack/02 I'm Not in Love.mp3"
        file_4 = r"/02 I'm Not in Love.mp3"
        file_5 = r"/10cc - Original Soundtrack - bonus/02 I'm Not in Love.mp3"
        self.assertEqual(aafp(file_1, '', ''), ('Original Soundtrack', '10cc'))
        self.assertEqual(aafp(file_2, '', ''), ('Original Soundtrack', '10cc'))
        self.assertEqual(aafp(file_3, '', ''), ('Original Soundtrack', ''))
        self.assertEqual(aafp(file_4, '', ''), ('', ''))
        self.assertEqual(aafp(file_5, '', ''), ('Original Soundtrack - bonus', '10cc'))
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

    def test_path_no_dirs(self):
        for name in ('', 'x', '/', '\\', '///'):
            self.assertEqual(('', 'artist'), album_artist_from_path(name, '', 'artist'))

    def test_strip_disc_dir(self):
        self.assertEqual(
            ('albumy', 'artistx'),
            album_artist_from_path(r'/artistx/albumy/CD 1/file.flac', '', ''))
        self.assertEqual(
            ('albumy', 'artistx'),
            album_artist_from_path(r'/artistx/albumy/the DVD 23 B/file.flac', '', ''))
        self.assertEqual(
            ('albumy', 'artistx'),
            album_artist_from_path(r'/artistx/albumy/disc23/file.flac', '', ''))
        self.assertNotEqual(
            ('albumy', 'artistx'),
            album_artist_from_path(r'/artistx/albumy/disc/file.flac', '', ''))

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_remove_windows_drive(self):
        self.assertEqual(
            ('album1', None),
            album_artist_from_path(r'C:\album1\foo.mp3', None, None))
        self.assertEqual(
            ('album1', None),
            album_artist_from_path(r'\\myserver\myshare\album1\foo.mp3', None, None))


class IsAbsolutePathTest(PicardTestCase):

    @unittest.skipIf(IS_WIN, "POSIX test")
    def test_is_absolute(self):
        self.assertTrue(is_absolute_path('/foo/bar'))
        self.assertFalse(is_absolute_path('foo/bar'))
        self.assertFalse(is_absolute_path('./foo/bar'))
        self.assertFalse(is_absolute_path('../foo/bar'))

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_is_absolute_windows(self):
        self.assertTrue(is_absolute_path('D:/foo/bar'))
        self.assertTrue(is_absolute_path('D:\\foo\\bar'))
        self.assertFalse(is_absolute_path('\\foo\\bar'))
        self.assertFalse(is_absolute_path('/foo/bar'))
        self.assertFalse(is_absolute_path('foo/bar'))
        self.assertFalse(is_absolute_path('./foo/bar'))
        self.assertFalse(is_absolute_path('../foo/bar'))
        # Paths to Windows shares
        self.assertTrue(is_absolute_path('\\\\foo\\bar'))
        self.assertTrue(is_absolute_path('\\\\foo\\bar\\'))
        self.assertTrue(is_absolute_path('\\\\foo\\bar\\baz'))


class CompareBarcodesTest(PicardTestCase):

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


class MbidValidateTest(PicardTestCase):

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


SimMatchTest = namedtuple('SimMatchTest', 'similarity name')


class SortBySimilarity(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.test_values = [
            SimMatchTest(similarity=0.74, name='d'),
            SimMatchTest(similarity=0.61, name='a'),
            SimMatchTest(similarity=0.75, name='b'),
            SimMatchTest(similarity=0.75, name='c'),
        ]

    def test_sort_by_similarity(self):
        results = [result.name for result in sort_by_similarity(self.test_values)]
        self.assertEqual(results, ['b', 'c', 'd', 'a'])

    def test_findbestmatch(self):
        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match(self.test_values, no_match)

        self.assertEqual(best_match.result.name, 'b')
        self.assertEqual(best_match.similarity, 0.75)

    def test_findbestmatch_nomatch(self):
        self.test_values = []

        no_match = SimMatchTest(similarity=-1, name='no_match')
        best_match = find_best_match(self.test_values, no_match)

        self.assertEqual(best_match.result.name, 'no_match')
        self.assertEqual(best_match.similarity, -1)


class LimitedJoin(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.list = [str(x) for x in range(0, 10)]

    def test_1(self):
        expected = '0+1+...+8+9'
        result = limited_join(self.list, 5, '+', '...')
        self.assertEqual(result, expected)

    def test_2(self):
        expected = '0+1+2+3+4+5+6+7+8+9'
        result = limited_join(self.list, -1)
        self.assertEqual(result, expected)
        result = limited_join(self.list, len(self.list))
        self.assertEqual(result, expected)
        result = limited_join(self.list, len(self.list) + 1)
        self.assertEqual(result, expected)

    def test_3(self):
        expected = '0,1,2,3,…,6,7,8,9'
        result = limited_join(self.list, len(self.list) - 1, ',')
        self.assertEqual(result, expected)


class IterFilesFromObjectsTest(PicardTestCase):

    def test_iterate_only_unique(self):
        f1 = Mock()
        f2 = Mock()
        f3 = Mock()
        obj1 = Mock()
        obj1.iterfiles = Mock(return_value=[f1, f2])
        obj2 = Mock()
        obj2.iterfiles = Mock(return_value=[f2, f3])
        result = iter_files_from_objects([obj1, obj2])
        self.assertTrue(isinstance(result, Iterator))
        self.assertEqual([f1, f2, f3], list(result))


class IterUniqifyTest(PicardTestCase):

    def test_unique(self):
        items = [1, 2, 3, 2, 3, 4]
        result = uniqify(items)
        self.assertEqual([1, 2, 3, 4], result)


class IterUniqueTest(PicardTestCase):

    def test_unique(self):
        items = [1, 2, 3, 2, 3, 4]
        result = iter_unique(items)
        self.assertTrue(isinstance(result, Iterator))
        self.assertEqual([1, 2, 3, 4], list(result))


class TracknumFromFilenameTest(PicardTestCase):

    def test_returns_expected_tracknumber(self):
        tests = (
            (2, '2.mp3'),
            (2, '02.mp3'),
            (2, '002.mp3'),
            (None, 'Foo.mp3'),
            (1, 'Foo 0001.mp3'),
            (1, '1 song.mp3'),
            (99, '99 Foo.mp3'),
            (42, '42. Foo.mp3'),
            (None, '20000 Feet.mp3'),
            (242, 'track no 242.mp3'),
            (77, 'Track no. 77 .mp3'),
            (242, 'track-242.mp3'),
            (242, 'track nr 242.mp3'),
            (242, 'track_242.mp3'),
            (3, 'track003.mp3'),
            (40, 'Track40.mp3'),
            (None, 'UB40.mp3'),
            (1, 'artist song 2004 track01 xxxx.ogg'),
            (1, 'artist song 2004 track-no-01 xxxx.ogg'),
            (1, 'artist song 2004 track-no_01 xxxx.ogg'),
            (1, '01_foo.mp3'),
            (1, '01ābc.mp3'),
            (1, '01abc.mp3'),
            (11, "11 Linda Jones - Things I've Been Through 08.flac"),
            (1, "01 artist song [2004] (02).mp3"),
            (1, "01 artist song [04].mp3"),
            (7, "artist song [2004] [7].mp3"),
            # (7, "artist song [2004] (7).mp3"),
            (7, 'artist song [2004] [07].mp3'),
            (7, 'artist song [2004] (07).mp3'),
            (4, 'xx 01 artist song [04].mp3'),
            (None, 'artist song-(666) (01) xxx.ogg'),
            (None, 'song-70s 69 comment.mp3'),
            (13, "2_13 foo.mp3"),
            (13, "02-13 foo.mp3"),
            (None, '1971.mp3'),
            (42, '1971 Track 42.mp3'),
            (None, "artist song [2004].mp3"),
            (None, '0.mp3'),
            (None, 'track00.mp3'),
            (None, 'song [2004] [1000].mp3'),
            (None, 'song 2015.mp3'),
            (None, '2015 song.mp3'),
            (None, '30,000 Pounds of Bananas.mp3'),
            (None, 'Dalas 1 PM.mp3'),
            (None, "Don't Stop the 80's.mp3"),
            (None, 'Symphony no. 5 in D minor.mp3'),
            (None, 'Song 2.mp3'),
            (None, '80s best of.mp3'),
            (None, 'best of 80s.mp3'),
            # (None, '99 Luftballons.mp3'),
            (7, '99 Luftballons Track 7.mp3'),
            (None, 'Margin 0.001.mp3'),
            (None, 'All the Small Things - blink‐182.mp3'),
            (None, '99.99 Foo.mp3'),
            (5, '٠٥ فاصله میان دو پرده.mp3'),
            (23, '23 foo.mp3'),
            (None, '²³ foo.mp3'),
        )
        for expected, filename in tests:
            tracknumber = tracknum_from_filename(filename)
            self.assertEqual(expected, tracknumber, filename)


class TracknumAndTitleFromFilenameTest(PicardTestCase):

    def test_returns_expected_tracknumber(self):
        tests = (
            ((None, 'Foo'), 'Foo.mp3'),
            (('1', 'Track 0001'), 'Track 0001.mp3'),
            (('42', 'Track-42'), 'Track-42.mp3'),
            (('99', 'Foo'), '99 Foo.mp3'),
            (('42', 'Foo'), '0000042 Foo.mp3'),
            (('2', 'Foo'), '0000002 Foo.mp3'),
            ((None, '20000 Feet'), '20000 Feet.mp3'),
            ((None, '20,000 Feet'), '20,000 Feet.mp3'),
            ((None, 'Venus (Original 12" version)'), 'Venus (Original 12" version).mp3'),
            ((None, 'Vanity 6'), 'Vanity 6.mp3'),
            ((None, 'UB40 - Red Red Wine'), 'UB40 - Red Red Wine.mp3'),
            ((None, 'Red Red Wine - UB40'), 'Red Red Wine - UB40.mp3'),
            ((None, 'Symphony no. 5 in D minor'), 'Symphony no. 5 in D minor.mp3'),
        )
        for expected, filename in tests:
            result = tracknum_and_title_from_filename(filename)
            self.assertEqual(expected, result)

    def test_namedtuple(self):
        result = tracknum_and_title_from_filename('0000002 Foo.mp3')
        self.assertEqual(result.tracknumber, '2')
        self.assertEqual(result.title, 'Foo')


class PatternAsRegexTest(PicardTestCase):

    def test_regex(self):
        regex = pattern_as_regex(r'/^foo.*/')
        self.assertEqual(r'^foo.*', regex.pattern)
        self.assertFalse(regex.flags & re.IGNORECASE)
        self.assertFalse(regex.flags & re.MULTILINE)

    def test_regex_flags(self):
        regex = pattern_as_regex(r'/^foo.*/', flags=re.MULTILINE | re.IGNORECASE)
        self.assertEqual(r'^foo.*', regex.pattern)
        self.assertTrue(regex.flags & re.IGNORECASE)
        self.assertTrue(regex.flags & re.MULTILINE)

    def test_regex_extra_flags(self):
        regex = pattern_as_regex(r'/^foo.*/im', flags=re.VERBOSE)
        self.assertEqual(r'^foo.*', regex.pattern)
        self.assertTrue(regex.flags & re.VERBOSE)
        self.assertTrue(regex.flags & re.IGNORECASE)
        self.assertTrue(regex.flags & re.MULTILINE)

    def test_regex_raises(self):
        with self.assertRaises(re.error):
            pattern_as_regex(r'/^foo(.*/')

    def test_wildcard(self):
        regex = pattern_as_regex(r'(foo?)\\*\?\*', allow_wildcards=True)
        self.assertEqual(r'^\(foo.\)\\.*\?\*$', regex.pattern)
        self.assertFalse(regex.flags & re.IGNORECASE)
        self.assertFalse(regex.flags & re.MULTILINE)

    def test_wildcard_flags(self):
        regex = pattern_as_regex(r'(foo)*', allow_wildcards=True, flags=re.MULTILINE | re.IGNORECASE)
        self.assertEqual(r'^\(foo\).*$', regex.pattern)
        self.assertTrue(regex.flags & re.IGNORECASE)
        self.assertTrue(regex.flags & re.MULTILINE)

    def test_string_match(self):
        regex = pattern_as_regex(r'(foo)*', allow_wildcards=False)
        self.assertEqual(r'\(foo\)\*', regex.pattern)
        self.assertFalse(regex.flags & re.IGNORECASE)
        self.assertFalse(regex.flags & re.MULTILINE)

    def test_string_match_flags(self):
        regex = pattern_as_regex(r'(foo)*', allow_wildcards=False, flags=re.MULTILINE | re.IGNORECASE)
        self.assertEqual(r'\(foo\)\*', regex.pattern)
        self.assertTrue(regex.flags & re.IGNORECASE)
        self.assertTrue(regex.flags & re.MULTILINE)


class WildcardsToRegexPatternTest(PicardTestCase):

    def test_wildcard_pattern(self):
        pattern = 'fo?o*'
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual('fo.o.*', regex)
        re.compile(regex)

    def test_escape(self):
        pattern = 'f\\?o\\*o?o*\\[o'
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual('f\\?o\\*o.o.*\\[o', regex)
        re.compile(regex)

    def test_character_group(self):
        pattern = '[abc*?xyz]]'
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual('[abc*?xyz]\\]', regex)
        re.compile(regex)

    def test_character_group_escape_square_brackets(self):
        pattern = '[a[b\\]c]'
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual('[a[b\\]c]', regex)
        re.compile(regex)

    def test_open_character_group(self):
        pattern = '[abc*?xyz['
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual('\\[abc.*.xyz\\[', regex)
        re.compile(regex)

    def test_special_chars(self):
        pattern = ']()\\^$|'
        regex = wildcards_to_regex_pattern(pattern)
        self.assertEqual(re.escape(pattern), regex)
        re.compile(regex)


class BuildQUrlTest(PicardTestCase):

    def test_path_and_querystring(self):
        query = {'foo': 'x', 'bar': 'y'}
        self.assertEqual('http://example.com/', build_qurl('example.com', path='/').toDisplayString())
        self.assertEqual('http://example.com/foo/bar', build_qurl('example.com', path='/foo/bar').toDisplayString())
        self.assertEqual('http://example.com/foo/bar?foo=x&bar=y', build_qurl('example.com', path='/foo/bar', queryargs=query).toDisplayString())
        self.assertEqual('http://example.com?foo=x&bar=y', build_qurl('example.com', queryargs=query).toDisplayString())

    def test_standard_ports(self):
        self.assertEqual('http://example.com', build_qurl('example.com').toDisplayString())
        self.assertEqual('http://example.com', build_qurl('example.com', port=80).toDisplayString())
        self.assertEqual('https://example.com', build_qurl('example.com', port=443).toDisplayString())

    def test_custom_port(self):
        self.assertEqual('http://example.com:8080', build_qurl('example.com', port=8080).toDisplayString())
        self.assertEqual('http://example.com:8080/', build_qurl('example.com', port=8080, path="/").toDisplayString())
        self.assertEqual('http://example.com:8080?foo=x', build_qurl('example.com', port=8080, queryargs={'foo': 'x'}).toDisplayString())

    def test_mb_server(self):
        for host in MUSICBRAINZ_SERVERS:
            expected = 'https://' + host
            self.assertEqual(expected, build_qurl(host, port=80).toDisplayString())
            self.assertEqual(expected, build_qurl(host, port=443).toDisplayString())
            self.assertEqual(expected, build_qurl(host, port=8080).toDisplayString())

    def test_encoded_queryargs(self):
        query = encoded_queryargs({'foo': ' %20&;', 'bar': '=%+?abc'})
        self.assertEqual('%20%2520%26%3B', query['foo'])
        self.assertEqual('%3D%25%2B%3Fabc', query['bar'])
        # spaces are decoded in displayed string
        expected = 'http://example.com?foo= %2520%26%3B&bar=%3D%25%2B%3Fabc'
        result = build_qurl('example.com', queryargs=query).toDisplayString()
        self.assertEqual(expected, result)


class NormpathTest(PicardTestCase):

    @unittest.skipIf(IS_WIN, "non-windows test")
    def test_normpath(self):
        self.assertEqual('/foo/bar', normpath('/foo//bar'))
        self.assertEqual('/bar', normpath('/foo/../bar'))

    @unittest.skipUnless(IS_WIN, "windows test")
    def test_normpath_windows(self):
        self.assertEqual(r'C:\Foo\Bar.baz', normpath('C:/Foo/Bar.baz'))
        self.assertEqual(r'C:\Bar.baz', normpath('C:/Foo/../Bar.baz'))

    @unittest.skipUnless(IS_WIN, "windows test")
    @patch.object(util, 'system_supports_long_paths')
    def test_normpath_windows_longpath(self, mock_system_supports_long_paths):
        mock_system_supports_long_paths.return_value = False
        path = rf'C:\foo\{252 * "a"}'
        self.assertEqual(path, normpath(path))
        path += 'a'
        self.assertEqual(rf'\\?\{path}', normpath(path))


class WinPrefixLongpathTest(PicardTestCase):

    def test_win_prefix_longpath_is_long(self):
        path = rf'C:\foo\{253 * "a"}'
        self.assertEqual(rf'\\?\{path}', win_prefix_longpath(path))

    def test_win_prefix_longpath_is_short(self):
        path = rf'C:\foo\{252 * "a"}'
        self.assertEqual(path, win_prefix_longpath(path))

    def test_win_prefix_longpath_unc(self):
        path = rf'\\server\{251 * "a"}'
        self.assertEqual(rf'\\?\UNC{path[1:]}', win_prefix_longpath(path))

    def test_win_prefix_longpath_already_prefixed(self):
        path = r'\\?\C:\foo'
        self.assertEqual(path, win_prefix_longpath(path))

    def test_win_prefix_longpath_already_prefixed_unc(self):
        path = r'\\?\server\someshare'
        self.assertEqual(path, win_prefix_longpath(path))


class SystemSupportsLongPathsTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        try:
            del system_supports_long_paths._supported
        except AttributeError:
            pass

    def test_system_supports_long_paths_returns_bool(self):
        result = system_supports_long_paths()
        self.assertTrue(isinstance(result, bool))

    @unittest.skipIf(IS_WIN, "non-windows test")
    def test_system_supports_long_paths(self):
        self.assertTrue(system_supports_long_paths())

    @unittest.skipUnless(IS_WIN, "windows test")
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_system_supports_long_paths_windows_unsupported(self, mock_query_value, mock_open_key):
        mock_query_value.return_value = [0]
        self.assertFalse(system_supports_long_paths())
        mock_open_key.assert_called_once()
        mock_query_value.assert_called_once()

    @unittest.skipUnless(IS_WIN, "windows test")
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_system_supports_long_paths_windows_supported(self, mock_query_value, mock_open_key):
        mock_query_value.return_value = [1]
        self.assertTrue(system_supports_long_paths())
        mock_open_key.assert_called_once()
        mock_query_value.assert_called_once()

    @unittest.skipUnless(IS_WIN, "windows test")
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_system_supports_long_paths_cache(self, mock_query_value, mock_open_key):
        mock_query_value.return_value = [1]
        self.assertTrue(system_supports_long_paths())
        self.assertTrue(system_supports_long_paths._supported)
        mock_query_value.return_value = [0]
        self.assertTrue(system_supports_long_paths())
        mock_open_key.assert_called_once()
        mock_query_value.assert_called_once()


class IterExceptionChainTest(PicardTestCase):

    def test_iter_exception_chain(self):
        e1 = Mock(name='e1')
        e2 = Mock(name='e2')
        e3 = Mock(name='e3')
        e4 = Mock(name='e4')
        e5 = Mock(name='e5')
        e1.__context__ = e2
        e2.__context__ = e3
        e2.__cause__ = e4
        e1.__cause__ = e5
        self.assertEqual([e1, e2, e3, e4, e5], list(iter_exception_chain(e1)))


class AnyExceptionIsinstanceTest(PicardTestCase):

    def test_any_exception_isinstance_itself(self):
        ex = RuntimeError()
        self.assertTrue(any_exception_isinstance(ex, RuntimeError))

    def test_any_exception_isinstance_context(self):
        ex = Mock()
        self.assertFalse(any_exception_isinstance(ex, RuntimeError))
        ex.__context__ = RuntimeError()
        self.assertTrue(any_exception_isinstance(ex, RuntimeError))

    def test_any_exception_isinstance_cause(self):
        ex = Mock()
        self.assertFalse(any_exception_isinstance(ex, RuntimeError))
        ex.__cause__ = RuntimeError()
        self.assertTrue(any_exception_isinstance(ex, RuntimeError))

    def test_any_exception_isinstance_nested(self):
        ex = Mock()
        self.assertFalse(any_exception_isinstance(ex, RuntimeError))
        ex.__cause__ = Mock()
        ex.__cause__.__context__ = RuntimeError()
        self.assertTrue(any_exception_isinstance(ex, RuntimeError))


class IgnoreUpdatesContextTest(PicardTestCase):

    def test_enter_exit(self):
        context = IgnoreUpdatesContext()
        self.assertFalse(context)
        with context:
            self.assertTrue(context)
        self.assertFalse(context)

    def test_run_on_exit(self):
        on_exit = Mock()
        context = IgnoreUpdatesContext(on_exit=on_exit)
        with context:
            on_exit.assert_not_called()
        on_exit.assert_called_once_with()

    def test_run_on_exit_nested(self):
        on_exit = Mock()
        context = IgnoreUpdatesContext(on_exit=on_exit)
        with context:
            with context:
                on_exit.assert_not_called()
            self.assertEqual(len(on_exit.mock_calls), 1)
        self.assertEqual(len(on_exit.mock_calls), 2)

    def test_run_on_last_exit(self):
        on_last_exit = Mock()
        context = IgnoreUpdatesContext(on_last_exit=on_last_exit)
        with context:
            on_last_exit.assert_not_called()
        on_last_exit.assert_called_once_with()

    def test_run_on_last_exit_nested(self):
        on_last_exit = Mock()
        context = IgnoreUpdatesContext(on_last_exit=on_last_exit)
        with context:
            with context:
                on_last_exit.assert_not_called()
            on_last_exit.assert_not_called()
        on_last_exit.assert_called_once_with()

    def test_run_on_enter(self):
        on_enter = Mock()
        context = IgnoreUpdatesContext(on_enter=on_enter)
        with context:
            on_enter.assert_called()
        on_enter.assert_called_once_with()

    def test_run_on_enter_nested(self):
        on_enter = Mock()
        context = IgnoreUpdatesContext(on_enter=on_enter)
        with context:
            self.assertEqual(len(on_enter.mock_calls), 1)
            with context:
                self.assertEqual(len(on_enter.mock_calls), 2)

    def test_run_on_first_enter(self):
        on_first_enter = Mock()
        context = IgnoreUpdatesContext(on_first_enter=on_first_enter)
        with context:
            on_first_enter.assert_called()
        on_first_enter.assert_called_once_with()

    def test_run_on_first_enter_nested(self):
        on_first_enter = Mock()
        context = IgnoreUpdatesContext(on_first_enter=on_first_enter)
        with context:
            on_first_enter.assert_called_once_with()
            with context:
                on_first_enter.assert_called_once_with()

    def test_nested_with(self):
        context = IgnoreUpdatesContext()
        with context:
            with context:
                self.assertTrue(context)
            self.assertTrue(context)
        self.assertFalse(context)


class DetectUnicodeEncodingTest(PicardTestCase):

    @unittest.skipUnless(charset_detect, "test requires charset_normalizer or chardet package")
    def test_detect_file_encoding_bom(self):
        boms = {
            b'\xff\xfe': 'utf-16-le',
            b'\xfe\xff': 'utf-16-be',
            b'\xff\xfe\x00\x00': 'utf-32-le',
            b'\x00\x00\xfe\xff': 'utf-32-be',
            b'\xef\xbb\xbf': 'utf-8-sig',
            b'': 'utf-8',
            b'\00': 'utf-8',
            b'no BOM, only ASCII': 'utf-8',
        }
        for bom, expected_encoding in boms.items():
            try:
                f = NamedTemporaryFile(delete=False)
                f.write(bom)
                f.close()
                encoding = detect_file_encoding(f.name)
                self.assertEqual(expected_encoding, encoding,
                                 f'BOM {bom!r} detected as {encoding}, expected {expected_encoding}')
            finally:
                f.close()
                os.remove(f.name)

    def test_detect_file_encoding_eac_utf_16_le(self):
        expected_encoding = 'utf-16-le'
        file_path = get_test_data_path('eac-utf16le.log')
        self.assertEqual(expected_encoding, detect_file_encoding(file_path))

    def test_detect_file_encoding_eac_utf_32_le(self):
        expected_encoding = 'utf-32-le'
        file_path = get_test_data_path('eac-utf32le.log')
        self.assertEqual(expected_encoding, detect_file_encoding(file_path))

    @unittest.skipUnless(charset_detect, "test requires charset_normalizer or chardet package")
    def test_detect_file_encoding_eac_windows_1251(self):
        expected_encoding = 'windows-1251'
        file_path = get_test_data_path('eac-windows1251.log')
        self.assertEqual(expected_encoding, detect_file_encoding(file_path))


class TitlecaseTest(PicardTestCase):

    def test_titlecase(self):
        tests = (
            # empty string
            ('', ''),
            # simple cases
            ('hello world', 'Hello World'),
            ('Hello World', 'Hello World'),
            ('HELLO WORLD', 'HELLO WORLD'),
            # contractions and possessives
            ("children's music", "Children's Music"),
            ("CHILDREN'S MUSIC", "CHILDREN'S MUSIC"),
            ("don't stop", "Don't Stop"),
            # hyphenated words
            ('first-class ticket', 'First-Class Ticket'),
            ('FIRST-CLASS ticket', 'FIRST-CLASS Ticket'),
            # multiple spaces
            ('hello   world', 'Hello   World'),
            # punctuation
            ('hello, world!', 'Hello, World!'),
            ('hello... world', 'Hello... World'),
            # special characters
            ('über café', 'Über Café'),
            ('españa', 'España'),
            ('ñandu', 'Ñandu'),
            # single character words
            ('a b c', 'A B C'),
            # numbers
            ('2001 a space odyssey', '2001 A Space Odyssey'),
            # preserves existing capitalization after first letter
            ('MacDonald had a farm', 'MacDonald Had A Farm'),
            ('LaTeX document', 'LaTeX Document'),
            # mixed case
            ('mIxEd CaSe', 'MIxEd CaSe'),
            # unicode boundaries
            ('hello—world', 'Hello—World'),
            ('hello\u2014world', 'Hello\u2014World'),
            # preserves all caps
            ('IBM PC', 'IBM PC'),
            # single letter
            ('a', 'A'),
            ('A', 'A'),
        )
        for input, expected in tests:
            self.assertEqual(expected, titlecase(input))

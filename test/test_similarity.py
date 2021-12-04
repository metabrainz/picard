# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013, 2018-2020 Laurent Monin
# Copyright (C) 2018 Wieland Hoffmann
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


from test.picardtestcase import PicardTestCase

from picard.similarity import (
    similarity,
    similarity2,
)


class SimilarityTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(similarity("K!", "K!"), 1.0)
        self.assertEqual(similarity("BBB", "AAA"), 0.0)
        self.assertAlmostEqual(similarity("ABC", "ABB"), 0.7, 1)


class Similarity2Test(PicardTestCase):
    def test_full_match(self):
        a = b = "a b c"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_match_various_separators_1(self):
        a = "a b c"
        b = "A,B•C"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_match_various_separators_2(self):
        a = "a b c"
        b = ",A, B •C•"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_a_b_order(self):
        a = "a b c"
        b = "c a b"
        self.assertEqual(similarity2(a, b), 1.0)

    def test_a_similar_b_1(self):
        a = "a b c"
        b = "a b d"
        self.assertAlmostEqual(similarity2(a, b), 0.6, 1)

    def test_a_similar_b_2(self):
        a = "a b c"
        b = "a f d"
        self.assertAlmostEqual(similarity2(a, b), 0.3, 1)

    def test_a_b_totally_different(self):
        a = "abc"
        b = "def"
        self.assertEqual(similarity2(a, b), 0.0)

    def test_not_a(self):
        a = ""
        b = "def"
        self.assertEqual(similarity2(a, b), 0.0)

    def test_not_b(self):
        a = "abc"
        b = ""
        self.assertEqual(similarity2(a, b), 0.0)

    def test_not_a_and_not_b(self):
        a = ""
        b = ""
        self.assertEqual(similarity2(a, b), 0.0)

    def test_empty_lists(self):
        a = " "
        b = "  "
        self.assertEqual(similarity2(a, b), 0.0)

    def test_a_longer_than_b(self):
        a = "a b c d"
        b = "a d c"
        self.assertAlmostEqual(similarity2(a, b), 0.88, 1)

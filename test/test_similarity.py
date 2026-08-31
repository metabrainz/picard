# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2013, 2018-2022, 2025 Laurent Monin
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2021 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

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
    @subtest_cases(
        "a,b,expected",
        {
            'full match': ("a b c", "a b c", 1.0),
            'various separators': ("a b c", "A,B•C", 1.0),
            'various separators with padding': ("a b c", ",A, B •C•", 1.0),
            'same words in different order': ("a b c", "c a b", 1.0),
            'totally different': ("abc", "def", 0.0),
            'empty a': ("", "def", 0.0),
            'empty b': ("abc", "", 0.0),
            'both empty': ("", "", 0.0),
            'whitespace only': (" ", "  ", 0.0),
        },
    )
    def test_similarity2_exact(self, a, b, expected):
        self.assertEqual(similarity2(a, b), expected)

    @subtest_cases(
        "a,b,expected",
        {
            'one word differs': ("a b c", "a b d", 0.6),
            'two words differ': ("a b c", "a f d", 0.3),
            'a longer than b': ("a b c d", "a d c", 0.88),
        },
    )
    def test_similarity2_approximate(self, a, b, expected):
        self.assertAlmostEqual(similarity2(a, b), expected, 1)

# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020, 2025 Laurent Monin
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

from picard.util import union_sorted_lists


class UnionSortedListsTest(PicardTestCase):
    @subtest_cases(
        "list1,list2,expected",
        {
            'overlapping ints': ([1, 2, 3], [3, 4, 5, 6], [1, 2, 3, 4, 5, 6]),
            'interleaved ints': ([1, 3, 5, 7], [2, 4, 6, 8], [1, 2, 3, 4, 5, 6, 7, 8]),
            'string duplicates': (
                ['Back', 'Back', 'Front', 'Front, Side'],
                ['Front', 'Front', 'Front, Side'],
                ['Back', 'Back', 'Front', 'Front', 'Front, Side'],
            ),
            'identical lists': (
                ['Back', 'Back, Spine', 'Front', 'Front, Side'],
                ['Back', 'Back, Spine', 'Front', 'Front, Side'],
                ['Back', 'Back, Spine', 'Front', 'Front, Side'],
            ),
        },
    )
    def test_union_sorted_lists(self, list1, list2, expected):
        # The union of two sorted lists is commutative, so both argument
        # orders must produce the same result.
        self.assertEqual(expected, union_sorted_lists(list1, list2))
        self.assertEqual(expected, union_sorted_lists(list2, list1))

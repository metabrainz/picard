# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020 Laurent Monin
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

from picard.util import union_sorted_lists


class UnionSortedListsTest(PicardTestCase):

    def test_1(self):
        list1 = [1, 2, 3]
        list2 = [3, 4, 5, 6]
        expected = [1, 2, 3, 4, 5, 6]
        r = union_sorted_lists(list1, list2)
        self.assertEqual(r, expected)
        r = union_sorted_lists(list2, list1)
        self.assertEqual(r, expected)

    def test_2(self):
        list1 = [1, 3, 5, 7]
        list2 = [2, 4, 6, 8]
        expected = [1, 2, 3, 4, 5, 6, 7, 8]
        r = union_sorted_lists(list1, list2)
        self.assertEqual(r, expected)

    def test_3(self):
        list1 = ['Back', 'Back', 'Front', 'Front, Side']
        list2 = ['Front', 'Front', 'Front, Side']
        expected = ['Back', 'Back', 'Front', 'Front', 'Front, Side']
        r = union_sorted_lists(list1, list2)
        self.assertEqual(r, expected)

    def test_4(self):
        list1 = ['Back', 'Back, Spine', 'Front', 'Front, Side']
        list2 = ['Back', 'Back, Spine', 'Front', 'Front, Side']
        expected = ['Back', 'Back, Spine', 'Front', 'Front, Side']
        r = union_sorted_lists(list1, list2)
        self.assertEqual(r, expected)

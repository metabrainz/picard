# -*- coding: utf-8 -*-
from test.picardtestcase import PicardTestCase

from picard.util import union_sorted_lists


class UnionSortedListsTest(PicardTestCase):

    def test_1(self):
        list1 = [1, 2, 3]
        list2 = [3, 4, 5]
        expected = [1, 2, 3, 4, 5]
        r = union_sorted_lists(list1, list2)
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

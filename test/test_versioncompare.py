# -*- coding: utf-8 -*-
from test.picardtestcase import PicardTestCase

from picard.util import compare_version_tuples


class CompareVersionsTest(PicardTestCase):
    """Unit tests for compare_version_tuples() function."""

    def test_compare_version_01(self):
        a, b, r = (0, 0, 1, 'dev', 1), (0, 0, 1, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_02(self):
        a, b, r = (0, 1, 0, 'dev', 1), (0, 1, 0, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_03(self):
        a, b, r = (0, 1, 1, 'dev', 1), (0, 1, 1, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_04(self):
        a, b, r = (1, 0, 0, 'dev', 1), (1, 0, 0, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_05(self):
        a, b, r = (1, 0, 1, 'dev', 1), (1, 0, 1, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_06(self):
        a, b, r = (1, 1, 0, 'dev', 1), (1, 1, 0, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_07(self):
        a, b, r = (1, 1, 1, 'dev', 1), (1, 1, 1, 'dev', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_08(self):
        a, b, r = (0, 0, 1, 'dev', 2), (0, 0, 1, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_09(self):
        a, b, r = (0, 0, 2, 'dev', 1), (0, 0, 1, 'dev', 2), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_10(self):
        a, b, r = (0, 1, 0, 'dev', 1), (0, 0, 1, 'dev', 2), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_11(self):
        a, b, r = (1, 0, 0, 'dev', 1), (0, 1, 1, 'dev', 2), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_12(self):
        a, b, r = (0, 0, 1, 'dev', 1), (0, 0, 1, 'dev', 2), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_13(self):
        a, b, r = (0, 0, 1, 'dev', 2), (0, 0, 2, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_14(self):
        a, b, r = (0, 0, 1, 'dev', 2), (0, 1, 0, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_15(self):
        a, b, r = (0, 1, 1, 'dev', 2), (1, 0, 0, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_16(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 0, 1, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_17(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 0, 1, 'final', 1), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_18(self):
        a, b, r = (0, 0, 1, 'final', 1), (0, 0, 1, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_19(self):
        a, b, r = (0, 1, 0, 'final', 0), (0, 1, 0, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_20(self):
        a, b, r = (0, 1, 1, 'final', 0), (0, 1, 1, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_21(self):
        a, b, r = (1, 0, 0, 'final', 0), (1, 0, 0, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_22(self):
        a, b, r = (1, 0, 1, 'final', 0), (1, 0, 1, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_23(self):
        a, b, r = (1, 1, 0, 'final', 0), (1, 1, 0, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_24(self):
        a, b, r = (1, 1, 1, 'final', 0), (1, 1, 1, 'final', 0), 0
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_25(self):
        a, b, r = (0, 0, 2, 'final', 0), (0, 0, 1, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_26(self):
        a, b, r = (0, 1, 0, 'final', 0), (0, 0, 1, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_27(self):
        a, b, r = (1, 0, 0, 'final', 0), (0, 1, 1, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_28(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 0, 2, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_29(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 1, 0, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_30(self):
        a, b, r = (0, 1, 1, 'final', 0), (1, 0, 0, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_31(self):
        a, b, r = (0, 0, 1, 'dev', 1), (0, 0, 1, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_32(self):
        a, b, r = (0, 0, 2, 'dev', 1), (0, 0, 1, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_33(self):
        a, b, r = (0, 0, 2, 'dev', 1), (0, 1, 0, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_34(self):
        a, b, r = (0, 1, 1, 'dev', 1), (0, 1, 0, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_35(self):
        a, b, r = (0, 2, 0, 'dev', 1), (0, 1, 0, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_36(self):
        a, b, r = (0, 2, 0, 'dev', 1), (0, 1, 1, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_37(self):
        a, b, r = (0, 2, 0, 'dev', 1), (0, 2, 0, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_38(self):
        a, b, r = (0, 2, 1, 'dev', 1), (0, 2, 0, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_39(self):
        a, b, r = (0, 2, 1, 'dev', 1), (0, 2, 1, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_40(self):
        a, b, r = (1, 0, 0, 'dev', 1), (0, 1, 0, 'final', 0), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_41(self):
        a, b, r = (1, 0, 0, 'dev', 1), (1, 0, 0, 'final', 0), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_42(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 0, 1, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_43(self):
        a, b, r = (0, 0, 1, 'final', 0), (0, 0, 2, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_44(self):
        a, b, r = (0, 1, 0, 'final', 0), (0, 0, 2, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_45(self):
        a, b, r = (0, 1, 0, 'final', 0), (0, 1, 1, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_46(self):
        a, b, r = (0, 1, 0, 'final', 0), (0, 2, 0, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_47(self):
        a, b, r = (0, 1, 1, 'final', 0), (0, 2, 0, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_48(self):
        a, b, r = (0, 2, 0, 'final', 0), (0, 2, 0, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_49(self):
        a, b, r = (0, 2, 0, 'final', 0), (0, 2, 1, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_50(self):
        a, b, r = (0, 2, 1, 'final', 0), (0, 2, 1, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_51(self):
        a, b, r = (0, 1, 0, 'final', 0), (1, 0, 0, 'dev', 1), 1
        self.assertEqual(compare_version_tuples(a, b), r)

    def test_compare_version_52(self):
        a, b, r = (1, 0, 0, 'final', 0), (1, 0, 0, 'dev', 1), -1
        self.assertEqual(compare_version_tuples(a, b), r)

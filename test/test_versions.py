# -*- coding: utf-8 -*-
import unittest

from test.picardtestcase import PicardTestCase

from picard import (
    VersionError,
    api_versions,
    api_versions_tuple,
    version_from_string,
    version_to_string,
)


class VersionsTest(PicardTestCase):

    def test_version_conv_1(self):
        l, s = (0, 0, 1, 'dev', 1), '0.0.1.dev1'
        r = '0.0.1.dev1'
        self.assertEqual(version_to_string(l), s)
        self.assertEqual(l, version_from_string(s))
        self.assertEqual(l, version_from_string(r))

    def test_version_conv_2(self):
        l, s = (1, 1, 0, 'final', 0), '1.1.0.final0'
        r = '1.1.0.final0'
        self.assertEqual(version_to_string(l), s)
        self.assertEqual(l, version_from_string(s))
        self.assertEqual(l, version_from_string(r))

    def test_version_conv_3(self):
        l, s = (1, 1, 0, 'dev', 0), '1.1.0.dev0'
        r = '1.1.0.dev0'
        self.assertEqual(version_to_string(l), s)
        self.assertEqual(l, version_from_string(s))
        self.assertEqual(l, version_from_string(r))

    def test_version_conv_4(self):
        l, s = (1, 0, 2, 'final', 0), '1.0.2'
        self.assertEqual(version_to_string(l, short=True), s)
        self.assertEqual(l, version_from_string(s))

    def test_version_conv_5(self):
        l, s = (999, 999, 999, 'dev', 999), '999.999.999.dev999'
        r = '999.999.999dev999'
        self.assertEqual(version_to_string(l), s)
        self.assertEqual(l, version_from_string(s))
        self.assertEqual(l, version_from_string(r))

    def test_version_conv_6(self):
        l = (1, 0, 2, 'xx', 0)
        self.assertRaises(VersionError, version_to_string, (l))

    def test_version_conv_7(self):
        l, s = (1, 1, 0, 'final', 0), '1.1'
        self.assertEqual(version_to_string(l, short=True), s)

    def test_version_conv_8(self):
        l, s = (1, 1, 1, 'final', 0), '1.1.1'
        self.assertEqual(version_to_string(l, short=True), s)

    def test_version_conv_9(self):
        l, s = (1, 1, 0, 'final', 1), '1.1'
        self.assertEqual(version_to_string(l, short=True), s)

    def test_version_conv_10(self):
        l, s = (1, 1, 0, 'dev', 0), '1.1.0.dev0'
        self.assertEqual(version_to_string(l, short=True), s)

    def test_version_conv_11(self):
        l, s = ('1', '1', '0', 'dev', '0'), '1.1.0.dev0'
        self.assertEqual(version_to_string(l), s)

    def test_version_conv_12(self):
        l, s = (1, 1, 0, 'dev', 0), '1_1_0_dev_0'
        self.assertEqual(l, version_from_string(s))

    def test_version_conv_13(self):
        l, s = (1, 1, 0, 'dev', 0), 'anything_28_1_1_0_dev_0'
        self.assertEqual(l, version_from_string(s))

    def test_version_conv_14(self):
        l = 'anything_28x_1_0_dev_0'
        self.assertRaises(VersionError, version_to_string, (l))

    def test_version_conv_15(self):
        l, s = (1, 1, 0, 'final', 0), 'anything_28_1_1_0'
        self.assertEqual(l, version_from_string(s))

    def test_version_conv_16(self):
        self.assertRaises(VersionError, version_from_string, '1.1.0dev')

    def test_version_conv_17(self):
        self.assertRaises(VersionError, version_from_string, '1.1.0devx')

    def test_version_conv_18(self):
        l, s = (1, 1, 0, 'final', 0), '1.1'
        self.assertEqual(version_to_string(l, short=True), s)
        self.assertEqual(l, version_from_string(s))

    def test_version_conv_19(self):
        self.assertRaises(VersionError, version_from_string, '123')

    def test_version_conv_20(self):
        self.assertRaises(VersionError, version_from_string, '123.')

    @unittest.skipUnless(len(api_versions) > 1, "api_versions do not have enough elements")
    def test_api_versions_1(self):
        """Check api versions format and order (from oldest to newest)"""

        for i in range(len(api_versions) - 1):
            a = version_from_string(api_versions[i])
            b = version_from_string(api_versions[i+1])
            self.assertLess(a, b)

    @unittest.skipUnless(len(api_versions_tuple) > 1, "api_versions_tuple do not have enough elements")
    def test_api_versions_tuple_1(self):
        """Check api versions format and order (from oldest to newest)"""

        for i in range(len(api_versions_tuple) - 1):
            a = api_versions_tuple[i]
            b = api_versions_tuple[i+1]
            self.assertLess(a, b)

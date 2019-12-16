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

    def test_version_conversion(self):
        versions =  (
            ((1, 1, 0, 'final', 0), '1.1.0.final0'),
            ((0, 0, 1, 'dev', 1), '0.0.1.dev1'),
            ((1, 1, 0, 'dev', 0), '1.1.0.dev0'),
            ((999, 999, 999, 'dev', 999), '999.999.999.dev999'),
            ((1, 1, 2, 'alpha', 2), '1.1.2.alpha2'),
            ((1, 1, 2, 'beta', 2), '1.1.2.beta2'),
            ((1, 1, 2, 'rc', 2), '1.1.2.rc2'),
        )
        for l, s in versions:
            self.assertEqual(version_to_string(l), s)
            self.assertEqual(l, version_from_string(s))

    def test_version_conversion_short(self):
        versions =  (
            ((1, 1, 0, 'final', 0), '1.1'),
            ((1, 1, 1, 'final', 0), '1.1.1'),
            ((0, 0, 1, 'dev', 1), '0.0.1.dev1'),
            ((1, 1, 0, 'dev', 0), '1.1.0.dev0'),
            ((1, 1, 2, 'alpha', 2), '1.1.2a2'),
            ((1, 1, 2, 'beta', 2), '1.1.2b2'),
            ((1, 1, 2, 'rc', 2), '1.1.2rc2'),
        )
        for l, s in versions:
            self.assertEqual(version_to_string(l, short=True), s)
            self.assertEqual(l, version_from_string(s))

    def test_version_to_string_invalid_identifier(self):
        l = (1, 0, 2, 'xx', 0)
        self.assertRaises(VersionError, version_to_string, (l))

    def test_version_from_string_underscores(self):
        l, s = (1, 1, 0, 'dev', 0), '1_1_0_dev_0'
        self.assertEqual(l, version_from_string(s))

    def test_version_from_string_prefixed(self):
        l, s = (1, 1, 0, 'dev', 0), 'anything_28_1_1_0_dev_0'
        self.assertEqual(l, version_from_string(s))

    def test_version_from_string_invalid(self):
        l = 'anything_28x_1_0_dev_0'
        self.assertRaises(VersionError, version_to_string, (l))

    def test_version_from_string_prefixed_final(self):
        l, s = (1, 1, 0, 'final', 0), 'anything_28_1_1_0'
        self.assertEqual(l, version_from_string(s))

    def test_from_string_invalid_identifier(self):
        self.assertRaises(VersionError, version_from_string, '1.1.0dev')
        self.assertRaises(VersionError, version_from_string, '1.1.0devx')

    def test_version_from_string_invalid_partial(self):
        self.assertRaises(VersionError, version_from_string, '123')
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

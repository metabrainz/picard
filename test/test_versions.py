# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013-2014, 2018-2020 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2020 Philipp Wolfer
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


import unittest

from test.picardtestcase import PicardTestCase

from picard import (
    api_versions,
    api_versions_tuple,
)
from picard.version import (
    Version,
    VersionError,
)


class VersionsTest(PicardTestCase):

    def test_version_conversion(self):
        versions = (
            (Version(1, 1, 0, 'final', 0), '1.1.0.final0'),
            (Version(0, 0, 1, 'dev', 1), '0.0.1.dev1'),
            (Version(1, 1, 0, 'dev', 0), '1.1.0.dev0'),
            (Version(999, 999, 999, 'dev', 999), '999.999.999.dev999'),
            (Version(1, 1, 2, 'alpha', 2), '1.1.2.alpha2'),
            (Version(1, 1, 2, 'a', 2), '1.1.2.alpha2'),
            (Version(1, 1, 2, 'beta', 2), '1.1.2.beta2'),
            (Version(1, 1, 2, 'b', 2), '1.1.2.beta2'),
            (Version(1, 1, 2, 'rc', 2), '1.1.2.rc2'),
        )
        for v, s in versions:
            self.assertEqual(str(v), s)
            self.assertEqual(v, Version.from_string(s))

    def test_version_conversion_short(self):
        versions = (
            (Version(1, 1, 0, 'final', 0), '1.1'),
            (Version(1, 1, 1, 'final', 0), '1.1.1'),
            (Version(0, 0, 1, 'dev', 1), '0.0.1.dev1'),
            (Version(1, 1, 0, 'dev', 0), '1.1.0.dev0'),
            (Version(1, 1, 2, 'alpha', 2), '1.1.2a2'),
            (Version(1, 1, 2, 'a', 2), '1.1.2a2'),
            (Version(1, 1, 2, 'beta', 2), '1.1.2b2'),
            (Version(1, 1, 2, 'b', 2), '1.1.2b2'),
            (Version(1, 1, 2, 'rc', 2), '1.1.2rc2'),
        )
        for v, s in versions:
            self.assertEqual(v.to_string(short=True), s)
            self.assertEqual(v, Version.from_string(s))

    def test_version_from_string_underscores(self):
        l, s = (1, 1, 0, 'dev', 0), '1_1_0_dev_0'
        self.assertEqual(l, Version.from_string(s))

    def test_version_from_string_prefixed_with_num(self):
        self.assertRaises(VersionError, Version.from_string, '8_1_1_0_dev_0')

    def test_version_from_string_suffixed_with_num(self):
        self.assertRaises(VersionError, Version.from_string, '1_1_0_dev_0_8')

    def test_version_from_string_prefixed_with_alpha(self):
        self.assertRaises(VersionError, Version.from_string, 'a_1_1_0_dev_0')

    def test_version_from_string_suffixed_with_alpha(self):
        self.assertRaises(VersionError, Version.from_string, '1_1_0_dev_0_a')

    def test_version_single_digit(self):
        l, s = (2, 0, 0, 'final', 0), '2'
        self.assertEqual(l, Version.from_string(s))
        self.assertEqual(l, Version(2))

    def test_from_string_invalid_identifier(self):
        self.assertRaises(VersionError, Version.from_string, '1.1.0dev')
        self.assertRaises(VersionError, Version.from_string, '1.1.0devx')

    def test_version_from_string_invalid_partial(self):
        self.assertRaises(VersionError, Version.from_string, '1dev')
        self.assertRaises(VersionError, Version.from_string, '1.0dev')
        self.assertRaises(VersionError, Version.from_string, '123.')

    @unittest.skipUnless(len(api_versions) > 1, "api_versions do not have enough elements")
    def test_api_versions_1(self):
        """Check api versions format and order (from oldest to newest)"""

        for i in range(len(api_versions) - 1):
            a = Version.from_string(api_versions[i])
            b = Version.from_string(api_versions[i+1])
            self.assertLess(a, b)

    @unittest.skipUnless(len(api_versions_tuple) > 1, "api_versions_tuple do not have enough elements")
    def test_api_versions_tuple_1(self):
        """Check api versions format and order (from oldest to newest)"""

        for i in range(len(api_versions_tuple) - 1):
            a = api_versions_tuple[i]
            b = api_versions_tuple[i+1]
            self.assertLess(a, b)

    def test_version_invalid_new(self):
        self.assertRaises(VersionError, Version, '1', 'a')
        self.assertRaises(VersionError, Version, None, 0)
        self.assertRaises(VersionError, Version, 1, 0, 0, 'final', None)
        self.assertRaises(VersionError, Version, 1, 0, 0, 'invalid', 0)

    def test_sortkey(self):
        self.assertEqual((2, 1, 3, 4, 2), Version(2, 1, 3, 'final', 2).sortkey)
        self.assertEqual((2, 0, 0, 1, 0), Version(2, 0, 0, 'a', 0).sortkey)
        self.assertEqual((2, 0, 0, 1, 0), Version(2, 0, 0, 'alpha', 0).sortkey)

    def test_lt(self):
        v1 = Version(2, 3, 0, 'dev', 1)
        v2 = Version(2, 3, 0, 'alpha', 1)
        self.assertLess(v1, v2)
        self.assertFalse(v2 < v2)

        v1 = Version(2, 3, 0, 'final', 1)
        v2 = Version(2, 10, 0, 'final', 1)
        self.assertLess(v1, v2)

    def test_le(self):
        v1 = Version(2, 3, 0, 'dev', 1)
        v2 = Version(2, 3, 0, 'alpha', 1)
        self.assertLessEqual(v1, v2)
        self.assertLessEqual(v2, v2)

    def test_gt(self):
        v1 = Version(2, 3, 0, 'alpha', 1)
        v2 = Version(2, 3, 0, 'dev', 1)
        self.assertGreater(v1, v2)
        self.assertFalse(v2 > v2)

    def test_ge(self):
        v1 = Version(2, 3, 0, 'alpha', 1)
        v2 = Version(2, 3, 0, 'dev', 1)
        self.assertGreaterEqual(v1, v2)
        self.assertGreaterEqual(v2, v2)

    def test_eq(self):
        v1 = Version(2, 3, 0, 'alpha', 1)
        v2 = Version(2, 3, 0, 'a', 1)
        v3 = Version(2, 3, 0, 'final', 1)
        self.assertEqual(v1, v1)
        self.assertEqual(v1, v2)
        self.assertFalse(v1 == v3)

    def test_ne(self):
        v1 = Version(2, 3, 0, 'alpha', 1)
        v2 = Version(2, 3, 0, 'a', 1)
        v3 = Version(2, 3, 0, 'final', 1)
        self.assertFalse(v1 != v1)
        self.assertFalse(v1 != v2)
        self.assertTrue(v1 != v3)

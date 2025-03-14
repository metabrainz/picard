# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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


from unittest import TestCase

from picard import PICARD_FANCY_VERSION_STR
from picard.util.versions import (
    _names,
    as_dict,
    as_string,
    version_name,
)


class UtilVersionsTest(TestCase):

    def test_version_name(self):
        self.assertEqual(version_name('version'), 'Picard')
        self.assertEqual(version_name('python-version'), 'Python')

    def test_as_dict(self):
        versions = as_dict()
        self.assertIsInstance(versions, dict)
        self.assertEqual(versions['version'], PICARD_FANCY_VERSION_STR)
        for name in _names:
            self.assertIn(name, versions)

    def test_as_string(self):
        versions = as_string()
        self.assertIsInstance(versions, str)
        self.assertTrue(versions.startswith(f'Picard {PICARD_FANCY_VERSION_STR}, Python '))
        for name in _names.values():
            self.assertIn(name, versions)

    def test_as_string_with_separator(self):
        versions = as_string(separator='/')
        self.assertIsInstance(versions, str)
        self.assertTrue(versions.startswith(f'Picard {PICARD_FANCY_VERSION_STR}/Python '))

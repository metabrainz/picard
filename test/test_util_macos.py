# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024 Laurent Monin
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
from unittest.mock import patch

from test.picardtestcase import PicardTestCase

from picard.const.sys import IS_MACOS
from picard.util.macos import (
    extend_root_volume_path,
    strip_root_volume_path,
)


def fake_os_scandir(path):
    raise OSError('failed os.scandir')


@unittest.skipUnless(IS_MACOS, "macOS test")
class UtilMacosExtendRootVolumeTest(PicardTestCase):

    def test_path_starts_with_volumes(self):
        path = '/Volumes/path'
        result = extend_root_volume_path(path)
        self.assertEqual(result, path)

    @patch('picard.util.macos._find_root_volume', lambda: '/Volumes/root_volume')
    def test_path_donot_starts_with_volumes_abs(self):
        path = '/test/path'
        result = extend_root_volume_path(path)
        self.assertEqual(result, '/Volumes/root_volume/test/path')

    @patch('picard.util.macos._find_root_volume', lambda: '/Volumes/root_volume')
    def test_path_donot_starts_with_volumes_rel(self):
        path = 'test/path'
        result = extend_root_volume_path(path)
        self.assertEqual(result, '/Volumes/root_volume/test/path')

    @patch('os.scandir', fake_os_scandir)
    def test_path_donot_starts_with_volumes_failed(self):
        path = '/test/path'
        with patch('picard.log.warning') as mock:
            result = extend_root_volume_path(path)
            self.assertEqual(result, path)
            self.assertTrue(mock.called)


@unittest.skipUnless(IS_MACOS, "macOS test")
class UtilMacosStripRootVolumeTest(PicardTestCase):

    def test_path_starts_not_with_volumes(self):
        path = '/Users/sandra'
        result = strip_root_volume_path(path)
        self.assertEqual(result, path)

    @patch('picard.util.macos._find_root_volume', lambda: '/Volumes/root_volume')
    def test_path_starts_not_with_root_volume(self):
        path = '/Volumes/other_volume/foo/bar'
        result = strip_root_volume_path(path)
        self.assertEqual(result, path)

    @patch('picard.util.macos._find_root_volume', lambda: '/Volumes/root_volume')
    def test_path_starts_with_root_volume(self):
        path = '/Volumes/root_volume/foo/bar'
        result = strip_root_volume_path(path)
        self.assertEqual(result, '/foo/bar')

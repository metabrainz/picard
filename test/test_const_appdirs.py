# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


import os.path
import unittest

from test.picardtestcase import PicardTestCase

from picard.const.appdirs import (
    cache_folder,
    config_folder,
    plugin_folder,
)
from picard.const.sys import (
    IS_LINUX,
    IS_MACOS,
    IS_WIN,
)


class AppPathsTest(PicardTestCase):
    def assert_home_path_equals(self, expected, actual):
        self.assertEqual(os.path.normpath(os.path.expanduser(expected)), actual)

    @unittest.skipUnless(IS_WIN, "Windows test")
    def test_config_folder_win(self):
        self.assert_home_path_equals('~/AppData/Local/MusicBrainz/Picard', config_folder())

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_config_folder_macos(self):
        self.assert_home_path_equals('~/Library/Preferences/MusicBrainz/Picard', config_folder())

    @unittest.skipUnless(IS_LINUX, "Linux test")
    def test_config_folder_linux(self):
        self.assert_home_path_equals('~/.config/MusicBrainz/Picard', config_folder())

    @unittest.skipUnless(IS_WIN, "Windows test")
    def test_cache_folder_win(self):
        self.assert_home_path_equals('~/AppData/Local/MusicBrainz/Picard/cache', cache_folder())

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_cache_folder_macos(self):
        self.assert_home_path_equals('~/Library/Caches/MusicBrainz/Picard', cache_folder())

    @unittest.skipUnless(IS_LINUX, "Linux test")
    def test_cache_folder_linux(self):
        self.assert_home_path_equals('~/.cache/MusicBrainz/Picard', cache_folder())

    @unittest.skipUnless(IS_WIN, "Windows test")
    def test_plugin_folder_win(self):
        self.assert_home_path_equals('~/AppData/Roaming/MusicBrainz/Picard/plugins3', plugin_folder())

    @unittest.skipUnless(IS_MACOS, "macOS test")
    def test_plugin_folder_macos(self):
        self.assert_home_path_equals('~/Library/Application Support/MusicBrainz/Picard/plugins3', plugin_folder())

    @unittest.skipUnless(IS_LINUX, "Linux test")
    def test_plugin_folder_linux(self):
        self.assert_home_path_equals('~/.local/share/MusicBrainz/Picard/plugins3', plugin_folder())

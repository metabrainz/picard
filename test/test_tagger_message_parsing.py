# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
# Copyright (C) 2022 Bob Swift
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

from picard.const.sys import IS_WIN
from picard.tagger import ParseItemsToLoad


class TestMessageParsing(PicardTestCase):
    def test(self):
        test_cases = {
            "test_case.mp3",
            "file:///home/picard/music/test.flac",
            "mbid://recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
            "https://musicbrainz.org/recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
            "http://musicbrainz.org/recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
        }

        result = ParseItemsToLoad(test_cases)
        self.assertSetEqual(result.files, {"test_case.mp3", "/home/picard/music/test.flac"}, "Files test")
        self.assertSetEqual(result.mbids, {"recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94"}, "MBIDs test")
        self.assertSetEqual(result.urls, {"recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
            "recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94"}, "URLs test")

    def test_bool_files_true(self):
        test_cases = {
            "test_case.mp3",
        }
        self.assertTrue(ParseItemsToLoad(test_cases))

    def test_bool_mbids_true(self):
        test_cases = {
            "mbid://recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
        }
        self.assertTrue(ParseItemsToLoad(test_cases))

    def test_bool_urls_true(self):
        test_cases = {
            "https://musicbrainz.org/recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
        }
        self.assertTrue(ParseItemsToLoad(test_cases))

    def test_bool_invalid_false(self):
        test_cases = {
            "mbd://recording/7cd3782d-86dc-4dd1-8d9b-e37f9cbe6b94",
        }
        self.assertFalse(ParseItemsToLoad(test_cases))

    def test_bool_empty_false(self):
        test_cases = {}
        self.assertFalse(ParseItemsToLoad(test_cases))

    def test_windows_file_with_drive(self):
        test_cases = {
            "C:\\test_case.mp3",
        }
        if IS_WIN:
            self.assertTrue(ParseItemsToLoad(test_cases))
        else:
            self.assertFalse(ParseItemsToLoad(test_cases))

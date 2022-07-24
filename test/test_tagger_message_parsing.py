# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2022 skelly37
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

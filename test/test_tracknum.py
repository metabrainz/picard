# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2013, 2018 Laurent Monin
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019 Philipp Wolfer
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

from picard.util import tracknum_from_filename


def parse(filename):
    return tracknum_from_filename(filename)


class TracknumTest(PicardTestCase):

    def test_matched_tracknum_01(self):
        self.assertEqual(parse('1.mp3'), 1)

    def test_matched_tracknum_02(self):
        self.assertEqual(parse('01.mp3'), 1)

    def test_matched_tracknum_03(self):
        self.assertEqual(parse('001.mp3'), 1)

    def test_matched_tracknum_04(self):
        self.assertEqual(parse('01 song.mp3'), 1)

    def test_matched_tracknum_05(self):
        self.assertEqual(parse('song 01.mp3'), 1)

    def test_matched_tracknum_06(self):
        self.assertEqual(parse('artist - song (01).mp3'), 1)

    def test_matched_tracknum_07(self):
        self.assertEqual(parse('artist - s 02 ong (01).mp3'), 1)

    def test_matched_tracknum_08(self):
        self.assertEqual(parse('artist song 2004 track01 xxxx.ogg'), 1)

    def test_matched_tracknum_09(self):
        self.assertEqual(parse('artist song 2004 track-no-01 xxxx.ogg'), 1)

    def test_matched_tracknum_10(self):
        self.assertEqual(parse('artist song 2004 track-no_01 xxxx.ogg'), 1)

    def test_matched_tracknum_11(self):
        self.assertEqual(parse('artist song-(666) (01) xxx.ogg'), 1)

    def test_matched_tracknum_12(self):
        self.assertEqual(parse('artist song [2004] [01].mp3'), 1)

    def test_matched_tracknum_13(self):
        self.assertEqual(parse('artist song [2004] (01).mp3'), 1)

    def test_matched_tracknum_14(self):
        self.assertEqual(parse('01 artist song [2004] (02).mp3'), 1)

    def test_matched_tracknum_15(self):
        self.assertEqual(parse('01 artist song [04].mp3'), 1)

    def test_matched_tracknum_16(self):
        self.assertEqual(parse('xx 01 artist song [04].mp3'), 1)

    def test_matched_tracknum_17(self):
        self.assertEqual(parse('song [2004] [1].mp3'), 1)

    def test_matched_tracknum_18(self):
        self.assertEqual(parse('song-70s 69 comment.mp3'), 69)

    def test_matched_tracknum_19(self):
        self.assertEqual(parse('01_foo.mp3'), 1)

    def test_matched_tracknum_20(self):
        self.assertEqual(parse('01ābc.mp3'), 1)

    def test_matched_tracknum_21(self):
        self.assertEqual(parse('01abc.mp3'), 1)

    def test_matched_tracknum_22(self):
        t = u"11 Linda Jones - Things I've Been Through 08.flac"
        self.assertEqual(parse(t), 11)

    def test_unmatched_tracknum_01(self):
        self.assertEqual(parse('0.mp3'), -1)

    def test_unmatched_tracknum_02(self):
        self.assertEqual(parse('track00.mp3'), -1)

    def test_unmatched_tracknum_03(self):
        self.assertEqual(parse('song.mp3'), -1)

    def test_unmatched_tracknum_04(self):
        self.assertEqual(parse('song [2004] [1000].mp3'), -1)

# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007 Lukáš Lalinský
# Copyright (C) 2013, 2018, 2020-2022 Laurent Monin
# Copyright (C) 2016 Christoph Reiter
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2019, 2021 Philipp Wolfer
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


from mutagen import id3

from test.picardtestcase import PicardTestCase

from picard.formats.id3 import Id3Encoding
from picard.formats.mutagenext import compatid3


class UpdateToV23Test(PicardTestCase):

    def test_keep_some_v24_tag(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TSOP(encoding=Id3Encoding.LATIN1, text=["foo"]))
        tags.add(id3.TSOA(encoding=Id3Encoding.LATIN1, text=["foo"]))
        tags.add(id3.TSOT(encoding=Id3Encoding.LATIN1, text=["foo"]))
        tags.update_to_v23()
        self.assertEqual(tags["TSOP"].text, ["foo"])
        self.assertEqual(tags["TSOA"].text, ["foo"])
        self.assertEqual(tags["TSOT"].text, ["foo"])

    def test_tdrc(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDRC(encoding=Id3Encoding.UTF16, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.assertEqual(tags["TYER"].text, ["2003"])
        self.assertEqual(tags["TDAT"].text, ["0504"])
        self.assertEqual(tags["TIME"].text, ["1203"])

    def test_tdor(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDOR(encoding=Id3Encoding.UTF16, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.assertEqual(tags["TORY"].text, ["2003"])

    def test_genre_from_v24_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=Id3Encoding.UTF16, text=["4", "Rock"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Disco", "Rock"])

    def test_genre_from_v24_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=Id3Encoding.UTF16, text=["RX", "3", "CR"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Remix", "Dance", "Cover"])

    def test_genre_from_v23_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=Id3Encoding.UTF16, text=["(4)Rock"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Disco", "Rock"])

    def test_genre_from_v23_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=Id3Encoding.UTF16, text=["(RX)(3)(CR)"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Remix", "Dance", "Cover"])

# -*- coding: utf-8 -*-

import unittest
from mutagen import id3
from picard.formats.mutagenext import compatid3

class UpdateToV23Test(unittest.TestCase):

    def test_multiple_text_values(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TALB(encoding=0, text=["123","abc"]))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TALB"].text, ["123/abc"])

    def test_encoding(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TALB(encoding=2, text="abc"))
        tags.add(id3.TIT2(encoding=3, text="abc"))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TALB"].encoding, 1)
        self.failUnlessEqual(tags["TIT2"].encoding, 1)

    def test_tdrc(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDRC(encoding=1, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TYER"].text, ["2003"])
        self.failUnlessEqual(tags["TDAT"].text, ["0504"])
        self.failUnlessEqual(tags["TIME"].text, ["1203"])

    def test_tdor(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDOR(encoding=1, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TORY"].text, ["2003"])

    def test_genre_from_v24_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["4","Rock"]))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TCON"].text, ["Disco/Rock"])

    def test_genre_from_v24_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["RX", "3", "CR"]))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TCON"].text, ["Remix/Dance/Cover"])

    def test_genre_from_v23_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["(4)Rock"]))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TCON"].text, ["Disco/Rock"])

    def test_genre_from_v23_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["(RX)(3)(CR)"]))
        tags.update_to_v23()
        self.failUnlessEqual(tags["TCON"].text, ["Remix/Dance/Cover"])


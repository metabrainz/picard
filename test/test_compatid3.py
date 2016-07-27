# -*- coding: utf-8 -*-

import unittest
from mutagen import id3
from picard.formats.mutagenext import compatid3
from picard.formats.id3 import id3text


class UpdateToV23Test(unittest.TestCase):

    def test_id3text(self):
        self.assertEqual(id3text(u"\u1234", 0), u"?")
        self.assertEqual(id3text(u"\u1234", 1), u"\u1234")
        self.assertEqual(id3text(u"\u1234", 2), u"\u1234")
        self.assertEqual(id3text(u"\u1234", 3), u"\u1234")

    def test_keep_some_v24_tag(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TSOP(encoding=0, text=["foo"]))
        tags.add(id3.TSOA(encoding=0, text=["foo"]))
        tags.add(id3.TSOT(encoding=0, text=["foo"]))
        tags.update_to_v23()
        self.assertEqual(tags["TSOP"].text, ["foo"])
        self.assertEqual(tags["TSOA"].text, ["foo"])
        self.assertEqual(tags["TSOT"].text, ["foo"])

    def test_tdrc(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDRC(encoding=1, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.assertEqual(tags["TYER"].text, ["2003"])
        self.assertEqual(tags["TDAT"].text, ["0504"])
        self.assertEqual(tags["TIME"].text, ["1203"])

    def test_tdor(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TDOR(encoding=1, text="2003-04-05 12:03"))
        tags.update_to_v23()
        self.assertEqual(tags["TORY"].text, ["2003"])

    def test_genre_from_v24_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["4", "Rock"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Disco", "Rock"])

    def test_genre_from_v24_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["RX", "3", "CR"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Remix", "Dance", "Cover"])

    def test_genre_from_v23_1(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["(4)Rock"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Disco", "Rock"])

    def test_genre_from_v23_2(self):
        tags = compatid3.CompatID3()
        tags.add(id3.TCON(encoding=1, text=["(RX)(3)(CR)"]))
        tags.update_to_v23()
        self.assertEqual(tags["TCON"].text, ["Remix", "Dance", "Cover"])

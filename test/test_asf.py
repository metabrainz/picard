# -*- coding: utf-8 -*-

import os
import shutil
import unittest
from picard.plugins.picardmutagen.mutagenext.asf import ASF, UnicodeAttribute
from tempfile import mkstemp


class ASFTest(unittest.TestCase):

    def setUp(self):
        self.filename = os.path.join("test", "data", "silence.wma")
        self.asf = ASF(self.filename)

    def test_write(self):
        fd, filename = mkstemp(suffix='.wma')
        os.close(fd)
        try:
            shutil.copy(self.filename, filename)
            wma = ASF(filename)
            wma.tags["WM/Composer"] = UnicodeAttribute("Test!")
            wma.save()
            wma = ASF(filename)
            self.failUnlessEqual(unicode(wma["WM/Composer"][0]), "Test!")
        finally:
            os.unlink(filename)

    def test_is_vbr(self):
        self.failUnlessEqual(bool(self.asf["IsVBR"][0]), True)

    def test_title(self):
        self.failUnlessEqual(unicode(self.asf["Title"][0]), "Enjoy the Silence!")


class TASFInfo(unittest.TestCase):

    def setUp(self):
        self.file = ASF(os.path.join("test", "data", "silence.wma"))

#    def test_length(self):
#        self.failUnlessAlmostEqual(self.file.info.length, 0.03, 2)

    def test_bitrate(self):
        self.failUnlessEqual(self.file.info.bitrate, 64)

    def test_sample_rate(self):
        self.failUnlessEqual(self.file.info.sample_rate, 44100)

    def test_channels(self):
        self.failUnlessEqual(self.file.info.channels, 2)


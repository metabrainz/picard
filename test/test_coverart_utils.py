#!/usr/bin/env python
# coding: utf-8
import os.path
import shutil
import tempfile
import unittest

from picard.coverart.utils import translate_caa_type
from picard.i18n import setup_gettext


class CaaTypeTranslationTest(unittest.TestCase):
    def setUp(self):
        # we are using temporary locales for tests
        self.tmp_path = tempfile.mkdtemp()
        self.localedir = os.path.join(self.tmp_path, 'locale')
        self.addCleanup(shutil.rmtree, self.tmp_path)
        setup_gettext(self.localedir, "C")

    def test_translating_unknown_types_returns_input(self):
        testtype = "ThisIsAMadeUpCoverArtTypeName"
        self.assertEqual(translate_caa_type(testtype), testtype)

#!/usr/bin/env python
# coding: utf-8
import os.path

from test.picardtestcase import PicardTestCase

from picard.coverart.utils import translate_caa_type
from picard.i18n import setup_gettext


class CaaTypeTranslationTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # we are using temporary locales for tests
        self.tmp_path = self.mktmpdir()
        self.localedir = os.path.join(self.tmp_path, 'locale')
        setup_gettext(self.localedir, "C")

    def test_translating_unknown_types_returns_input(self):
        testtype = "ThisIsAMadeUpCoverArtTypeName"
        self.assertEqual(translate_caa_type(testtype), testtype)

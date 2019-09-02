# -*- coding: utf-8 -*-
from test.picardtestcase import PicardTestCase

from picard.formats import mutagenext


class MutagenExtTest(PicardTestCase):

    def test_delall_ci(self):
        tags = {
            'TAGNAME:ABC': 'a',
            'tagname:abc': 'a',
            'TagName:Abc': 'a',
            'OtherTag': 'a'
        }
        mutagenext.delall_ci(tags, 'tagname:Abc')
        self.assertEqual({'OtherTag': 'a'}, tags)

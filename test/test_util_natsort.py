# -*- coding: utf-8 -*-
import unittest

from test.picardtestcase import PicardTestCase

from picard.util import natsort


class NatsortTest(PicardTestCase):
    def test_natkey(self):
        self.assertTrue(natsort.natkey('foo1bar') < natsort.natkey('foo02bar'))
        self.assertTrue(natsort.natkey('foo1bar') == natsort.natkey('foo01bar'))
        self.assertTrue(natsort.natkey('foo (100)') < natsort.natkey('foo (00200)'))

    def test_natsorted(self):
        l = ['foo11', 'foo0012', 'foo02', 'foo0', 'foo1', 'foo10', 'foo9']
        ls = natsort.natsorted(l)
        self.assertEqual(
            ['foo0', 'foo1', 'foo02', 'foo9', 'foo10', 'foo11', 'foo0012'], ls)

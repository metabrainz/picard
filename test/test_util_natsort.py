# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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

from locale import strxfrm

from test.picardtestcase import PicardTestCase

from picard.util import natsort


class NatsortTest(PicardTestCase):
    def test_natkey(self):
        self.assertTrue(natsort.natkey('foo1bar') < natsort.natkey('foo02bar'))
        self.assertTrue(natsort.natkey('foo1bar') == natsort.natkey('foo01bar'))
        self.assertTrue(natsort.natkey('foo (100)') < natsort.natkey('foo (00200)'))

    def test_natsorted(self):
        unsorted_list = ['foo11', 'foo0012', 'foo02', 'foo0', 'foo1', 'foo10', 'foo9']
        expected = ['foo0', 'foo1', 'foo02', 'foo9', 'foo10', 'foo11', 'foo0012']
        sorted_list = natsort.natsorted(unsorted_list)
        self.assertEqual(expected, sorted_list)

    def test_natkey_handles_null_char(self):
        self.assertEqual(natsort.natkey('foo\0'), natsort.natkey('foo'))

    def test_natkey_handles_numeric_chars(self):
        self.assertEqual(
            natsort.natkey('foo0123456789|²³|٠١٢٣٤٥٦٧٨٩|๐๑๒๓๔๕๖๗๘๙|𝟜𝟚bar'),
            [strxfrm('foo'), 123456789, strxfrm('|²³|'), 123456789,
             strxfrm('|'), 123456789, strxfrm('|'), 42, strxfrm('bar')])

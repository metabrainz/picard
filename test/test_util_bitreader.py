# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
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


from io import BytesIO

from test.picardtestcase import PicardTestCase

from picard.util.bitreader import (
    LSBBitReader,
    MSBBitReader,
)


class LsbBitReaderTest(PicardTestCase):

    def test_msb_bit_reader(self):
        data = BytesIO(b'\x8B\xC0\x17\x10')
        reader = MSBBitReader(data)
        self.assertEqual(8944, reader.bits(14))
        self.assertEqual(369, reader.bits(14))
        self.assertEqual(0, reader.bits(4))

    def test_lsb_bit_reader(self):
        data = BytesIO(b'\x8B\xC0\x17\x10')
        reader = LSBBitReader(data)
        self.assertEqual(139, reader.bits(14))
        self.assertEqual(95, reader.bits(14))
        self.assertEqual(1, reader.bits(4))

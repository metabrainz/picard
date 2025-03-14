# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021, 2025 Philipp Wolfer
# Copyright (C) 2021-2022 Laurent Monin
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
    BitReaderError,
    LSBBitReader,
    MSBBitReader,
    _BitReader,
)


class LsbBitReaderTest(PicardTestCase):

    def test_msb_bit_reader(self):
        data = BytesIO(b'\x8B\xC0\x17\x10')
        reader = MSBBitReader(data)
        self.assertEqual(8944, reader.bits(14))
        self.assertFalse(reader.is_aligned())
        self.assertEqual(369, reader.bits(14))
        self.assertEqual(0, reader.bits(4))
        self.assertEqual(32, reader.get_position())

    def test_lsb_bit_reader(self):
        data = BytesIO(b'\x8B\xC0\x17\x10')
        reader = LSBBitReader(data)
        self.assertEqual(139, reader.bits(14))
        self.assertEqual(95, reader.bits(14))
        self.assertEqual(1, reader.bits(4))
        self.assertEqual(32, reader.get_position())

    def test_alignment(self):
        data = BytesIO(b'\xFF\x00')
        reader = LSBBitReader(data)
        self.assertTrue(reader.is_aligned())
        self.assertEqual(31, reader.bits(5))
        self.assertEqual(5, reader.get_position())
        self.assertEqual(3, reader.align())
        self.assertTrue(reader.is_aligned())
        self.assertEqual(8, reader.get_position())

    def test_skip(self):
        data = BytesIO(b'\x00\xF0')
        reader = LSBBitReader(data)
        reader.skip(12)
        self.assertEqual(3, reader.bits(2))
        reader.skip(2)
        self.assertEqual(16, reader.get_position())

    def test_bytes(self):
        data = BytesIO(b'\xA0\xB0\xC0\x0D')
        reader = LSBBitReader(data)
        self.assertEqual(b'\xA0\xB0', reader.bytes(2))
        reader.skip(4)
        self.assertEqual(b'\xDC', reader.bytes(1))
        self.assertRaises(BitReaderError, reader.bytes, 1)

    def test_read_negative(self):
        self.assertRaises(ValueError, MSBBitReader(BytesIO(b'\xFF')).bits, -1)
        self.assertRaises(ValueError, LSBBitReader(BytesIO(b'\xFF')).bits, -1)
        self.assertRaises(ValueError, LSBBitReader(BytesIO(b'\xFF')).skip, -1)
        self.assertRaises(ValueError, LSBBitReader(BytesIO(b'\xFF')).bytes, -1)

    def test_read_not_enough_data(self):
        self.assertRaises(BitReaderError, MSBBitReader(BytesIO(b'\xFF')).bits, 9)
        self.assertRaises(BitReaderError, LSBBitReader(BytesIO(b'\xFF')).bits, 9)
        self.assertRaises(BitReaderError, LSBBitReader(BytesIO(b'\xFF')).skip, 9)
        self.assertRaises(BitReaderError, LSBBitReader(BytesIO(b'\xFF')).bytes, 2)

    def test_bits_no_default_implementation(self):
        self.assertRaises(NotImplementedError, _BitReader(BytesIO(b'')).bits, 0)

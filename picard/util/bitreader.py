# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2020 Christoph Reiter
# Copyright (C) 2019, 2021 Philipp Wolfer
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

# This implementation is taken from mutagen, see
# https://github.com/quodlibet/mutagen/blob/master/mutagen/_util.py
# https://github.com/quodlibet/mutagen/blob/master/mutagen/tak.py


class BitReaderError(Exception):
    pass


class _BitReader(object):

    def __init__(self, fileobj):
        self._fileobj = fileobj
        self._buffer = 0
        self._bits = 0
        self._pos = fileobj.tell()

    def bits(self, count):
        """Reads `count` bits and returns an uint.

        May raise BitReaderError if not enough data could be read or
        IOError by the underlying file object.
        """
        raise NotImplementedError

    def bytes(self, count):
        """Returns a bytearray of length `count`. Works unaligned."""

        if count < 0:
            raise ValueError

        # fast path
        if self._bits == 0:
            data = self._fileobj.read(count)
            if len(data) != count:
                raise BitReaderError("not enough data")
            return data

        return bytes(bytearray(self.bits(8) for _ in range(count)))

    def skip(self, count):
        """Skip `count` bits.

        Might raise BitReaderError if there wasn't enough data to skip,
        but might also fail on the next bits() instead.
        """

        if count < 0:
            raise ValueError

        if count <= self._bits:
            self.bits(count)
        else:
            count -= self.align()
            n_bytes = count // 8
            self._fileobj.seek(n_bytes, 1)
            count -= n_bytes * 8
            self.bits(count)

    def get_position(self):
        """Returns the amount of bits read or skipped so far"""

        return (self._fileobj.tell() - self._pos) * 8 - self._bits

    def align(self):
        """Align to the next byte, returns the amount of bits skipped"""

        bits = self._bits
        self._buffer = 0
        self._bits = 0
        return bits

    def is_aligned(self):
        """If we are currently aligned to bytes and nothing is buffered"""

        return self._bits == 0


class MSBBitReader(_BitReader):
    """BitReader implementation which reads bits starting at LSB in each byte.
    """

    def bits(self, count):
        """Reads `count` bits and returns an uint, MSB read first.

        May raise BitReaderError if not enough data could be read or
        IOError by the underlying file object.
        """

        if count < 0:
            raise ValueError

        if count > self._bits:
            n_bytes = (count - self._bits + 7) // 8
            data = self._fileobj.read(n_bytes)
            if len(data) != n_bytes:
                raise BitReaderError("not enough data")
            for b in bytearray(data):
                self._buffer = (self._buffer << 8) | b
            self._bits += n_bytes * 8

        self._bits -= count
        value = self._buffer >> self._bits
        self._buffer &= (1 << self._bits) - 1
        return value


class LSBBitReader(_BitReader):
    """BitReader implementation which reads bits starting at LSB in each byte.
    """

    def _lsb(self, count):
        value = self._buffer & 0xff >> (8 - count)
        self._buffer = self._buffer >> count
        self._bits -= count
        return value

    def bits(self, count):
        """Reads `count` bits and returns an uint, LSB read first.

        May raise BitReaderError if not enough data could be read or
        IOError by the underlying file object.
        """
        if count < 0:
            raise ValueError

        value = 0
        if count <= self._bits:
            value = self._lsb(count)
        else:
            # First read all available bits
            shift = 0
            remaining = count
            if self._bits > 0:
                remaining -= self._bits
                shift = self._bits
                value = self._lsb(self._bits)

            # Now add additional bytes
            n_bytes = (remaining - self._bits + 7) // 8
            data = self._fileobj.read(n_bytes)
            if len(data) != n_bytes:
                raise BitReaderError("not enough data")
            for b in bytearray(data):
                if remaining > 8:  # Use full byte
                    remaining -= 8
                    value = (b << shift) | value
                    shift += 8
                else:
                    self._buffer = b
                    self._bits = 8
                    b = self._lsb(remaining)
                    value = (b << shift) | value

        return value

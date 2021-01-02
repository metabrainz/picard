# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2018, 2020 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
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
import struct

from picard.util.bitreader import LSBBitReader


class IdentificationError(Exception):
    pass


class NotEnoughData(IdentificationError):
    pass


class UnrecognizedFormat(IdentificationError):
    pass


class UnexpectedError(IdentificationError):
    pass


def identify(data):
    """Parse data for jpg, gif, png, webp and pdf metadata
    If successfully recognized, it returns a tuple with:
        - width
        - height
        - mimetype
        - extension
        - data length
    Exceptions:
        - `NotEnoughData` if data has less than 16 bytes.
        - `UnrecognizedFormat` if data isn't recognized as a known format.
        - `UnexpectedError` if unhandled cases (shouldn't happen).
        - `IdentificationError` is parent class for all preceding exceptions.
    """

    datalen = len(data)
    if datalen < 16:
        raise NotEnoughData('Not enough data')

    w = -1
    h = -1
    mime = ''
    extension = ''

    # http://en.wikipedia.org/wiki/Graphics_Interchange_Format
    if data[:6] in (b'GIF87a', b'GIF89a'):
        w, h = struct.unpack('<HH', data[6:10])
        mime = 'image/gif'
        extension = '.gif'

    # http://en.wikipedia.org/wiki/Portable_Network_Graphics
    # http://www.w3.org/TR/PNG/#11IHDR
    elif data[:8] == b'\x89PNG\x0D\x0A\x1A\x0A' and data[12:16] == b'IHDR':
        w, h = struct.unpack('>LL', data[16:24])
        mime = 'image/png'
        extension = '.png'

    # http://en.wikipedia.org/wiki/JPEG
    elif data[:2] == b'\xFF\xD8':  # Start Of Image (SOI) marker
        jpeg = BytesIO(data)
        # skip SOI
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            while b and ord(b) != 0xDA:  # Start Of Scan (SOS)
                while ord(b) != 0xFF:
                    b = jpeg.read(1)
                while ord(b) == 0xFF:
                    b = jpeg.read(1)
                if ord(b) in (0xC0, 0xC1, 0xC2, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    jpeg.read(2)  # parameter length (2 bytes)
                    jpeg.read(1)  # data precision (1 byte)
                    h, w = struct.unpack('>HH', jpeg.read(4))
                    mime = 'image/jpeg'
                    extension = '.jpg'
                    break
                else:
                    # read 2 bytes as integer
                    length = int(struct.unpack('>H', jpeg.read(2))[0])
                    # skip data
                    jpeg.read(length - 2)
                b = jpeg.read(1)
        except struct.error:
            pass
        except ValueError:
            pass

    # WebP
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        # See https://developers.google.com/speed/webp/docs/riff_container
        format = data[12:16]
        # Simple File Format (Lossy)
        if format == b'VP8 ':
            # See https://tools.ietf.org/html/rfc6386#section-9.1
            index = data.find(b'\x9d\x01\x2a')
            if index != -1:
                if len(data) < index + 7:
                    raise NotEnoughData('Not enough data for WebP VP8')
                w, h = struct.unpack('<HH', data[index + 3:index + 7])
                # Width and height are encoded as 14 bit integers, ignore the first 2 bits
                w &= 0x3fff
                h &= 0x3fff
            else:
                w, h = 0, 0
        # Simple File Format (Lossless)
        elif format == b'VP8L':
            if len(data) < 25:
                raise NotEnoughData('Not enough data for WebP VP8L')
            reader = LSBBitReader(BytesIO(data[21:25]))
            w = reader.bits(14) + 1
            h = reader.bits(14) + 1
        # Extended File Format
        elif format == b'VP8X':
            if len(data) < 30:
                raise NotEnoughData('Not enough data for WebP VP8X')
            reader = LSBBitReader(BytesIO(data[24:30]))
            w = reader.bits(24) + 1
            h = reader.bits(24) + 1
        else:
            h, w = 0, 0
        mime = 'image/webp'
        extension = '.webp'

    # TIFF
    elif data[:4] == b'II*\x00' or data[:4] == b'MM\x00*':
        TIFF_BYTE_ORDER_LSB = b'II'
        TIFF_BYTE_ORDER_MSB = b'MM'
        TIFF_TAG_IMAGE_LENGTH = 257
        TIFF_TAG_IMAGE_WIDTH = 256
        TIFF_TYPE_SHORT = 3
        TIFF_TYPE_LONG = 4

        def read_value(type, data):
            if type == TIFF_TYPE_LONG:
                value = data[:4]
                format = order + 'I'
            elif type == TIFF_TYPE_SHORT:
                value = data[:2]
                format = order + 'H'
            return struct.unpack(format, value)[0]

        byte_order = data[:2]
        if byte_order == TIFF_BYTE_ORDER_LSB:
            order = '<'
        elif byte_order == TIFF_BYTE_ORDER_MSB:
            order = '>'
        try:
            offset, = struct.unpack(order + 'I', data[4:8])
            entry_count, = struct.unpack(order + 'H', data[offset:offset + 2])
            pos = offset + 2
            for i in range(entry_count):
                field = data[pos:pos + 12]
                tag, type = struct.unpack(order + 'HH', field[:4])
                if tag == TIFF_TAG_IMAGE_WIDTH:
                    w = read_value(type, field[8:12])
                elif tag == TIFF_TAG_IMAGE_LENGTH:
                    h = read_value(type, field[8:12])
                if h > -1 and w > -1:  # Found both width and height, abort
                    break
                pos += 12
            else:
                w, h = 0, 0
        except struct.error:
            w, h = 0, 0
        mime = 'image/tiff'
        extension = '.tiff'

    # PDF
    elif data[:4] == b'%PDF':
        h, w = 0, 0
        mime = 'application/pdf'
        extension = '.pdf'

    else:
        raise UnrecognizedFormat('Unrecognized image data')

    # this shouldn't happen
    if w == -1 or h == -1 or mime == '' or extension == '':
        raise UnexpectedError("Unexpected error: w=%d h=%d mime=%s extension=%s"
                              % (w, h, mime, extension))

    return (int(w), int(h), mime, extension, datalen)

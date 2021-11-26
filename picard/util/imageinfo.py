# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2018, 2020-2021 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2020-2021 Philipp Wolfer
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


class IdentifyImageType:
    mime = ''
    extension = ''
    w = -1
    h = -1

    def __init__(self, data):
        self.data = data
        self.datalen = len(self.data)
        if self.datalen < 16:
            raise NotEnoughData('Not enough data')

    def read(self):
        self._read()
        return self._result()

    def _result(self):
        return (int(self.w), int(self.h), self.mime, self.extension, self.datalen)

    def match(self):
        raise NotImplementedError

    def _read(self):
        raise NotImplementedError

    @classmethod
    def all_extensions(cls):
        return [cls.extension]


class IdentifyJPEG(IdentifyImageType):
    mime = 'image/jpeg'
    extension = '.jpg'

    def match(self):
        # http://en.wikipedia.org/wiki/JPEG
        return self.data[:2] == b'\xFF\xD8'  # Start Of Image (SOI) marker

    @classmethod
    def all_extensions(cls):
        return [cls.extension, '.jpeg']

    def _read(self):
        jpeg = BytesIO(self.data)
        # skip SOI
        jpeg.read(2)
        b = jpeg.read(1)
        try:
            # https://en.wikibooks.org/wiki/JPEG_-_Idea_and_Practice/The_header_part
            # https://www.disktuna.com/list-of-jpeg-markers/
            # https://de.wikipedia.org/wiki/JPEG_File_Interchange_Format
            SOF_markers = {
                0xC0, 0xC1, 0xC2, 0xC3,
                0xC5, 0xC6, 0xC7,
                0xC9, 0xCA, 0xCB,
                0xCD, 0xCE, 0xCF
            }
            while b and ord(b) != 0xDA:  # Start Of Scan (SOS)
                while ord(b) != 0xFF:
                    b = jpeg.read(1)
                while ord(b) == 0xFF:
                    b = jpeg.read(1)
                if ord(b) in SOF_markers:
                    jpeg.read(2)  # parameter length (2 bytes)
                    jpeg.read(1)  # data precision (1 byte)
                    self.h, self.w = struct.unpack('>HH', jpeg.read(4))
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


class IdentifyGIF(IdentifyImageType):
    mime = 'image/gif'
    extension = '.gif'

    def match(self):
        # http://en.wikipedia.org/wiki/Graphics_Interchange_Format
        return self.data[:6] in {b'GIF87a', b'GIF89a'}

    def _read(self):
        self.w, self.h = struct.unpack('<HH', self.data[6:10])


class IdentifyPDF(IdentifyImageType):
    mime = 'application/pdf'
    extension = '.pdf'

    def match(self):
        # PDF
        return self.data[:4] == b'%PDF'

    def _read(self):
        self.w = self.h = 0


class IdentifyPNG(IdentifyImageType):
    mime = 'image/png'
    extension = '.png'

    def match(self):
        # http://en.wikipedia.org/wiki/Portable_Network_Graphics
        # http://www.w3.org/TR/PNG/#11IHDR
        return self.data[:8] == b'\x89PNG\x0D\x0A\x1A\x0A' and self.data[12:16] == b'IHDR'

    def _read(self):
        self.w, self.h = struct.unpack('>LL', self.data[16:24])


class IdentifyWebP(IdentifyImageType):
    mime = 'image/webp'
    extension = '.webp'

    def match(self):
        return self.data[:4] == b'RIFF' and self.data[8:12] == b'WEBP'

    def _read(self):
        data = self.data
        # See https://developers.google.com/speed/webp/docs/riff_container
        format = data[12:16]
        # Simple File Format (Lossy)
        if format == b'VP8 ':
            # See https://tools.ietf.org/html/rfc6386#section-9.1
            index = data.find(b'\x9d\x01\x2a')
            if index != -1:
                if self.datalen < index + 7:
                    raise NotEnoughData('Not enough data for WebP VP8')
                self.w, self.h = struct.unpack('<HH', data[index + 3:index + 7])
                # Width and height are encoded as 14 bit integers, ignore the first 2 bits
                self.w &= 0x3fff
                self.h &= 0x3fff
            else:
                self.w, self.h = 0, 0
        # Simple File Format (Lossless)
        elif format == b'VP8L':
            if self.datalen < 25:
                raise NotEnoughData('Not enough data for WebP VP8L')
            reader = LSBBitReader(BytesIO(data[21:25]))
            self.w = reader.bits(14) + 1
            self.h = reader.bits(14) + 1
        # Extended File Format
        elif format == b'VP8X':
            if self.datalen < 30:
                raise NotEnoughData('Not enough data for WebP VP8X')
            reader = LSBBitReader(BytesIO(data[24:30]))
            self.w = reader.bits(24) + 1
            self.h = reader.bits(24) + 1
        else:
            self.h, self.w = 0, 0


TIFF_BYTE_ORDER_LSB = b'II'
TIFF_BYTE_ORDER_MSB = b'MM'
TIFF_TAG_IMAGE_LENGTH = 257
TIFF_TAG_IMAGE_WIDTH = 256
TIFF_TYPE_SHORT = 3
TIFF_TYPE_LONG = 4


class IdentifyTiff(IdentifyImageType):
    mime = 'image/tiff'
    extension = '.tiff'

    def match(self):
        return self.data[:4] == b'II*\x00' or self.data[:4] == b'MM\x00*'

    @classmethod
    def all_extensions(cls):
        return [cls.extension, '.tif']

    def _read(self):
        # See https://www.adobe.io/content/dam/udp/en/open/standards/tiff/TIFF6.pdf
        data = self.data
        self.w, self.h = 0, 0
        byte_order = data[:2]
        if byte_order == TIFF_BYTE_ORDER_LSB:
            order = '<'
        elif byte_order == TIFF_BYTE_ORDER_MSB:
            order = '>'
        else:
            raise UnexpectedError('TIFF: unexpected byte order %r' % byte_order)
        try:
            offset, = struct.unpack(order + 'I', data[4:8])
            entry_count, = struct.unpack(order + 'H', data[offset:offset + 2])
            pos = offset + 2
            for i in range(entry_count):
                field = data[pos:pos + 12]
                tag, tiff_type = struct.unpack(order + 'HH', field[:4])
                if tag == TIFF_TAG_IMAGE_WIDTH:
                    self.w = self._read_value(tiff_type, order, field[8:12])
                    if self.h:
                        return
                elif tag == TIFF_TAG_IMAGE_LENGTH:
                    self.h = self._read_value(tiff_type, order, field[8:12])
                    if self.w:
                        return
                pos += 12
        except struct.error:
            pass

    @staticmethod
    def _read_value(tiff_type, order, data):
        if tiff_type == TIFF_TYPE_LONG:
            value = data[:4]
            struct_format = order + 'I'
        elif tiff_type == TIFF_TYPE_SHORT:
            value = data[:2]
            struct_format = order + 'H'
        else:
            raise UnexpectedError('TIFF: unexpected field type %s' % tiff_type)
        return struct.unpack(struct_format, value)[0]


knownimagetypes = (
    IdentifyJPEG,
    IdentifyPNG,
    IdentifyPDF,
    IdentifyGIF,
    IdentifyWebP,
    IdentifyTiff,
)


def identify(data):
    """Parse data for jpg, gif, png, webp, tiff and pdf metadata
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
    for cls in knownimagetypes:
        obj = cls(data)
        if obj.match():
            return obj.read()

    raise UnrecognizedFormat('Unrecognized image data')


def supports_mime_type(mime):
    return any(cls.mime == mime for cls in knownimagetypes)


def get_supported_extensions():
    for cls in knownimagetypes:
        yield from cls.all_extensions()

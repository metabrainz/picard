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

from mutagen.tak import _LSBBitReader as LSBBitReader


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
            # TODO: Implement reading width and height
            h, w = 0, 0
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

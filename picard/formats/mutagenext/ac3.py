# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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


"""Pure AC3 files with APEv2 tags.
"""

__all__ = ["AC3", "Open", "delete"]

from mutagen._util import (
    BitReader,
    BitReaderError,
)
from mutagen.apev2 import (
    APEv2File,
    _APEv2Data,
    delete,
    error,
)


AC3_HEADER_SIZE = 7

AC3_CHMODE_DUALMONO = 0
AC3_CHMODE_MONO = 1
AC3_CHMODE_STEREO = 2
AC3_CHMODE_3F = 3
AC3_CHMODE_2F1R = 4
AC3_CHMODE_3F1R = 5
AC3_CHMODE_2F2R = 6
AC3_CHMODE_3F2R = 7

AC3_CHANNELS = {
    AC3_CHMODE_DUALMONO: 2,
    AC3_CHMODE_MONO: 1,
    AC3_CHMODE_STEREO: 2,
    AC3_CHMODE_3F: 3,
    AC3_CHMODE_2F1R: 3,
    AC3_CHMODE_3F1R: 4,
    AC3_CHMODE_2F2R: 4,
    AC3_CHMODE_3F2R: 5
}

AC3_SAMPLE_RATES = [48000, 44100, 32000]

AC3_BITRATES = [
    32, 40, 48, 56, 64, 80, 96, 112, 128,
    160, 192, 224, 256, 320, 384, 448, 512, 576, 640
]

EAC3_FRAME_TYPE_INDEPENDENT = 0
EAC3_FRAME_TYPE_DEPENDENT = 1
EAC3_FRAME_TYPE_AC3_CONVERT = 2
EAC3_FRAME_TYPE_RESERVED = 3

EAC3_BLOCKS = [1, 2, 3, 6]


class AC3HeaderError(error):
    pass


class AC3Info(object):

    """AC3 stream information.
    The length of the stream is just a guess and might not be correct.

    Attributes:
        channels (`int`): number of audio channels
        length (`float`): file length in seconds, as a float
        sample_rate (`int`): audio sampling rate in Hz
        bitrate (`int`): audio bitrate, in bits per second
        type (`str`): AC3 or EAC3
    """

    channels = 0
    length = 0
    sample_rate = 0
    bitrate = 0
    type = 'AC3'

    def __init__(self, fileobj):
        header = fileobj.read(6)
        if not header.startswith(b"\x0b\x77"):
            raise AC3HeaderError("not a AC3 file")

        bitstream_id = header[5] >> 3
        if bitstream_id > 16:
            raise AC3HeaderError("invalid bitstream_id %i" % bitstream_id)

        fileobj.seek(2)
        self._read_header(fileobj, bitstream_id)

    def _read_header(self, fileobj, bitstream_id):
        bitreader = BitReader(fileobj)
        try:
            # This is partially based on code from
            # https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/ac3_parser.c
            if bitstream_id <= 10:  # Normal AC-3
                self._read_header_normal(bitreader, bitstream_id)
            else:  # Enhanced AC-3
                self._read_header_enhanced(bitreader)
        except (BitReaderError, KeyError) as e:
            raise AC3HeaderError(e)

        self.length = self._guess_length(fileobj)

    def _read_header_normal(self, bitreader, bitstream_id):
        r = bitreader
        r.skip(16)  # 16 bit CRC
        sr_code = r.bits(2)
        if sr_code == 3:
            raise AC3HeaderError("invalid sample rate code %i" % sr_code)

        frame_size_code = r.bits(6)
        if frame_size_code > 37:
            raise AC3HeaderError("invalid frame size code %i" % frame_size_code)

        r.skip(5)  # bitstream ID, already read
        r.skip(3)  # bitstream mode, not needed
        channel_mode = r.bits(3)
        r.skip(2)  # dolby surround mode (AC3_CHMODE_MONO) or surround mix level
        lfe_on = r.bits(1)

        sr_shift = max(bitstream_id, 8) - 8
        self.sample_rate = AC3_SAMPLE_RATES[sr_code] >> sr_shift
        self.bitrate = (AC3_BITRATES[frame_size_code >> 1] * 1000) >> sr_shift
        self.channels = self._get_channels(channel_mode, lfe_on)
        self._skip_unused_header_bits_normal(r, channel_mode)

    def _read_header_enhanced(self, bitreader):
        r = bitreader
        self.type = "EAC3"
        frame_type = r.bits(2)
        if frame_type == EAC3_FRAME_TYPE_RESERVED:
            raise AC3HeaderError("invalid frame type %i" % frame_type)

        r.skip(3)  # substream ID, not needed

        frame_size = (r.bits(11) + 1) << 1
        if frame_size < AC3_HEADER_SIZE:
            raise AC3HeaderError("invalid frame size %i" % frame_size)

        sr_code = r.bits(2)
        if sr_code == 3:
            sr_code2 = r.bits(2)
            if sr_code2 == 3:
                raise AC3HeaderError("invalid sample rate code %i" % sr_code2)

            numblocks_code = 3
            self.sample_rate = AC3_SAMPLE_RATES[sr_code2] / 2
        else:
            numblocks_code = r.bits(2)
            self.sample_rate = AC3_SAMPLE_RATES[sr_code]

        channel_mode = r.bits(3)
        lfe_on = r.bits(1)
        self.bitrate = 8 * frame_size * self.sample_rate / (EAC3_BLOCKS[numblocks_code] * 256)
        r.skip(5)  # bitstream ID, already read
        self.channels = self._get_channels(channel_mode, lfe_on)
        self._skip_unused_header_bits_enhanced(
            r, frame_type, channel_mode, sr_code, numblocks_code)

    @staticmethod
    def _skip_unused_header_bits_normal(bitreader, channel_mode):
        r = bitreader
        r.skip(5)  # Dialogue Normalization, 5 Bits
        if r.bits(1):  # Compression Gain Word Exists, 1 Bit
            r.skip(8)  # Compression Gain Word, 8 Bits
        if r.bits(1):  # Language Code Exists, 1 Bit
            r.skip(8)  # Language Code, 8 Bits
        if r.bits(1):  # Audio Production Information Exists, 1 Bit
            # Mixing Level, 5 Bits
            # Room Type, 2 Bits
            r.skip(7)
        if channel_mode == AC3_CHMODE_DUALMONO:
            r.skip(5)  # Dialogue Normalization, ch2, 5 Bits
            if r.bits(1):  # Compression Gain Word Exists, ch2, 1 Bit
                r.skip(8)  # Compression Gain Word, ch2, 1 Bit
            if r.bits(1):  # Language Code Exists, ch2, 1 Bit
                r.skip(8)  # Language Code, ch2, 1 Bit
            if r.bits(1):  # Audio Production Information Exists, ch2, 1 Bit
                # Mixing Level, ch2, 5 Bits
                # Room Type, ch2, 2 Bits
                r.skip(7)
        # Copyright Bit, 1 Bit
        # Original Bit Stream, 1 Bit
        r.skip(2)
        timecod1e = r.bits(1)  # Time Code First Halve Exists, 1 Bit
        timecod2e = r.bits(1)  # Time Code Second Halve Exists, 1 Bit
        if timecod1e:
            r.skip(14)  # Time Code First Half, 14 Bits
        if timecod2e:
            r.skip(14)  # Time Code Second Half, 14 Bits
        if r.bits(1):  # Additional Bit Stream Information Exists, 1 Bit
            addbsil = r.bit(6)  # Additional Bit Stream Information Length, 6 Bits
            r.skip((addbsil + 1) * 8)

    @staticmethod
    def _skip_unused_header_bits_enhanced(bitreader, frame_type, channel_mode, sr_code, numblocks_code):
        r = bitreader
        r.skip(5)  # Dialogue Normalization, 5 Bits
        if r.bits(1):  # Compression Gain Word Exists, 1 Bit
            r.skip(8)  # Compression Gain Word, 8 Bits
        if channel_mode == AC3_CHMODE_DUALMONO:
            r.skip(5)  # Dialogue Normalization, ch2, 5 Bits
            if r.bits(1):  # Compression Gain Word Exists, ch2, 1 Bit
                r.skip(8)  # Compression Gain Word, ch2, 8 Bits
        if frame_type == EAC3_FRAME_TYPE_DEPENDENT:
            if r.bits(1):  # chanmap exists
                r.skip(16)  # chanmap
        if r.bits(1):  # mixmdate, 1 Bit
            # FIXME: Handle channel dependent fields
            return
        if r.bits(1):  # Informational Metadata Exists, 1 Bit
            # bsmod, 3 Bits
            # Copyright Bit, 1 Bit
            # Original Bit Stream, 1 Bit
            r.skip(5)
            if channel_mode == AC3_CHMODE_STEREO:
                # dsurmod. 2 Bits
                # dheadphonmod, 2 Bits
                r.skip(4)
            elif channel_mode >= AC3_CHMODE_2F2R:
                r.skip(2)  # dsurexmod, 2 Bits
            if r.bits(1):  # Audio Production Information Exists, 1 Bit
                # Mixing Level, 5 Bits
                # Room Type, 2 Bits
                # adconvtyp, 1 Bit
                r.skip(8)
            if channel_mode == AC3_CHMODE_DUALMONO:
                if r.bits(1):  # Audio Production Information Exists, ch2, 1 Bit
                    # Mixing Level, ch2, 5 Bits
                    # Room Type, ch2, 2 Bits
                    # adconvtyp, ch2, 1 Bit
                    r.skip(8)
            if sr_code < 3:  # if not half sample rate
                r.skip(1)  # sourcefscod, 1 Bit
        if frame_type == EAC3_FRAME_TYPE_INDEPENDENT and numblocks_code == 3:
            r.skip(1)  # convsync, 1 Bit
        if frame_type == EAC3_FRAME_TYPE_AC3_CONVERT:
            if numblocks_code != 3:
                if r.bits(1):  # blkid
                    r.skip(6)  # frmsizecod
        if r.bits(1):  # Additional Bit Stream Information Exists, 1 Bit
            addbsil = r.bit(6)  # Additional Bit Stream Information Length, 6 Bits
            r.skip((addbsil + 1) * 8)

    @staticmethod
    def _get_channels(channel_mode, lfe_on):
        return AC3_CHANNELS[channel_mode] + lfe_on

    def _guess_length(self, fileobj):
        # use bitrate + data size to guess length
        if self.bitrate == 0:
            return
        start = fileobj.tell()
        fileobj.seek(0, 2)
        length = fileobj.tell() - start
        ape_data = _APEv2Data(fileobj)
        if ape_data.size is not None:
            length -= ape_data.size
        return 8 * length / self.bitrate

    def pprint(self):
        return "%s, %d Hz, %.2f seconds, %d channel(s), %d bps" % (
            self.type, self.sample_rate, self.length, self.channels,
            self.bitrate)


class AC3APEv2(APEv2File):
    _Info = AC3Info
    _mimes = ["audio/ac3"]

    @staticmethod
    def score(filename, fileobj, header):
        return header.startswith(b"\x0b\x77") + filename.lower().endswith(".ac3")


Open = AC3APEv2

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

from mutagen.apev2 import (
    APEv2File,
    delete,
    error,
)


class AC3HeaderError(error):
    pass


class AC3Info(object):

    """AC3 stream information.

    Attributes:
      (none at the moment)
    """

    def __init__(self, fileobj):
        header = fileobj.read(2)
        if len(header) != 2 or not header.startswith(b"\x0b\x77"):
            raise AC3HeaderError("not a AC3 file")
        # https://github.com/FFmpeg/FFmpeg/blob/08b1d1d8122517d07f2335437cde0aeedc50143f/libavcodec/ac3_parser.c#L54

    @staticmethod
    def pprint():
        return "AC3"


class AC3APEv2(APEv2File):
    _Info = AC3Info
    _mimes = ["audio/ac3"]

    @staticmethod
    def score(filename, fileobj, header):
        return header.startswith(b"\x0b\x77") + filename.lower().endswith(".ac3")


Open = AC3APEv2

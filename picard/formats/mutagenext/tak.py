# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2008 Lukáš Lalinský
# Copyright (C) 2013, 2018-2021 Laurent Monin
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018-2019, 2022 Philipp Wolfer
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


"""Tom's lossless Audio Kompressor streams with APEv2 tags.

TAK is a lossless audio compressor developed by Thomas Becker.

For more information, see http://wiki.hydrogenaudio.org/index.php?title=TAK
and http://en.wikipedia.org/wiki/TAK_(audio_codec)
"""

__all__ = ["TAK", "Open", "delete"]

try:
    from mutagen.tak import (
        TAK,
        Open,
        TAKHeaderError,
        TAKInfo,
        delete,
    )

    native_tak = True

except ImportError:
    from mutagen import StreamInfo
    from mutagen.apev2 import (
        APEv2File,
        delete,
        error,
    )

    native_tak = False

    class TAKHeaderError(error):
        pass

    class TAKInfo(StreamInfo):

        """TAK stream information.

        Attributes:
          (none at the moment)
        """

        def __init__(self, fileobj):
            header = fileobj.read(4)
            if len(header) != 4 or not header.startswith(b"tBaK"):
                raise TAKHeaderError("not a TAK file")

        @staticmethod
        def pprint():
            return "Tom's lossless Audio Kompressor"

    class TAK(APEv2File):
        """TAK(filething)

        Arguments:
            filething (filething)

        Attributes:
            info (`TAKInfo`)
        """

        _Info = TAKInfo
        _mimes = ["audio/x-tak"]

        @staticmethod
        def score(filename, fileobj, header):
            return header.startswith(b"tBaK") + filename.lower().endswith(".tak")

    Open = TAK

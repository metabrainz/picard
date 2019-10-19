# Tom's lossless Audio Kompressor (TAK) reader/tagger
#
# Copyright 2008 Lukas Lalinsky <lalinsky@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# $$

"""Tom's lossless Audio Kompressor streams with APEv2 tags.

TAK is a lossless audio compressor developed by Thomas Becker.

For more information, see http://wiki.hydrogenaudio.org/index.php?title=TAK
and http://en.wikipedia.org/wiki/TAK_(audio_codec)
"""

__all__ = ["TAK", "Open", "delete"]

try:
    from mutagen.tak import (
        Open,
        TAK,
        TAKHeaderError,
        TAKInfo,
        delete
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

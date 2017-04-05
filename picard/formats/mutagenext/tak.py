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

from mutagen.apev2 import APEv2File, error, delete


class TAKHeaderError(error):
    pass


class TAKInfo(object):

    """TAK stream information.

    Attributes:
      (none at the moment)
    """

    def __init__(self, fileobj):
        header = fileobj.read(4)
        if len(header) != 4 or not header.startswith("tBaK"):
            raise TAKHeaderError("not a TAK file")

    def pprint(self):
        return "Tom's lossless Audio Kompressor"


class TAK(APEv2File):
    _Info = TAKInfo
    _mimes = ["audio/x-tak"]

    def score(filename, fileobj, header):
        return header.startswith(b"tBaK") + filename.lower().endswith(".tak")
    score = staticmethod(score)

Open = TAK

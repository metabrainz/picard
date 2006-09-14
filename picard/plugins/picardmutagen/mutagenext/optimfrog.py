# OptimFROG reader/tagger
#
# Copyright 2006 Lukas Lalinsky <lalinsky@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# $Id$

"""OptimFROG audio streams with APEv2 tags.

OptimFROG is a lossless audio compression program. Its main goal is to
reduce at maximum the size of audio files, while permitting bit
identical restoration for all input. It is similar with the ZIP
compression, but it is highly specialized to compress audio data.

For more information, see http://www.losslessaudio.org/
"""

__all__ = ["OptimFROG", "Open", "delete"]

from mutagen.apev2 import APEv2File, error
from mutagen._util import cdata

class OptimFROGHeaderError(error): pass

class OptimFROGInfo(object):
    """OptimFROG stream information.

    Attributes:
    channels - number of audio channels
    length - file length in seconds, as a float
    sample_rate - audio sampling rate in Hz
    bitrate -- audio bitrate, in bits per second 
    """

    def __init__(self, fileobj):
        self.channels = 0
        self.length = 0.0
        self.sample_rate = 0
        self.bitrate = 0

    def pprint(self):
        return "OptimFROG, %.2f seconds, %d Hz" % (self.length,
                                                   self.sample_rate)

class OptimFROG(APEv2File):
    _Info = OptimFROGInfo

    def score(filename, fileobj, header):
        return (header.startswith("OFR") + filename.endswith(".ofr") +
                filename.endswith(".ofs"))
    score = staticmethod(score)

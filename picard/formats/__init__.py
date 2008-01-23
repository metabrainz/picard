# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from picard.plugin import ExtensionPoint

_formats = ExtensionPoint()
_extensions = {}

def register_format(format):
    _formats.register(format.__module__, format)
    for ext in format.EXTENSIONS:
        _extensions[ext[1:]] = format

def supported_formats():
    """Returns list of supported formats."""
    formats = []
    for format in _formats:
        formats.append((format.EXTENSIONS, format.NAME))
    return formats

def open(filename):
    """Open the specified file and return a File instance with the appropriate format handler, or None."""
    i = filename.rfind(".")
    if i < 0:
        return None
    ext = filename[i+1:].lower()
    try:
        format = _extensions[ext]
    except KeyError:
        return None
    return format(filename)


from picard.formats.id3 import (
    MP3File,
    TrueAudioFile,
    )
register_format(MP3File)
register_format(TrueAudioFile)

from picard.formats.apev2 import (
    MonkeysAudioFile,
    MusepackFile,
    OptimFROGFile,
    WavPackFile,
    )
register_format(MusepackFile)
register_format(WavPackFile)
register_format(OptimFROGFile)
register_format(MonkeysAudioFile)

from picard.formats.vorbis import (
    FLACFile,
    OggFLACFile,
    OggSpeexFile,
    OggVorbisFile,
    )
register_format(FLACFile)
register_format(OggFLACFile)
register_format(OggSpeexFile)
register_format(OggVorbisFile)

try:
    from picard.formats.mp4 import MP4File
    register_format(MP4File)
except ImportError:
    pass

try:
    from picard.formats.asf import ASFFile
    register_format(ASFFile)
except ImportError:
    pass

from picard.formats.wav import WAVFile
register_format(WAVFile)

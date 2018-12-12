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

from picard import log
from picard.plugin import ExtensionPoint

_formats = ExtensionPoint()
_extensions = {}


def register_format(file_format):
    _formats.register(file_format.__module__, file_format)
    for ext in file_format.EXTENSIONS:
        _extensions[ext[1:]] = file_format


def supported_formats():
    """Returns list of supported formats."""
    return [(file_format.EXTENSIONS, file_format.NAME) for file_format in _formats]


def supported_extensions():
    """Returns list of supported extensions."""
    return [ext for exts, name in supported_formats() for ext in exts]


def ext_to_format(ext):
    return _extensions.get(ext, None)


def guess_format(filename, options=_formats):
    """Select the best matching file type amongst supported formats."""
    results = []
    # Since we are reading only 128 bytes and then immediately closing the file,
    # use unbuffered mode.
    with open(filename, "rb", 0) as fileobj:
        header = fileobj.read(128)
        # Calls the score method of a particular format's associated filetype
        # and assigns a positive score depending on how closely the fileobj's header matches
        # the header for a particular file format.
        results = [(option._File.score(filename, fileobj, header), option.__name__, option)
                   for option in options
                   if getattr(option, "_File", None)]
    if results:
        results.sort()
        if results[-1][0] > 0:
            # return the format with the highest matching score
            return results[-1][2](filename)

    # No positive score i.e. the fileobj's header did not match any supported format
    return None


def open_(filename):
    """Open the specified file and return a File instance with the appropriate format handler, or None."""
    try:
        # First try to guess the format on the basis of file headers
        audio_file = guess_format(filename)
        if not audio_file:
            i = filename.rfind(".")
            if i < 0:
                return None
            ext = filename[i+1:].lower()
            # Switch to extension based opening if guess_format fails
            audio_file = _extensions[ext](filename)
        return audio_file
    except KeyError:
        # None is returned if both the methods fail
        return None
    except Exception as error:
        log.error("Error occurred:\n{}".format(error))
        return None


from picard.formats.id3 import (
    AiffFile,
    DSFFile,
    MP3File,
    TrueAudioFile,
)
register_format(AiffFile)
register_format(DSFFile)
register_format(MP3File)
register_format(TrueAudioFile)

from picard.formats.apev2 import (
    MonkeysAudioFile,
    MusepackFile,
    OptimFROGFile,
    WavPackFile,
    TAKFile,
)
register_format(MusepackFile)
register_format(WavPackFile)
register_format(OptimFROGFile)
register_format(MonkeysAudioFile)
register_format(TAKFile)

from picard.formats.vorbis import (
    FLACFile,
    OggFLACFile,
    OggSpeexFile,
    OggVorbisFile,
    OggAudioFile,
    OggVideoFile,
    OggOpusFile,
)
register_format(FLACFile)
register_format(OggFLACFile)
register_format(OggSpeexFile)
register_format(OggVorbisFile)
register_format(OggOpusFile)
register_format(OggAudioFile)
register_format(OggVideoFile)

from picard.formats.mp4 import MP4File
register_format(MP4File)

from picard.formats.asf import ASFFile
register_format(ASFFile)

from picard.formats.wav import WAVFile
register_format(WAVFile)

from picard.formats.midi import MIDIFile
register_format(MIDIFile)

from picard.formats.aac import AACFile
register_format(AACFile)

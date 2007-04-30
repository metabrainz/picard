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

def register_format(format):
    _formats.register(format.__module__, format)

def supported_formats():
    """Returns list of supported formats."""
    formats = []
    for format in _formats:
        formats.append((format.EXTENSIONS, format.NAME))
    return formats

def open(filename):
    """Open the specified file and return a File instance, or None."""
    for format in _formats:
        for extension in format.EXTENSIONS:
            if filename.lower().endswith(extension):
                file = format(filename)
                if file:
                    return file
    return None


def _insert_bytes(fobj, size, offset):
    """Insert size bytes of empty space starting at offset.

    fobj must be an open file object, open rb+ or
    equivalent. Mutagen tries to use mmap to resize the file, but
    falls back to a significantly slower method if mmap fails.
    """
    assert 0 < size
    assert 0 <= offset
    fobj.seek(0, 2)
    filesize = fobj.tell()
    movesize = filesize - offset
    fobj.write('\x00' * size)
    fobj.flush()
    fobj.truncate(filesize)
    fobj.seek(offset)
    backbuf = fobj.read(size)
    offset += len(backbuf)
    if len(backbuf) < size:
        fobj.seek(offset)
        fobj.write('\x00' * (size - len(backbuf)))
    while len(backbuf) == size:
        frontbuf = fobj.read(size)
        fobj.seek(offset)
        fobj.write(backbuf)
        offset += len(backbuf)
        fobj.seek(offset)
        backbuf = frontbuf
    fobj.write(backbuf)

def _delete_bytes(fobj, size, offset):
    """Delete size bytes of empty space starting at offset.

    fobj must be an open file object, open rb+ or
    equivalent. Mutagen tries to use mmap to resize the file, but
    falls back to a significantly slower method if mmap fails.
    """
    assert 0 < size
    assert 0 <= offset
    fobj.seek(0, 2)
    filesize = fobj.tell()
    movesize = filesize - offset - size
    assert 0 <= movesize
    if movesize > 0:
        fobj.flush()
        fobj.seek(offset + size)
        buf = fobj.read(size)
        while len(buf):
            fobj.seek(offset)
            fobj.write(buf)
            offset += len(buf)
            fobj.seek(offset + size)
            buf = fobj.read(size)
    fobj.truncate(filesize - size)
    fobj.flush()

# Patch Mutagen to disable mmap
import mutagen._util
mutagen._util.insert_bytes = _insert_bytes
mutagen._util.delete_bytes = _delete_bytes


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

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

import sys
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


from mutagen import _util

def _insert_bytes_no_mmap(fobj, size, offset, BUFFER_SIZE=2**16):
    """Insert size bytes of empty space starting at offset.

    fobj must be an open file object, open rb+ or
    equivalent. Mutagen tries to use mmap to resize the file, but
    falls back to a significantly slower method if mmap fails.
    """
    assert 0 < size
    assert 0 <= offset
    locked = False
    fobj.seek(0, 2)
    filesize = fobj.tell()
    movesize = filesize - offset
    fobj.write('\x00' * size)
    fobj.flush()
    try:
        locked = _util.lock(fobj)
        fobj.truncate(filesize)

        fobj.seek(0, 2)
        padsize = size
        # Don't generate an enormous string if we need to pad
        # the file out several megs.
        while padsize:
            addsize = min(BUFFER_SIZE, padsize)
            fobj.write("\x00" * addsize)
            padsize -= addsize

        fobj.seek(filesize, 0)
        while movesize:
            # At the start of this loop, fobj is pointing at the end
            # of the data we need to move, which is of movesize length.
            thismove = min(BUFFER_SIZE, movesize)
            # Seek back however much we're going to read this frame.
            fobj.seek(-thismove, 1)
            nextpos = fobj.tell()
            # Read it, so we're back at the end.
            data = fobj.read(thismove)
            # Seek back to where we need to write it.
            fobj.seek(-thismove + size, 1)
            # Write it.
            fobj.write(data)
            # And seek back to the end of the unmoved data.
            fobj.seek(nextpos)
            movesize -= thismove

        fobj.flush()
    finally:
        if locked:
            _util.unlock(fobj)

def _delete_bytes_no_mmap(fobj, size, offset, BUFFER_SIZE=2**16):
    """Delete size bytes of empty space starting at offset.

    fobj must be an open file object, open rb+ or
    equivalent. Mutagen tries to use mmap to resize the file, but
    falls back to a significantly slower method if mmap fails.
    """
    locked = False
    assert 0 < size
    assert 0 <= offset
    fobj.seek(0, 2)
    filesize = fobj.tell()
    movesize = filesize - offset - size
    assert 0 <= movesize
    try:
        if movesize > 0:
            fobj.flush()
            locked = _util.lock(fobj)
            fobj.seek(offset + size)
            buf = fobj.read(BUFFER_SIZE)
            while buf:
                fobj.seek(offset)
                fobj.write(buf)
                offset += len(buf)
                fobj.seek(offset + size)
                buf = fobj.read(BUFFER_SIZE)
        fobj.truncate(filesize - size)
        fobj.flush()
    finally:
        if locked:
            _util.unlock(fobj)

if sys.platform == 'win32':
    _util.insert_bytes = _insert_bytes_no_mmap
    _util.delete_bytes = _delete_bytes_no_mmap


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
    OggOpusFile,
    with_opus,
    )
register_format(FLACFile)
register_format(OggFLACFile)
register_format(OggSpeexFile)
register_format(OggVorbisFile)
if with_opus:
    register_format(OggOpusFile)
register_format(OggAudioFile)

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

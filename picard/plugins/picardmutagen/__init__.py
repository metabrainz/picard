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

import mutagen._util
mutagen._util.insert_bytes = _insert_bytes
mutagen._util.delete_bytes = _delete_bytes

from picard.api import IFileOpener
from picard.component import Component, implements
from picard.plugins.picardmutagen.asf import MutagenASFFile
from picard.plugins.picardmutagen.mp4 import MP4File
from picard.plugins.picardmutagen.id3 import (
    MP3File,
    TrueAudioFile,
    )
from picard.plugins.picardmutagen.apev2 import (
    MonkeysAudioFile,
    MusepackFile,
    OptimFROGFile,
    WavPackFile,
    )
from picard.plugins.picardmutagen.vorbis import (
    FLACFile,
    OggFLACFile,
    OggSpeexFile,
    OggTheoraFile,
    OggVorbisFile,
    )

class MutagenComponent(Component):

    implements(IFileOpener)

    __supported_formats = {
        ".mp3": (MP3File, "MPEG Layer-3"),
        ".mpc": (MusepackFile, "Musepack"),
        ".tta": (TrueAudioFile, "The True Audio"),
        ".wma": (MutagenASFFile, "Windows Media Audio"),
        ".wmv": (MutagenASFFile, "Windows Media Video"),
        ".asf": (MutagenASFFile, "ASF"),
        ".ofr": (OptimFROGFile, "OptimFROG Lossless Audio"),
        ".ofs": (OptimFROGFile, "OptimFROG DualStream Audio"),
        ".wv": (WavPackFile, "WavPack"),
        ".ape": (MonkeysAudioFile, "Monkey's Audio"),
        ".flac": (FLACFile, "FLAC"),
        ".oggflac": (OggFLACFile, "Ogg FLAC"),
        ".spx": (OggSpeexFile, "Ogg Speex"),
        ".ogg": (OggVorbisFile, "Ogg Vorbis"),
        ".m4a": (MP4File, "MP4 Audio"),
        ".m4p": (MP4File, "MP4 Audio (protected)"),
        ".m4b": (MP4File, "MP4 Audiobook"),
        ".mp4": (MP4File, "MP4"),
    }

    def get_supported_formats(self):
        return [(key, value[1]) for key, value in
                self.__supported_formats.items()]

    def can_open_file(self, filename):
        for ext in self.__supported_formats.keys():
            if filename.lower().endswith(ext):
                return True
        return False

    def open_file(self, filename):
        for ext in self.__supported_formats.keys():
            if filename.lower().endswith(ext):
                file = self.__supported_formats[ext][0](filename)
                file.read()
                return (file,)
        return None

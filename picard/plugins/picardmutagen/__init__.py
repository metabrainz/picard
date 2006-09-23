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

from picard.api import IFileOpener
from picard.component import Component, implements
from picard.plugins.picardmutagen.asf import MutagenASFFile
from picard.plugins.picardmutagen.mp3 import MutagenMP3File
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
        ".mp3": (MutagenMP3File, "MPEG Layer-3"),
        ".mpc": (MusepackFile, "Musepack"),
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
        ".oggx": (OggVorbisFile, "Ogg Vorbis"),
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


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

"""Collection of Mutagen-based metadata readers."""

from picard.component import Component, implements
from picard.api import IFileOpener
from picard.plugins.picardmutagen.asf import MutagenASFFile
from picard.plugins.picardmutagen.mp3 import MutagenMP3File
from picard.plugins.picardmutagen.vorbis import MutagenOggVorbisFile
from picard.plugins.picardmutagen.musepack import MutagenMusepackFile
from picard.plugins.picardmutagen.optimfrog import MutagenOptimFROGFile
from picard.plugins.picardmutagen.wavpack import MutagenWavPackFile
from picard.plugins.picardmutagen.mac import MutagenMACFile

class MutagenComponent(Component):

    implements(IFileOpener)

    # IFileOpener

    _supported_formats = {
        u".mp3": (MutagenMP3File, u"MPEG Layer-3"),
        u".ogg": (MutagenOggVorbisFile, u"Ogg Vorbis"),
        u".mpc": (MutagenMusepackFile, u"Musepack"),
        u".wma": (MutagenASFFile, u"Windows Media Audio"),
        u".wmv": (MutagenASFFile, u"Windows Media Video"),
        u".asf": (MutagenASFFile, u"ASF"),
        u".ofr": (MutagenOptimFROGFile, u"OptimFROG Lossless Audio"),
        u".ofs": (MutagenOptimFROGFile, u"OptimFROG DualStream Audio"),
        u".wv": (MutagenWavPackFile, u"WavPack"),
        u".ape": (MutagenMACFile, u"Monkey's Audio"),
    }

    def get_supported_formats(self):
        return [(key, value[1]) for key, value in self._supported_formats.items()]

    def can_open_file(self, filename):
        for ext in self._supported_formats.keys():
            if filename.lower().endswith(ext):
                return True
        return False

    def open_file(self, filename):
        for ext in self._supported_formats.keys():
            if filename.lower().endswith(ext):
                file = self._supported_formats[ext][0](filename)
                file.read()
                return (file,)
        return None


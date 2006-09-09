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

"""Mutagen-based MP3 metadata reader."""

from picard.component import Component, implements
from picard.api import IFileOpener
from picard.file import File
from picard.util import encode_filename
from mutagen.mp3 import MP3

class MutagenMP3File(File):

    def read(self):
        mp3file = MP3(encode_filename(self.filename))

        # Local metadata
        if "TIT2" in mp3file:
            self.localMetadata["title"] = unicode(mfile["TIT2"]) 
        if "TPE1" in mp3file:
            self.localMetadata["artist"] = unicode(mfile["TPE1"])
        if "TALB" in mp3file:
            self.localMetadata["album"] = unicode(mfile["TALB"])

        if "TRCK" in mp3file:
            text = unicode(mp3file["TRCK"])
            if "/" in text:
                trackNum, totalTracks = text.split("/")
                self.localMetadata["tracknumber"] = trackNum
                self.localMetadata["totaltracks"] = totalTracks
            else:
                self.localMetadata["tracknumber"] = text

        # Special tags
        self.localMetadata["~filename"] = self.baseFileName
        self.localMetadata["~#length"] = int(mfile.info.length * 1000)

        # Audio properties
        self.audioProperties.length = int(mfile.info.length * 1000)
        self.audioProperties.bitrate = mfile.info.bitrate / 1000.0

        self.metadata.copy(self.localMetadata)

    def save(self):
        mp3File = MP3(encode_filename(self.filename))
        mp3File.save()


class MutagenMP3Component(Component):

    implements(IFileOpener)

    # IFileOpener

    _supported_formats = {
        u".mp3": (MutagenMP3File, u"MPEG Layer-3"),
    }

    def get_supported_formats(self):
        return [(key, value[1]) for key, value in self._supported_formats.items()]

    def can_open_file(self, filename):
        for ext in self._supported_formats.keys():
            if filename.endswith(ext):
                return True
        return False

    def open_file(self, filename):
        for ext in self._supported_formats.keys():
            if filename.endswith(ext):
                file = self._supported_ormats[ext][0](filename)
                file.read()
                return (file,)
        return None


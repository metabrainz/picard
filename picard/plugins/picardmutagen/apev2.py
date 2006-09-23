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

import mutagen.apev2
import mutagen.musepack
import mutagen.wavpack
import mutagenext.optimfrog
from picard.file import File
from picard.util import encode_filename, sanitize_date

class APEv2File(File):
    """Generic APEv2-based file."""
    _File = None

    __translate = {
        "Album Artist": "albumartist",
    }

    def read(self):
        file = self._File(encode_filename(self.filename))
        if file.tags:
            for name, value in file.tags.items():
                value = ";".join(value)
                if name == "Year":
                    name = "date"
                    value = sanitize_date(value)
                elif name == "Track":
                    name = "tracknumber"
                    track = value.split("/")
                    if len(track) > 1:
                        self.metadata["totaltracks"] = track[1]
                        value = track[0]
                elif name in self.__translate:
                    name = self.__translate[name]
                else:
                    name = name.lower()
                self.metadata[name] = value
        self.metadata["~#length"] = int(file.info.length * 1000)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        """Save metadata to the file."""
        try:
            tags = mutagen.apev2.APEv2(encode_filename(self.filename))
        except mutagen.apev2.APENoHeaderError:
            tags = mutagen.apev2.APEv2()
        if self.config.setting["clear_existing_tags"]:
            tags.clear()
        for name, value in self.metadata.items():
            if name.startswith("~"):
                continue
            if name == "date":
                name = "Year"
            elif name == "totaltracks":
                continue
            elif name == "tracknumber":
                name = "Track"
                totaltracks = self.metadata["totaltracks"]
                if totaltracks:
                    value = "%s/%s" % (value, totaltracks)
            elif name == "albumartist":
                name = "Album Artist"
            else:
                name = name.title()
            tags[name] = value
        tags.save(encode_filename(self.filename))

class MusepackFile(APEv2File):
    """Musepack file."""
    _File = mutagen.musepack.Musepack

class WavPackFile(APEv2File):
    """WavPack file."""
    _File = mutagen.wavpack.WavPack

class OptimFROGFile(APEv2File):
    """OptimFROG file."""
    _File = mutagenext.optimfrog.OptimFROG

class MonkeysAudioFile(APEv2File):
    """Monkey's Audio file."""
    _File = mutagen.apev2.APEv2File


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

import mutagen.m4a
from picard.file import File
from picard.util import encode_filename

class MP4File(File):

    def read(self):
        file = mutagen.m4a.M4A(encode_filename(self.filename))

        def read_text(id, name):
            if id in file.tags:
                self.metadata[name] = file.tags[id]

        def read_free_text(desc, name):
            id = "----:com.apple.iTunes:%s" % desc
            if id in file.tags:
                self.metadata[name] = \
                    file.tags[id].strip("\x00").decode("utf-8")

        read_text("\xa9ART", "artist")
        read_text("\xa9nam", "title")
        read_text("\xa9alb", "album")
        read_text("\xa9wrt", "composer")
        read_text("aART", "albumartist")
        read_text("\xa9grp", "grouping")
        read_text("\xa9day", "date")
        read_text("\xa9gen", "genre")

        read_free_text("MusicBrainz Track Id", "musicbrainz_trackid")
        read_free_text("MusicBrainz Artist Id", "musicbrainz_artistid")
        read_free_text("MusicBrainz Album Id", "musicbrainz_albumid")
        read_free_text("MusicBrainz Album Artist Id",
                       "musicbrainz_albumartistid")
        read_free_text("MusicIP PUID", "musicip_puid")

        if "trkn" in file.tags:
            self.metadata["tracknumber"] = str(file.tags["trkn"][0])
            self.metadata["totaltracks"] = str(file.tags["trkn"][1])

        if "disk" in file.tags:
            self.metadata["discnumber"] = str(file.tags["disk"][0])
            self.metadata["totaldiscs"] = str(file.tags["disk"][1])

        if "covr" in file.tags:
            self.metadata["~artwork"] = [
                (None, file.tags["covr"])
            ]

        self.metadata["~#length"] = int(file.info.length * 1000)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        raise NotImplementedError


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

from mutagen.mp4 import MP4
from picard.file import File
from picard.util import encode_filename

class MP4File(File):

    def read(self):
        file = MP4(encode_filename(self.filename))

        def read_text(id, name):
            if id in file.tags:
                self.metadata[name] = file.tags[id][0]

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
            self.metadata["~artwork"] = []
            for data in file.tags["covr"]:
                self.metadata.add("~artwork", (None, data))

        self._info(file)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        file = MP4(encode_filename(self.filename))

        if self.config.setting["clear_existing_tags"]:
            file.tags.clear()

        def write_text(id, name):
            if name in self.metadata:
                file.tags[id] = self.metadata[name]

        def write_free_text(desc, name):
            if name in self.metadata:
                id = "----:com.apple.iTunes:%s" % desc
                file.tags[id] = self.metadata[name].encode("utf-8") + "\x00"

        write_text("\xa9ART", "artist")
        write_text("\xa9nam", "title")
        write_text("\xa9alb", "album")
        write_text("\xa9wrt", "composer")
        write_text("aART", "albumartist")
        write_text("\xa9grp", "grouping")
        write_text("\xa9day", "date")
        write_text("\xa9gen", "genre")

        write_free_text("MusicBrainz Track Id", "musicbrainz_trackid")
        write_free_text("MusicBrainz Artist Id", "musicbrainz_artistid")
        write_free_text("MusicBrainz Album Id", "musicbrainz_albumid")
        write_free_text("MusicBrainz Album Artist Id",
                        "musicbrainz_albumartistid")
        write_free_text("MusicIP PUID", "musicip_puid")

        if "tracknumber" in self.metadata:
            if "totaltracks" in self.metadata:
                file.tags["trkn"] = (int(self.metadata["tracknumber"]),
                                     int(self.metadata["totaltracks"]))
            else:
                file.tags["trkn"] = (int(self.metadata["tracknumber"]), 0)

        if "discnumber" in self.metadata:
            if "totaldiscs" in self.metadata:
                file.tags["disk"] = (int(self.metadata["discnumber"]),
                                     int(self.metadata["totaldiscs"]))
            else:
                file.tags["disk"] = (int(self.metadata["discnumber"]), 0)

        file.save()

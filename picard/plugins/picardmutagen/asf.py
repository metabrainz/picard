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

"""Mutagen-based ASF metadata reader."""

from picard.file import File
from picard.util import encode_filename
from picard.plugins.picardmutagen.mutagenext.asf import ASF

class MutagenASFFile(File):

    def read(self):

        file = ASF(encode_filename(self.filename))

        def read_text(wmname, name):
            if wmname in file.tags:
                self.metadata[name] = "; ".join(
                    unicode(a) for a in file.tags[wmname])

        read_text("Title", "title")
        read_text("Author", "artist")
        read_text("WM/AlbumArtist", "albumartist")
        read_text("WM/AlbumTitle", "album")
        read_text("WM/Track", "tracknumber")
        read_text("WM/TrackNumber", "tracknumber")
        read_text("WM/Year", "date")
        read_text("WM/Composer", "composer")
        read_text("WM/Conductor", "conductor")

        read_text("MusicBrainz/AlbumId", "musicbrainz_albumid")
        read_text("MusicBrainz/TrackId", "musicbrainz_trackid")
        read_text("MusicBrainz/ArtistId", "musicbrainz_artistid")

        self.metadata["~filename"] = self.base_filename
        self.metadata["~#length"] = int(file.info.length * 1000)
        self.metadata["~#bitrate"] = int(file.info.bitrate / 1000)

        self.orig_metadata.copy(self.metadata)

    def save(self):
        pass


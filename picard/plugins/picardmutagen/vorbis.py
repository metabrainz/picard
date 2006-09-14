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

"""Mutagen-based Ogg Vorbis metadata reader."""

from picard.file import File
from picard.util import encode_filename, sanitize_date
from mutagen.oggvorbis import OggVorbis

class MutagenOggVorbisFile(File):

    def read(self):
        """Load metadata from the file."""

        mfile = OggVorbis(encode_filename(self.filename))

        metadata = self.orig_metadata
        for name, values in mfile.items():
            value = ";".join(values)
            if name == "date":
                value = sanitize_date(value)
            metadata[name] = value

        metadata["~#length"] = int(mfile.info.length * 1000)
        metadata["~#bitrate"] = mfile.info.bitrate

        self.metadata.copy(self.orig_metadata)

    def save(self):
        """Save metadata to the file."""

        mfile = OggVorbis(encode_filename(self.filename))

        for name, value in self.metadata.items():
            if not name.startswith("~"):
                mfile[name] = value

        mfile.save()

        self.orig_metadata.copy(self.metadata)
        self.metadata.set_changed(False)


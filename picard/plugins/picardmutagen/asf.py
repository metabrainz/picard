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
        
        asf = ASF(encode_filename(self.filename))

        self.orig_metadata["~filename"] = self.base_filename
        self.orig_metadata["~#length"] = int(mp3file.info.length * 1000)
        self.orig_metadata["~#bitrate"] = int(mp3file.info.bitrate / 1000)

        self.metadata.copy(self.orig_metadata)

    def save(self):
        pass


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

"""Mutagen-based OptimFROG metadata reader."""

from picard.file import File
from picard.util import encode_filename
from mutagenext.optimfrog import OptimFROG
from mutagen.apev2 import APEv2
from picard.plugins.picardmutagen._apev2 import read_apev2_tags, \
                                                write_apev2_tags

class MutagenOptimFROGFile(File):

    def read(self):
        """Load metadata from the file."""

        ofrfile = OptimFROG(encode_filename(self.filename))

        metadata = self.orig_metadata
        read_apev2_tags(ofrfile.tags, metadata)

        metadata["~#length"] = int(ofrfile.info.length * 1000)
        metadata["~#bitrate"] = ofrfile.info.bitrate

        self.metadata.copy(self.orig_metadata)

    def save(self):
        apev2 = APEv2(encode_filename(self.filename))
        write_apev2_tags(apev2, self.metadata)
        apev2.save()


# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2018 Philipp Wolfer
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

from mutagen.aac import AAC
from mutagen.apev2 import (
    APENoHeaderError,
    APEv2,
    error as APEError,
)

from picard.formats.apev2 import APEv2File


class AACAPEv2(AAC):
    def load(self, filething):
        super().load(filething)
        try:
            self.tags = APEv2(filething)
        except APENoHeaderError:
            self.tags = None

    def add_tags(self):
        if self.tags is None:
            self.tags = APEv2()
        else:
            raise APEError("%r already has tags: %r" % (self, self.tags))


class AACFile(APEv2File):
    EXTENSIONS = [".aac"]
    NAME = "AAC"
    _File = AACAPEv2

    def _info(self, metadata, file):
        super()._info(metadata, file)
        if file.tags:
            metadata['~format'] = "%s (APEv2)" % self.NAME

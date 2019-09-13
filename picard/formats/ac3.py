# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2019 Philipp Wolfer
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

from picard.formats.apev2 import APEv2File

from .mutagenext import ac3


class AC3File(APEv2File):
    EXTENSIONS = [".ac3"]
    NAME = "AC3"
    _File = ac3.AC3APEv2

    def _info(self, metadata, file):
        super()._info(metadata, file)
        if file.tags:
            metadata['~format'] = "%s (APEv2)" % self.NAME

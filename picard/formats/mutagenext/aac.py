# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2019 Philipp Wolfer
# Copyright (C) 2020-2021 Laurent Monin
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


from mutagen._util import loadfile
from mutagen.aac import AAC

from .apev2 import (
    add_apev2_tags,
    load_apev2_tags,
)


class AACAPEv2(AAC):
    """AAC file with APEv2 tags.
    """
    @loadfile()
    def load(self, filething):
        super().load(filething)
        load_apev2_tags(self, filething)

    def add_tags(self):
        add_apev2_tags(self)

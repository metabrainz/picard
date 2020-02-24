# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2018-2019 Philipp Wolfer
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
from mutagen.apev2 import (
    APENoHeaderError,
    APEv2,
    _APEv2Data,
    error as APEError,
)


class AACAPEv2(AAC):
    """AAC file with APEv2 tags.
    """
    @loadfile()
    def load(self, filething):
        super().load(filething)
        try:
            self.tags = APEv2(filething)
            # Correct the calculated length
            if not hasattr(self.info, 'bitrate') or self.info.bitrate == 0:
                return
            ape_data = _APEv2Data(filething.fileobj)
            if ape_data.size is not None:
                # Remove APEv2 data length from calculated track length
                extra_length = (8.0 * ape_data.size) / self.info.bitrate
                self.info.length = max(self.info.length - extra_length, 0.001)
        except APENoHeaderError:
            self.tags = None

    def add_tags(self):
        if self.tags is None:
            self.tags = APEv2()
        else:
            raise APEError("%r already has tags: %r" % (self, self.tags))

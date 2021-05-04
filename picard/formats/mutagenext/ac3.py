# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019 Philipp Wolfer
# Copyright (C) 2020 Laurent Monin
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


from mutagen._file import FileType
from mutagen._util import (
    MutagenError,
    loadfile,
)
from mutagen.apev2 import (
    APENoHeaderError,
    APEv2,
    _APEv2Data,
    error as APEError,
)


try:
    from mutagen.ac3 import AC3
    native_ac3 = True
except ImportError:
    native_ac3 = False

    class AC3Error(MutagenError):
        pass

    class AC3Info(object):

        """AC3 stream information.

        Attributes:
          (none at the moment)
        """

        def __init__(self, fileobj):
            header = fileobj.read(4)
            if len(header) != 4 or not header.startswith(b"\x0b\x77"):
                raise AC3Error("not a AC3 file")

        @staticmethod
        def pprint():
            return "AC3"

    class AC3(FileType):
        @loadfile()
        def load(self, filething):
            self.info = AC3Info(filething.fileobj)

        @staticmethod
        def score(filename, fileobj, header):
            return header.startswith(b"\x0b\x77") + (filename.endswith(".ac3")
                or filename.endswith(".eac3"))


class AC3APEv2(AC3):
    @loadfile()
    def load(self, filething):
        super().load(filething)
        try:
            self.tags = APEv2(filething.fileobj)
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

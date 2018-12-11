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

from mutagen.smf import SMF

from picard import log
from picard.file import File
from picard.metadata import Metadata
from picard.util import encode_filename


class MIDIFile(File):
    EXTENSIONS = [".mid", ".kar"]
    NAME = "Standard MIDI File"
    _File = SMF

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        metadata = Metadata()
        file = self._File(encode_filename(filename))
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)

    def _info(self, metadata, file):
        super()._info(metadata, file)
        # mutagen.File.filename can be either a bytes or str object
        filename = file.filename
        if isinstance(filename, bytes):
            filename = filename.decode()
        if filename.lower().endswith(".kar"):
            metadata['~format'] = "Standard MIDI File (Karaoke File)"

    @classmethod
    def supports_tag(cls, name):
        return False

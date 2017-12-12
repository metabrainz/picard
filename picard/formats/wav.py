# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
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

import wave
from picard import log
from picard.file import File
from picard.metadata import Metadata


class WAVFile(File):
    EXTENSIONS = [".wav"]
    NAME = "Microsoft WAVE"
    _File = None

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        f = wave.open(filename, "rb")
        metadata = Metadata()
        metadata['~channels'] = f.getnchannels()
        metadata['~bits_per_sample'] = f.getsampwidth() * 8
        metadata['~sample_rate'] = f.getframerate()
        metadata.length = 1000 * f.getnframes() // f.getframerate()
        metadata['~format'] = 'Microsoft WAVE'
        self._add_path_to_metadata(metadata)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)

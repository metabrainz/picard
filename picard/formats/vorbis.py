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

import mutagen.flac
import mutagen.oggflac
import mutagen.oggspeex
import mutagen.oggtheora
import mutagen.oggvorbis
from picard.file import File
from picard.util import encode_filename, sanitize_date

class VCommentFile(File):
    """Generic VComment-based file."""
    _File = None

    def read(self):
        file = self._File(encode_filename(self.filename))
        for name, values in file.tags.items():
            value = ";".join(values)
            if name == "date":
                value = sanitize_date(value)
            self.metadata[name] = value
        self.metadata["~#length"] = int(file.info.length * 1000)
        self._info(file)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        """Save metadata to the file."""
        file = self._File(encode_filename(self.filename))
        if self.config.setting["clear_existing_tags"]:
            file.tags.clear()
        for name, value in self.metadata.items():
            if not name.startswith("~"):
                file.tags[name] = value
        file.save()

class FLACFile(VCommentFile):
    """FLAC file."""
    _File = mutagen.flac.FLAC
    def _info(self, file):
        super(FLACFile, self)._info(file)
        self.metadata['~format'] = 'FLAC'

class OggFLACFile(VCommentFile):
    """FLAC file."""
    _File = mutagen.oggflac.OggFLAC
    def _info(self, file):
        super(OggFLACFile, self)._info(file)
        self.metadata['~format'] = 'Ogg FLAC'

class OggSpeexFile(VCommentFile):
    """Ogg Speex file."""
    _File = mutagen.oggspeex.OggSpeex
    def _info(self, file):
        super(OggSpeexFile, self)._info(file)
        self.metadata['~format'] = 'Ogg Speex'

class OggTheoraFile(VCommentFile):
    """Ogg Theora file."""
    _File = mutagen.oggtheora.OggTheora
    def _info(self, file):
        super(OggTheoraFile, self)._info(file)
        self.metadata['~format'] = 'Ogg Theora'

class OggVorbisFile(VCommentFile):
    """Ogg Vorbis file."""
    _File = mutagen.oggvorbis.OggVorbis
    def _info(self, file):
        super(OggVorbisFile, self)._info(file)
        self.metadata['~format'] = 'Ogg Vorbis'

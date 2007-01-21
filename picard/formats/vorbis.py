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
        for origname, values in file.tags.items():
            for value in values:
                name = origname
                if name == "date":
                    value = sanitize_date(value)
                elif name == 'performer' and value.endswith(')'):
                    start = value.rfind(' (')
                    if start > 0:
                        name += ':' + value[start + 2:-1]
                        value = value[:start]
                self.metadata.add(name, value)
        self.metadata["~#length"] = int(file.info.length * 1000)
        self._info(file)
        self.orig_metadata.copy(self.metadata)

    def save(self):
        """Save metadata to the file."""
        file = self._File(encode_filename(self.filename))
        if self.config.setting["clear_existing_tags"]:
            file.tags.clear()
        for name, value in self.metadata.items():
            if name.startswith("~"):
                continue
            # "performer:Piano=Joe Barr" => "performer=Joe Barr (Piano)"
            if name.startswith('performer:') or name.startswith('comment:'):
                name, desc = name.split(':', 1)
                if desc:
                    value += ' (%s)' % desc
            file.tags.append((name.lower(), value))
        file.save()

class FLACFile(VCommentFile):
    """FLAC file."""
    EXTENSIONS = [".flac"]
    NAME = "FLAC"
    _File = mutagen.flac.FLAC
    def _info(self, file):
        super(FLACFile, self)._info(file)
        self.metadata['~format'] = self.NAME

class OggFLACFile(VCommentFile):
    """FLAC file."""
    EXTENSIONS = [".oggflac"]
    NAME = "Ogg FLAC"
    _File = mutagen.oggflac.OggFLAC
    def _info(self, file):
        super(OggFLACFile, self)._info(file)
        self.metadata['~format'] = self.NAME

class OggSpeexFile(VCommentFile):
    """Ogg Speex file."""
    EXTENSIONS = [".spx"]
    NAME = "Speex"
    _File = mutagen.oggspeex.OggSpeex
    def _info(self, file):
        super(OggSpeexFile, self)._info(file)
        self.metadata['~format'] = self.NAME

class OggTheoraFile(VCommentFile):
    """Ogg Theora file."""
    EXTENSIONS = [".oggtheora"]
    NAME = "Ogg Theora"
    _File = mutagen.oggtheora.OggTheora
    def _info(self, file):
        super(OggTheoraFile, self)._info(file)
        self.metadata['~format'] = self.NAME

class OggVorbisFile(VCommentFile):
    """Ogg Vorbis file."""
    EXTENSIONS = [".ogg"]
    NAME = "Ogg Vorbis"
    _File = mutagen.oggvorbis.OggVorbis
    def _info(self, file):
        super(OggVorbisFile, self)._info(file)
        self.metadata['~format'] = self.NAME

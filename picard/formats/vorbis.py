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
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date

class VCommentFile(File):
    """Generic VComment-based file."""
    _File = None

    def _load(self):
        file = self._File(encode_filename(self.filename))
        metadata = Metadata()
        for origname, values in file.tags.items():
            for value in values:
                name = origname
                if name == "date":
                    # YYYY-00-00 => YYYY
                    value = sanitize_date(value)
                elif name == 'performer' and value.endswith(')'):
                    # transform "performer=Joe Barr (Piano)" to "performer:Piano=Joe Barr"
                    start = value.rfind(' (')
                    if start > 0:
                        name += ':' + value[start + 2:-1]
                        value = value[:start]
                metadata.add(name, value)
        self.metadata.update(metadata)
        self.metadata["~#length"] = int(file.info.length * 1000)
        self._info(file)

    def _save(self):
        """Save metadata to the file."""
        file = self._File(encode_filename(self.filename))
        if self.config.setting["clear_existing_tags"]:
            file.tags.clear()
        tags = {}
        for name, value in self.metadata.items():
            # don't save private tags
            if name.startswith("~"):
                continue
            if name == "date":
                # YYYY-00-00 => YYYY
                value = sanitize_date(value)
            elif name.startswith('performer:') or name.startswith('comment:'):
                # transform "performer:Piano=Joe Barr" to "performer=Joe Barr (Piano)"
                name, desc = name.split(':', 1)
                if desc:
                    value += ' (%s)' % desc
            tags.setdefault(name.upper().encode('utf-8'), []).append(value)
        file.tags.update(tags)
        kwargs = {}
        if self._File == mutagen.flac.FLAC and self.config.setting["remove_id3_from_flac"]:
            kwargs["deleteid3"] = True
        try:
            file.save(**kwargs)
        except TypeError:
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

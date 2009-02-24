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

import base64
import mutagen.flac
import mutagen.ogg
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

    def _load(self, filename):
        self.log.debug("Loading file %r", filename)
        file = self._File(encode_filename(filename))
        file.tags = file.tags or {}
        metadata = Metadata()
        for origname, values in file.tags.items():
            for value in values:
                name = origname
                if name == "date":
                    # YYYY-00-00 => YYYY
                    value = sanitize_date(value)
                elif name == 'performer':
                    # transform "performer=Joe Barr (Piano)" to "performer:Piano=Joe Barr"
                    name += ':'
                    if value.endswith(')'):
                        start = value.rfind(' (')
                        if start > 0:
                            name += value[start + 2:-1]
                            value = value[:start]
                elif name.startswith('rating:'):
                    name, email = name.split(':', 1)
                    if email != self.config.setting['rating_user_email']:
                        continue
                    name = '~%s' % name
                    value = unicode(int(round((float(value) * (self.config.setting['rating_steps'] - 1)))))
                elif name == "fingerprint" and value.startswith("MusicMagic Fingerprint"):
                    name = "musicip_fingerprint"
                    value = value[22:]
                elif name == "tracktotal" and "totaltracks" not in file.tags:
                    name = "totaltracks"
                metadata.add(name, value)
        if self._File == mutagen.flac.FLAC:
            for image in file.pictures:
                metadata.add_image(image.mime, image.data)
        try:
            for index, data in enumerate(file["COVERART"]):
                metadata.add_image(file["COVERARTMIME"][index], base64.standard_b64decode(data))
        except KeyError:
            pass
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata, settings):
        """Save metadata to the file."""
        self.log.debug("Saving file %r", filename)
        file = self._File(encode_filename(filename))
        if file.tags is None:
            file.add_tags()
        if settings["clear_existing_tags"]:
            file.tags.clear()
        if self._File == mutagen.flac.FLAC and (
            settings["clear_existing_tags"] or
            (settings['save_images_to_tags'] and metadata.images)):
            file.clear_pictures()
        tags = {}
        for name, value in metadata.items():
            if name == '~rating':
                # Save rating according to http://code.google.com/p/quodlibet/wiki/Specs_VorbisComments
                name = 'rating:%s' % settings['rating_user_email']
                value = unicode(float(value) / (settings['rating_steps'] - 1))
            # don't save private tags
            elif name.startswith("~"):
                continue
            if name.startswith('lyrics:'):
                name = 'lyrics'
            elif name == "date":
                # YYYY-00-00 => YYYY
                value = sanitize_date(value)
            elif name.startswith('performer:') or name.startswith('comment:'):
                # transform "performer:Piano=Joe Barr" to "performer=Joe Barr (Piano)"
                name, desc = name.split(':', 1)
                if desc:
                    value += ' (%s)' % desc
            elif name == "musicip_fingerprint":
                name = "fingerprint"
                value = "MusicMagic Fingerprint%s" % value
            tags.setdefault(name.upper().encode('utf-8'), []).append(value)
        if settings['save_images_to_tags']:
            for mime, data in metadata.images:
                if self._File == mutagen.flac.FLAC:
                   image = mutagen.flac.Picture()
                   image.type = 3 # Cover image
                   image.data = data
                   image.mime = mime
                   file.add_picture(image)
                else:
                   tags.setdefault("COVERART", []).append(base64.standard_b64encode(data))
                   tags.setdefault("COVERARTMIME", []).append(mime)
        file.tags.update(tags)
        kwargs = {}
        if self._File == mutagen.flac.FLAC and settings["remove_id3_from_flac"]:
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
    def _info(self, metadata, file):
        super(FLACFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

class OggFLACFile(VCommentFile):
    """FLAC file."""
    EXTENSIONS = [".oggflac"]
    NAME = "Ogg FLAC"
    _File = mutagen.oggflac.OggFLAC
    def _info(self, metadata, file):
        super(OggFLACFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

class OggSpeexFile(VCommentFile):
    """Ogg Speex file."""
    EXTENSIONS = [".spx"]
    NAME = "Speex"
    _File = mutagen.oggspeex.OggSpeex
    def _info(self, metadata, file):
        super(OggSpeexFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

class OggTheoraFile(VCommentFile):
    """Ogg Theora file."""
    EXTENSIONS = [".oggtheora"]
    NAME = "Ogg Theora"
    _File = mutagen.oggtheora.OggTheora
    def _info(self, metadata, file):
        super(OggTheoraFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

class OggVorbisFile(VCommentFile):
    """Ogg Vorbis file."""
    EXTENSIONS = [".ogg"]
    NAME = "Ogg Vorbis"
    _File = mutagen.oggvorbis.OggVorbis
    def _info(self, metadata, file):
        super(OggVorbisFile, self)._info(metadata, file)
        metadata['~format'] = self.NAME

def OggAudioFile(filename):
    """Generic Ogg audio file."""
    options = [OggFLACFile, OggSpeexFile, OggVorbisFile]
    fileobj = file(filename, "rb")
    results = []
    try:
        header = fileobj.read(128)
        results = [
            (option._File.score(filename, fileobj, header), option.__name__, option)
            for option in options]
    finally:
        fileobj.close()
    results.sort()
    if not results or results[-1][0] <= 0:
        raise mutagen.ogg.error("unknown Ogg audio format")
    return results[-1][2](filename)

OggAudioFile.EXTENSIONS = [".oga"]
OggAudioFile.NAME = "Ogg Audio"

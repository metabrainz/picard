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
try:
    from mutagen.oggopus import OggOpus
    with_opus = True
except ImportError:
    OggOpus = None
    with_opus = False
from picard.file import File
from picard.formats.id3 import ID3_IMAGE_TYPE_MAP, ID3_REVERSE_IMAGE_TYPE_MAP
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
                if name == "date" or name == "originaldate":
                    # YYYY-00-00 => YYYY
                    value = sanitize_date(value)
                elif name == 'performer' or name == 'comment':
                    # transform "performer=Joe Barr (Piano)" to "performer:Piano=Joe Barr"
                    name += ':'
                    if value.endswith(')'):
                        start = len(value) - 2
                        count = 1
                        while count > 0 and start > 0:
                            if value[start] == ')':
                                count += 1
                            elif value[start] == '(':
                                count -= 1
                            start -= 1
                        if start > 0:
                            name += value[start + 2:-1]
                            value = value[:start]
                elif name.startswith('rating'):
                    try: name, email = name.split(':', 1)
                    except ValueError: email = ''
                    if email != self.config.setting['rating_user_email']:
                        continue
                    name = '~rating'
                    value = unicode(int(round((float(value) * (self.config.setting['rating_steps'] - 1)))))
                elif name == "fingerprint" and value.startswith("MusicMagic Fingerprint"):
                    name = "musicip_fingerprint"
                    value = value[22:]
                elif name == "tracktotal":
                    if "totaltracks" in file.tags:
                        continue
                    name = "totaltracks"
                elif name == "disctotal":
                    if "totaldiscs" in file.tags:
                        continue
                    name = "totaldiscs"
                elif name == "metadata_block_picture":
                    image = mutagen.flac.Picture(base64.standard_b64decode(value))
                    imagetype = ID3_REVERSE_IMAGE_TYPE_MAP.get(image.type, "other")
                    metadata.add_image(image.mime, image.data,
                                       description=image.desc,
                                       types=[imagetype],
                                       source="file")
                    continue
                metadata.add(name, value)
        if self._File == mutagen.flac.FLAC:
            for image in file.pictures:
                imagetype = ID3_REVERSE_IMAGE_TYPE_MAP.get(image.type, "other")
                metadata.add_image(image.mime, image.data,
                                   description=image.desc, types=[imagetype],
                                   source="file")
        # Read the unofficial COVERART tags, for backward compatibillity only
        if not "metadata_block_picture" in file.tags:
            try:
                for index, data in enumerate(file["COVERART"]):
                    metadata.add_image(file["COVERARTMIME"][index],
                                       base64.standard_b64decode(data),
                                       source="file")
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
        embeddable_images = metadata.embeddable_images()
        if self._File == mutagen.flac.FLAC and (settings["clear_existing_tags"]
                                                or embeddable_images):
            file.clear_pictures()
        tags = {}
        for name, value in metadata.items():
            if name == '~rating':
                # Save rating according to http://code.google.com/p/quodlibet/wiki/Specs_VorbisComments
                if settings['rating_user_email']:
                    name = 'rating:%s' % settings['rating_user_email']
                else:
                    name = 'rating'
                value = unicode(float(value) / (settings['rating_steps'] - 1))
            # don't save private tags
            elif name.startswith("~"):
                continue
            if name.startswith('lyrics:'):
                name = 'lyrics'
            elif name == "date" or name == "originaldate":
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

        if "totaltracks" in metadata:
            tags.setdefault(u"TRACKTOTAL", []).append(metadata["totaltracks"])
        if "totaldiscs" in metadata:
            tags.setdefault(u"DISCTOTAL", []).append(metadata["totaldiscs"])

        for image in embeddable_images:
            picture = mutagen.flac.Picture()
            picture.data = image.data
            picture.mime = image.mime
            picture.desc = image.description
            picture.type = ID3_IMAGE_TYPE_MAP.get(image.main_type, 0)
            if self._File == mutagen.flac.FLAC:
                file.add_picture(picture)
            else:
                tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(
                    base64.standard_b64encode(picture.write()))
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

class OggOpusFile(VCommentFile):
    """Ogg Opus file."""
    EXTENSIONS = [".opus"]
    NAME = "Ogg Opus"
    _File = OggOpus
    def _info(self, metadata, file):
        super(OggOpusFile, self)._info(metadata, file)
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

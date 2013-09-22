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
from picard import config, log
from picard.file import File
from picard.formats.id3 import image_type_from_id3_num, image_type_as_id3_num
from picard.metadata import Metadata, save_this_image_to_tags
from picard.util import encode_filename, sanitize_date


class VCommentFile(File):

    """Generic VComment-based file."""
    _File = None

    __translate = {
        "musicbrainz_trackid": "musicbrainz_recordingid",
        "musicbrainz_releasetrackid": "musicbrainz_trackid",
    }
    __rtranslate = dict([(v, k) for k, v in __translate.iteritems()])

    def _load(self, filename):
        log.debug("Loading file %r", filename)
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
                    try:
                        name, email = name.split(':', 1)
                    except ValueError:
                        email = ''
                    if email != config.setting['rating_user_email']:
                        continue
                    name = '~rating'
                    value = unicode(int(round((float(value) * (config.setting['rating_steps'] - 1)))))
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
                    extras = {
                        'desc': image.desc,
                        'type': image_type_from_id3_num(image.type)
                    }
                    metadata.add_image(image.mime, image.data, extras=extras)
                    continue
                elif name in self.__translate:
                    name = self.__translate[name]
                metadata.add(name, value)
        if self._File == mutagen.flac.FLAC:
            for image in file.pictures:
                extras = {
                    'desc': image.desc,
                    'type': image_type_from_id3_num(image.type)
                }
                metadata.add_image(image.mime, image.data, extras=extras)
        # Read the unofficial COVERART tags, for backward compatibillity only
        if not "metadata_block_picture" in file.tags:
            try:
                for index, data in enumerate(file["COVERART"]):
                    metadata.add_image(file["COVERARTMIME"][index],
                                       base64.standard_b64decode(data)
                                      )
            except KeyError:
                pass
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file %r", filename)
        file = self._File(encode_filename(filename))
        if file.tags is None:
            file.add_tags()
        if config.setting["clear_existing_tags"]:
            file.tags.clear()
        if self._File == mutagen.flac.FLAC and (
            config.setting["clear_existing_tags"] or
            (config.setting['save_images_to_tags'] and metadata.images)):
            file.clear_pictures()
        tags = {}
        for name, value in metadata.items():
            if name == '~rating':
                # Save rating according to http://code.google.com/p/quodlibet/wiki/Specs_VorbisComments
                if config.setting['rating_user_email']:
                    name = 'rating:%s' % config.setting['rating_user_email']
                else:
                    name = 'rating'
                value = unicode(float(value) / (config.setting['rating_steps'] - 1))
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
            elif name in self.__rtranslate:
                name = self.__rtranslate[name]
            tags.setdefault(name.upper().encode('utf-8'), []).append(value)

        if "totaltracks" in metadata:
            tags.setdefault(u"TRACKTOTAL", []).append(metadata["totaltracks"])
        if "totaldiscs" in metadata:
            tags.setdefault(u"DISCTOTAL", []).append(metadata["totaldiscs"])

        if config.setting['save_images_to_tags']:
            for image in metadata.images:
                if not save_this_image_to_tags(image):
                    continue
                picture = mutagen.flac.Picture()
                picture.data = image["data"]
                picture.mime = image["mime"]
                picture.desc = image['desc']
                picture.type = image_type_as_id3_num(image['type'])
                if self._File == mutagen.flac.FLAC:
                    file.add_picture(picture)
                else:
                    tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(
                        base64.standard_b64encode(picture.write()))
        file.tags.update(tags)
        kwargs = {}
        if self._File == mutagen.flac.FLAC and config.setting["remove_id3_from_flac"]:
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

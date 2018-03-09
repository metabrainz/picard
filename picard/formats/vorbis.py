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
import re
import mutagen.flac
import mutagen.ogg
import mutagen.oggflac
import mutagen.oggspeex
import mutagen.oggtheora
import mutagen.oggvorbis
import mutagen.oggopus

from picard import config, log
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.file import File
from picard.formats.id3 import types_from_id3, image_type_as_id3_num
from picard.metadata import Metadata
from picard.util import encode_filename, sanitize_date
from picard.formats import guess_format

class VCommentFile(File):

    """Generic VComment-based file."""
    _File = None

    __translate = {
        "musicbrainz_trackid": "musicbrainz_recordingid",
        "musicbrainz_releasetrackid": "musicbrainz_trackid",
    }
    __rtranslate = dict([(v, k) for k, v in __translate.items()])

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
                    value = string_(int(round((float(value) * (config.setting['rating_steps'] - 1)))))
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
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            types=types_from_id3(image.type),
                            comment=image.desc,
                            support_types=True,
                            data=image.data,
                        )
                    except CoverArtImageError as e:
                        log.error('Cannot load image from %r: %s' % (filename, e))
                    else:
                        metadata.append_image(coverartimage)

                    continue
                elif name in self.__translate:
                    name = self.__translate[name]
                metadata.add(name, value)
        if self._File == mutagen.flac.FLAC:
            for image in file.pictures:
                try:
                    coverartimage = TagCoverArtImage(
                        file=filename,
                        tag='FLAC/PICTURE',
                        types=types_from_id3(image.type),
                        comment=image.desc,
                        support_types=True,
                        data=image.data,
                    )
                except CoverArtImageError as e:
                    log.error('Cannot load image from %r: %s' % (filename, e))
                else:
                    metadata.append_image(coverartimage)

        # Read the unofficial COVERART tags, for backward compatibility only
        if "metadata_block_picture" not in file.tags:
            try:
                for data in file["COVERART"]:
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag='COVERART',
                            data=base64.standard_b64decode(data)
                        )
                    except CoverArtImageError as e:
                        log.error('Cannot load image from %r: %s' % (filename, e))
                    else:
                        metadata.append_image(coverartimage)
            except KeyError:
                pass
        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        """Save metadata to the file."""
        log.debug("Saving file %r", filename)
        is_flac = self._File == mutagen.flac.FLAC
        file = self._File(encode_filename(filename))
        if file.tags is None:
            file.add_tags()
        if config.setting["clear_existing_tags"]:
            file.tags.clear()
        if (is_flac and (config.setting["clear_existing_tags"] or
                         metadata.images_to_be_saved_to_tags)):
            file.clear_pictures()
        tags = {}
        for name, value in metadata.items():
            if name == '~rating':
                # Save rating according to http://code.google.com/p/quodlibet/wiki/Specs_VorbisComments
                if config.setting['rating_user_email']:
                    name = 'rating:%s' % config.setting['rating_user_email']
                else:
                    name = 'rating'
                value = string_(float(value) / (config.setting['rating_steps'] - 1))
            # don't save private tags
            elif name.startswith("~"):
                continue
            elif name.startswith('lyrics:'):
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
            tags.setdefault(name.upper(), []).append(value)

        if "totaltracks" in metadata:
            tags.setdefault("TRACKTOTAL", []).append(metadata["totaltracks"])
        if "totaldiscs" in metadata:
            tags.setdefault("DISCTOTAL", []).append(metadata["totaldiscs"])

        for image in metadata.images_to_be_saved_to_tags:
            picture = mutagen.flac.Picture()
            picture.data = image.data
            picture.mime = image.mimetype
            picture.desc = image.comment
            picture.type = image_type_as_id3_num(image.maintype)
            if self._File == mutagen.flac.FLAC:
                file.add_picture(picture)
            else:
                tags.setdefault("METADATA_BLOCK_PICTURE", []).append(
                    base64.b64encode(picture.write()).decode('ascii'))

        file.tags.update(tags)

        self._remove_deleted_tags(metadata, file.tags)

        kwargs = {}
        if is_flac and config.setting["remove_id3_from_flac"]:
            kwargs["deleteid3"] = True
        try:
            file.save(**kwargs)
        except TypeError:
            file.save()

    def _remove_deleted_tags(self, metadata, tags):
        """Remove the tags from the file that were deleted in the UI"""
        for tag in metadata.deleted_tags:
            real_name = self._get_tag_name(tag)
            if real_name and real_name in tags:
                if real_name in ('performer', 'comment'):
                    tag_type = r"\(%s\)" % tag.split(':', 1)[1]
                    for item in tags.get(real_name):
                        if re.search(tag_type, item):
                            tags.get(real_name).remove(item)
                else:
                    if tag in ('totaldiscs', 'totaltracks'):
                        # both tag and real_name are to be deleted in this case
                        del tags[tag]
                    del tags[real_name]

    def _get_tag_name(self, name):
        if name == '~rating':
            if config.setting['rating_user_email']:
                return 'rating:%s' % config.setting['rating_user_email']
            else:
                return 'rating'
        elif name.startswith("~"):
            return None
        elif name.startswith('lyrics:'):
            return 'lyrics'
        elif name.startswith('performer:') or name.startswith('comment:'):
            return name.split(':', 1)[0]
        elif name == 'musicip_fingerprint':
            return 'fingerprint'
        elif name == 'totaltracks':
            return 'tracktotal'
        elif name == 'totaldiscs':
            return 'disctotal'
        elif name in self.__rtranslate:
            return self.__rtranslate[name]
        else:
            return name

    @classmethod
    def supports_tag(cls, name):
        return bool(name)


class FLACFile(VCommentFile):

    """FLAC file."""
    EXTENSIONS = [".flac"]
    NAME = "FLAC"
    _File = mutagen.flac.FLAC

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


class OggFLACFile(VCommentFile):

    """FLAC file."""
    EXTENSIONS = [".oggflac"]
    NAME = "Ogg FLAC"
    _File = mutagen.oggflac.OggFLAC

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


class OggSpeexFile(VCommentFile):

    """Ogg Speex file."""
    EXTENSIONS = [".spx"]
    NAME = "Speex"
    _File = mutagen.oggspeex.OggSpeex

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


class OggTheoraFile(VCommentFile):

    """Ogg Theora file."""
    EXTENSIONS = [".oggtheora"]
    NAME = "Ogg Theora"
    _File = mutagen.oggtheora.OggTheora

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


class OggVorbisFile(VCommentFile):

    """Ogg Vorbis file."""
    EXTENSIONS = [".ogg"]
    NAME = "Ogg Vorbis"
    _File = mutagen.oggvorbis.OggVorbis

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


class OggOpusFile(VCommentFile):

    """Ogg Opus file."""
    EXTENSIONS = [".opus"]
    NAME = "Ogg Opus"
    _File = mutagen.oggopus.OggOpus

    def _info(self, metadata, file):
        super()._info(metadata, file)
        metadata['~format'] = self.NAME


def OggAudioFile(filename):
    """Generic Ogg audio file."""
    options = [OggFLACFile, OggSpeexFile, OggVorbisFile]
    return guess_format(filename, options)

OggAudioFile.EXTENSIONS = [".oga"]
OggAudioFile.NAME = "Ogg Audio"


def OggVideoFile(filename):
    """Generic Ogg video file."""
    options = [OggTheoraFile]
    return guess_format(filename, options)


OggVideoFile.EXTENSIONS = [".ogv"]
OggVideoFile.NAME = "Ogg Video"

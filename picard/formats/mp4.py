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

from mutagen.mp4 import (
    MP4,
    MP4Cover,
)

from picard import (
    config,
    log,
)
from picard.coverart.image import (
    CoverArtImageError,
    TagCoverArtImage,
)
from picard.file import File
from picard.metadata import Metadata
from picard.util import encode_filename


class MP4File(File):
    EXTENSIONS = [".m4a", ".m4b", ".m4p", ".m4v", ".mp4"]
    NAME = "MPEG-4 Audio"
    _File = MP4

    __text_tags = {
        "\xa9ART": "artist",
        "\xa9nam": "title",
        "\xa9alb": "album",
        "\xa9wrt": "composer",
        "aART": "albumartist",
        "\xa9grp": "grouping",
        "\xa9day": "date",
        "\xa9gen": "genre",
        "\xa9lyr": "lyrics",
        "\xa9cmt": "comment:",
        "\xa9too": "encodedby",
        "cprt": "copyright",
        "soal": "albumsort",
        "soaa": "albumartistsort",
        "soar": "artistsort",
        "sonm": "titlesort",
        "soco": "composersort",
        "sosn": "showsort",
        "tvsh": "show",
        "purl": "podcasturl",
        "\xa9mvn": "movement",
        "\xa9wrk": "work",
    }
    __r_text_tags = dict([(v, k) for k, v in __text_tags.items()])

    __bool_tags = {
        "pcst": "podcast",
        "cpil": "compilation",
        "pgap": "gapless",
    }
    __r_bool_tags = dict([(v, k) for k, v in __bool_tags.items()])

    __int_tags = {
        "tmpo": "bpm",
        "\xa9mvi": "movementnumber",
        "\xa9mvc": "movementtotal",
        "shwm": "showmovement",
    }
    __r_int_tags = dict([(v, k) for k, v in __int_tags.items()])

    __freeform_tags = {
        "----:com.apple.iTunes:MusicBrainz Track Id": "musicbrainz_recordingid",
        "----:com.apple.iTunes:MusicBrainz Artist Id": "musicbrainz_artistid",
        "----:com.apple.iTunes:MusicBrainz Album Id": "musicbrainz_albumid",
        "----:com.apple.iTunes:MusicBrainz Album Artist Id": "musicbrainz_albumartistid",
        "----:com.apple.iTunes:MusicIP PUID": "musicip_puid",
        "----:com.apple.iTunes:MusicBrainz Album Status": "releasestatus",
        "----:com.apple.iTunes:MusicBrainz Album Release Country": "releasecountry",
        "----:com.apple.iTunes:MusicBrainz Album Type": "releasetype",
        "----:com.apple.iTunes:MusicBrainz Disc Id": "musicbrainz_discid",
        "----:com.apple.iTunes:MusicBrainz TRM Id": "musicbrainz_trmid",
        "----:com.apple.iTunes:MusicBrainz Work Id": "musicbrainz_workid",
        "----:com.apple.iTunes:MusicBrainz Release Group Id": "musicbrainz_releasegroupid",
        "----:com.apple.iTunes:MusicBrainz Release Track Id": "musicbrainz_trackid",
        "----:com.apple.iTunes:MusicBrainz Original Album Id": "musicbrainz_originalalbumid",
        "----:com.apple.iTunes:MusicBrainz Original Artist Id": "musicbrainz_originalartistid",
        "----:com.apple.iTunes:Acoustid Fingerprint": "acoustid_fingerprint",
        "----:com.apple.iTunes:Acoustid Id": "acoustid_id",
        "----:com.apple.iTunes:ASIN": "asin",
        "----:com.apple.iTunes:BARCODE": "barcode",
        "----:com.apple.iTunes:PRODUCER": "producer",
        "----:com.apple.iTunes:LYRICIST": "lyricist",
        "----:com.apple.iTunes:CONDUCTOR": "conductor",
        "----:com.apple.iTunes:ENGINEER": "engineer",
        "----:com.apple.iTunes:MIXER": "mixer",
        "----:com.apple.iTunes:DJMIXER": "djmixer",
        "----:com.apple.iTunes:REMIXER": "remixer",
        "----:com.apple.iTunes:ISRC": "isrc",
        "----:com.apple.iTunes:MEDIA": "media",
        "----:com.apple.iTunes:LABEL": "label",
        "----:com.apple.iTunes:LICENSE": "license",
        "----:com.apple.iTunes:CATALOGNUMBER": "catalognumber",
        "----:com.apple.iTunes:SUBTITLE": "subtitle",
        "----:com.apple.iTunes:DISCSUBTITLE": "discsubtitle",
        "----:com.apple.iTunes:MOOD": "mood",
        "----:com.apple.iTunes:SCRIPT": "script",
        "----:com.apple.iTunes:LANGUAGE": "language",
        "----:com.apple.iTunes:ARTISTS": "artists",
        "----:com.apple.iTunes:WORK": "work",
        "----:com.apple.iTunes:initialkey": "key",
    }
    __r_freeform_tags = dict([(v, k) for k, v in __freeform_tags.items()])

    __other_supported_tags = ("discnumber", "tracknumber",
                              "totaldiscs", "totaltracks")

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        file = MP4(encode_filename(filename))
        tags = file.tags
        if tags is None:
            file.add_tags()

        metadata = Metadata()
        for name, values in tags.items():
            if name in self.__text_tags:
                for value in values:
                    metadata.add(self.__text_tags[name], value)
            elif name in self.__bool_tags:
                metadata.add(self.__bool_tags[name], values and '1' or '0')
            elif name in self.__int_tags:
                for value in values:
                    metadata.add(self.__int_tags[name], str(value))
            elif name in self.__freeform_tags:
                for value in values:
                    value = value.decode("utf-8", "replace").strip("\x00")
                    metadata.add(self.__freeform_tags[name], value)
            elif name == "----:com.apple.iTunes:fingerprint":
                for value in values:
                    value = value.decode("utf-8", "replace").strip("\x00")
                    if value.startswith("MusicMagic Fingerprint"):
                        metadata.add("musicip_fingerprint", value[22:])
            elif name == "trkn":
                metadata["tracknumber"] = str(values[0][0])
                metadata["totaltracks"] = str(values[0][1])
            elif name == "disk":
                metadata["discnumber"] = str(values[0][0])
                metadata["totaldiscs"] = str(values[0][1])
            elif name == "covr":
                for value in values:
                    if value.imageformat not in (value.FORMAT_JPEG,
                                                 value.FORMAT_PNG):
                        continue
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            data=value,
                        )
                    except CoverArtImageError as e:
                        log.error('Cannot load image from %r: %s' %
                                  (filename, e))
                    else:
                        metadata.images.append(coverartimage)

        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        file = MP4(encode_filename(self.filename))
        tags = file.tags
        if tags is None:
            file.add_tags()

        if config.setting["clear_existing_tags"]:
            tags.clear()

        for name, values in metadata.rawitems():
            if name.startswith('lyrics:'):
                name = 'lyrics'
            if name in self.__r_text_tags:
                tags[self.__r_text_tags[name]] = values
            elif name in self.__r_bool_tags:
                tags[self.__r_bool_tags[name]] = (values[0] == '1')
            elif name in self.__r_int_tags:
                try:
                    tags[self.__r_int_tags[name]] = [int(value) for value in values]
                except ValueError:
                    pass
            elif name in self.__r_freeform_tags:
                values = [v.encode("utf-8") for v in values]
                tags[self.__r_freeform_tags[name]] = values
            elif name == "musicip_fingerprint":
                tags["----:com.apple.iTunes:fingerprint"] = [b"MusicMagic Fingerprint%s" % v.encode('ascii') for v in values]

        if "tracknumber" in metadata:
            if "totaltracks" in metadata:
                tags["trkn"] = [(int(metadata["tracknumber"]),
                                 int(metadata["totaltracks"]))]
            else:
                tags["trkn"] = [(int(metadata["tracknumber"]), 0)]

        if "discnumber" in metadata:
            if "totaldiscs" in metadata:
                tags["disk"] = [(int(metadata["discnumber"]),
                                 int(metadata["totaldiscs"]))]
            else:
                tags["disk"] = [(int(metadata["discnumber"]), 0)]

        covr = []
        for image in metadata.images.to_be_saved_to_tags():
            if image.mimetype == "image/jpeg":
                covr.append(MP4Cover(image.data, MP4Cover.FORMAT_JPEG))
            elif image.mimetype == "image/png":
                covr.append(MP4Cover(image.data, MP4Cover.FORMAT_PNG))
        if covr:
            tags["covr"] = covr

        self._remove_deleted_tags(metadata, tags)

        file.save()

    def _remove_deleted_tags(self, metadata, tags):
        """Remove the tags from the file that were deleted in the UI"""
        for tag in metadata.deleted_tags:
            real_name = self._get_tag_name(tag)
            if real_name and real_name in tags:
                if tag not in ("totaltracks", "totaldiscs"):
                    del tags[real_name]

    @classmethod
    def supports_tag(cls, name):
        return (name in cls.__r_text_tags
                or name in cls.__r_bool_tags
                or name in cls.__r_freeform_tags
                or name in cls.__r_int_tags
                or name in cls.__other_supported_tags
                or name.startswith('lyrics:')
                or name in ('~length', 'musicip_fingerprint'))

    def _get_tag_name(self, name):
        if name.startswith('lyrics:'):
            return 'lyrics'
        if name in self.__r_text_tags:
            return self.__r_text_tags[name]
        elif name in self.__r_bool_tags:
            return self.__r_bool_tags[name]
        elif name in self.__r_int_tags:
            return self.__r_int_tags[name]
        elif name in self.__r_freeform_tags:
            return self.__r_freeform_tags[name]
        elif name == "musicip_fingerprint":
            return "----:com.apple.iTunes:fingerprint"
        elif name in ("tracknumber", "totaltracks"):
            return "trkn"
        elif name in ("discnumber", "totaldiscs"):
            return "disk"
        else:
            return None

    def _info(self, metadata, file):
        super()._info(metadata, file)
        if hasattr(file.info, 'codec_description') and file.info.codec_description:
            metadata['~format'] = "%s (%s)" % (metadata['~format'], file.info.codec_description)

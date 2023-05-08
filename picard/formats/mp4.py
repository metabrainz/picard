# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2009-2011, 2015, 2018-2022 Philipp Wolfer
# Copyright (C) 2011 Johannes Weißl
# Copyright (C) 2011-2014 Wieland Hoffmann
# Copyright (C) 2012-2013 Michael Wiencek
# Copyright (C) 2013 Calvin Walton
# Copyright (C) 2013 Frederik “Freso” S. Olesen
# Copyright (C) 2013-2014, 2018-2021 Laurent Monin
# Copyright (C) 2014-2015 Sophist-UK
# Copyright (C) 2016-2018 Sambhav Kothari
# Copyright (C) 2019 Reinaldo Antonio Camargo Rauch
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


import re

from mutagen.mp4 import (
    MP4,
    MP4Cover,
)

from picard import log
from picard.config import get_config
from picard.coverart.image import (
    CoverArtImageError,
    TagCoverArtImage,
)
from picard.file import File
from picard.formats.mutagenext import delall_ci
from picard.metadata import Metadata
from picard.util import encode_filename


def _add_text_values_to_metadata(metadata, name, values):
    for value in values:
        metadata.add(name, value.decode("utf-8", "replace").strip("\x00"))


_VALID_KEY_CHARS = re.compile('^[\x00-\xff]+$')
UNSUPPORTED_TAGS = {'r128_album_gain', 'r128_track_gain'}


def _is_valid_key(key):
    """
    Return true if a string is a valid name for a custom tag.
    """
    return bool(_VALID_KEY_CHARS.match(key))


class MP4File(File):
    EXTENSIONS = [".m4a", ".m4b", ".m4p", ".m4v", ".m4r", ".mp4"]
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
        "\xa9cmt": "comment",
        "\xa9too": "encodedby",
        "\xa9dir": "director",
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
    __r_text_tags = {v: k for k, v in __text_tags.items()}

    __bool_tags = {
        "pcst": "podcast",
        "cpil": "compilation",
        "pgap": "gapless",
    }
    __r_bool_tags = {v: k for k, v in __bool_tags.items()}

    __int_tags = {
        "tmpo": "bpm",
        "\xa9mvi": "movementnumber",
        "\xa9mvc": "movementtotal",
        "shwm": "showmovement",
    }
    __r_int_tags = {v: k for k, v in __int_tags.items()}

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
    __r_freeform_tags = {v: k for k, v in __freeform_tags.items()}

    # Tags to load case insensitive. Case is preserved, but the specified case
    # is written if it is unset.
    __r_freeform_tags_ci = {
        "replaygain_album_gain": "----:com.apple.iTunes:REPLAYGAIN_ALBUM_GAIN",
        "replaygain_album_peak": "----:com.apple.iTunes:REPLAYGAIN_ALBUM_PEAK",
        "replaygain_album_range": "----:com.apple.iTunes:REPLAYGAIN_ALBUM_RANGE",
        "replaygain_track_gain": "----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN",
        "replaygain_track_peak": "----:com.apple.iTunes:REPLAYGAIN_TRACK_PEAK",
        "replaygain_track_range": "----:com.apple.iTunes:REPLAYGAIN_TRACK_RANGE",
        "replaygain_reference_loudness": "----:com.apple.iTunes:REPLAYGAIN_REFERENCE_LOUDNESS",
        "releasedate": "----:com.apple.iTunes:RELEASEDATE",
    }
    __freeform_tags_ci = {b.lower(): a for a, b in __r_freeform_tags_ci.items()}

    __other_supported_tags = ("discnumber", "tracknumber",
                              "totaldiscs", "totaltracks")

    def __init__(self, filename):
        super().__init__(filename)
        self.__casemap = {}

    def _load(self, filename):
        log.debug("Loading file %r", filename)
        self.__casemap = {}
        file = MP4(encode_filename(filename))
        tags = file.tags or {}
        metadata = Metadata()
        for name, values in tags.items():
            name_lower = name.lower()
            if name in self.__text_tags:
                for value in values:
                    metadata.add(self.__text_tags[name], value)
            elif name in self.__bool_tags:
                metadata.add(self.__bool_tags[name], values and '1' or '0')
            elif name in self.__int_tags:
                for value in values:
                    metadata.add(self.__int_tags[name], value)
            elif name in self.__freeform_tags:
                tag_name = self.__freeform_tags[name]
                _add_text_values_to_metadata(metadata, tag_name, values)
            elif name_lower in self.__freeform_tags_ci:
                tag_name = self.__freeform_tags_ci[name_lower]
                self.__casemap[tag_name] = name
                _add_text_values_to_metadata(metadata, tag_name, values)
            elif name == "----:com.apple.iTunes:fingerprint":
                for value in values:
                    value = value.decode("utf-8", "replace").strip("\x00")
                    if value.startswith("MusicMagic Fingerprint"):
                        metadata.add("musicip_fingerprint", value[22:])
            elif name == "trkn":
                try:
                    metadata["tracknumber"] = values[0][0]
                    metadata["totaltracks"] = values[0][1]
                except IndexError:
                    log.debug('trkn is invalid, ignoring')
            elif name == "disk":
                try:
                    metadata["discnumber"] = values[0][0]
                    metadata["totaldiscs"] = values[0][1]
                except IndexError:
                    log.debug('disk is invalid, ignoring')
            elif name == "covr":
                for value in values:
                    if value.imageformat not in {value.FORMAT_JPEG, value.FORMAT_PNG}:
                        continue
                    try:
                        coverartimage = TagCoverArtImage(
                            file=filename,
                            tag=name,
                            data=value,
                        )
                    except CoverArtImageError as e:
                        log.error('Cannot load image from %r: %s', filename, e)
                    else:
                        metadata.images.append(coverartimage)
            # Read other freeform tags always case insensitive
            elif name.startswith('----:com.apple.iTunes:'):
                tag_name = name_lower[22:]
                self.__casemap[tag_name] = name[22:]
                if (name not in self.__r_text_tags
                    and name not in self.__r_bool_tags
                    and name not in self.__r_int_tags
                    and name not in self.__r_freeform_tags
                    and name_lower not in self.__r_freeform_tags_ci
                    and name not in self.__other_supported_tags):
                    _add_text_values_to_metadata(metadata, tag_name, values)

        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file %r", filename)
        config = get_config()
        file = MP4(encode_filename(self.filename))
        if file.tags is None:
            file.add_tags()
        tags = file.tags

        if config.setting["clear_existing_tags"]:
            cover = tags.get('covr') if config.setting['preserve_images'] else None
            tags.clear()
            if cover:
                tags['covr'] = cover

        for name, values in metadata.rawitems():
            if name.startswith('lyrics:'):
                name = 'lyrics'
            if name == 'comment:':
                name = 'comment'
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
            elif name in self.__r_freeform_tags_ci:
                values = [v.encode("utf-8") for v in values]
                delall_ci(tags, self.__r_freeform_tags_ci[name])
                if name in self.__casemap:
                    name = self.__casemap[name]
                else:
                    name = self.__r_freeform_tags_ci[name]
                tags[name] = values
            elif name == "musicip_fingerprint":
                tags["----:com.apple.iTunes:fingerprint"] = [b"MusicMagic Fingerprint%s" % v.encode('ascii') for v in values]
            elif self.supports_tag(name) and name not in self.__other_supported_tags:
                values = [v.encode("utf-8") for v in values]
                name = self.__casemap.get(name, name)
                tags['----:com.apple.iTunes:' + name] = values

        if "tracknumber" in metadata:
            try:
                tracknumber = int(metadata["tracknumber"])
            except ValueError:
                pass
            else:
                totaltracks = 0
                if "totaltracks" in metadata:
                    try:
                        totaltracks = int(metadata["totaltracks"])
                    except ValueError:
                        pass
                tags["trkn"] = [(tracknumber, totaltracks)]

        if "discnumber" in metadata:
            try:
                discnumber = int(metadata["discnumber"])
            except ValueError:
                pass
            else:
                totaldiscs = 0
                if "totaldiscs" in metadata:
                    try:
                        totaldiscs = int(metadata["totaldiscs"])
                    except ValueError:
                        pass
                tags["disk"] = [(discnumber, totaldiscs)]

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
                if tag not in {"totaltracks", "totaldiscs"}:
                    del tags[real_name]

    @classmethod
    def supports_tag(cls, name):
        return (name
                and not name.startswith("~")
                and name not in UNSUPPORTED_TAGS
                and not (name.startswith('comment:') and len(name) > 9)
                and not name.startswith('performer:')
                and _is_valid_key(name))

    def _get_tag_name(self, name):
        if name.startswith('lyrics:'):
            name = 'lyrics'
        if name in self.__r_text_tags:
            return self.__r_text_tags[name]
        elif name in self.__r_bool_tags:
            return self.__r_bool_tags[name]
        elif name in self.__r_int_tags:
            return self.__r_int_tags[name]
        elif name in self.__r_freeform_tags:
            return self.__r_freeform_tags[name]
        elif name in self.__r_freeform_tags_ci:
            return self.__r_freeform_tags_ci[name]
        elif name == "musicip_fingerprint":
            return "----:com.apple.iTunes:fingerprint"
        elif name in {"tracknumber", "totaltracks"}:
            return "trkn"
        elif name in {"discnumber", "totaldiscs"}:
            return "disk"
        elif self.supports_tag(name) and name not in self.__other_supported_tags:
            name = self.__casemap.get(name, name)
            return '----:com.apple.iTunes:' + name

    def _info(self, metadata, file):
        super()._info(metadata, file)
        if hasattr(file.info, 'codec_description') and file.info.codec_description:
            metadata['~format'] = "%s (%s)" % (metadata['~format'], file.info.codec_description)
        filename = file.filename
        if isinstance(filename, bytes):
            filename = filename.decode()
        if filename.lower().endswith(".m4v") or (file.tags and 'hdvd' in file.tags):
            metadata['~video'] = '1'

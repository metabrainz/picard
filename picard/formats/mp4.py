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

from picard import config, log
from picard.const import TIMESTAMP_FORMAT
from picard.coverart.image import TagCoverArtImage, CoverArtImageError
from picard.file import File
from picard.metadata import Metadata
from picard.util import encode_filename, pack_performer, unpack_performer, sanitize_date

from mutagen.mp4 import MP4, MP4Cover

from os import path
from time import strftime, gmtime, gmtime


# iTunes metadata is the de-facto standard for mp4 files however the apple
# specification is not publicly available, and apple documentation that is
# circulating was never approved.
#
# The most definitive definitions of iTunes metadata found so far are at:
#   https://code.google.com/p/mp4v2/wiki/iTunesMetadata
#   http://atomicparsley.sourceforge.net/mpeg-4files.html
#
# This version of mp4 support is based on these web pages.

class MP4File(File):
    EXTENSIONS = [".m4a", ".m4b", ".m4p", ".m4v", ".mp4"]
    NAME = "MPEG-4 Audio"

    __load_text_tags = {
        "\xa9alb": "album",
        "\xa9ART": "artist",
        "\xa9nam": "title",
        "\xa9wrt": "composer",
        "aART": "albumartist",
        "\xa9grp": "grouping",
        "\xa9day": "date",
        "\xa9enc": "encodedby",
        "\xa9gen": "genre",
        "\xa9lyr": "lyrics",
        "\xa9cmt": "comment",
        "\xa9too": "encodedby",
        "\xa9phg": "recordingcopyright",
        "\xa9prf": "performer",
        "catg": "category",
        "cprt": "copyright",
        "keyw": "keywords",
        "soal": "albumsort",
        "soaa": "albumartistsort",
        "soar": "artistsort",
        "sonm": "titlesort",
        "soco": "composersort",
        "sosn": "showsort",
        "tvsh": "show",
        "purl": "podcasturl",
        "\xa9arg": "arranger", # iTunes Metadata spec. rather than Jaikoz
        "\xa9con": "conductor", # iTunes Metadata spec. rather than Jaikoz
        "\xa9sne": "engineer", # iTunes Metadata spec. rather than Jaikoz
        "\xa9mak": "label", # iTunes Metadata spec. rather than Jaikoz
        "\xa9ope": "originalartist", # iTunes Metadata spec. rather than Jaikoz
        "\xa9phg": "recordingcopyright", # iTunes Metadata spec.
        "\xa9prd": "producer", # iTunes Metadata spec. rather than Jaikoz
        "\xa9st3": "subtitle", # iTunes Metadata spec. rather than Jaikoz
        "\xa9too": "encodersettings", # iTunes Metadata spec.
        "rate": "~rating", # iTunes Metadata spec.
    }
    __save_text_tags = dict([(v, k) for k, v in __load_text_tags.iteritems()])

    __load_bool_tags = {
        "pcst": "podcast",
        "cpil": "compilation",
        "pgap": "playdelay",
    }
    __save_bool_tags = dict([(v, k) for k, v in __load_bool_tags.iteritems()])

    __load_int_tags = {
        "tmpo": "bpm",
    }
    __save_int_tags = dict([(v, k) for k, v in __load_int_tags.iteritems()])

    __load_freetext_tags = {
        "----:com.apple.iTunes:Acoustid Fingerprint": "acoustid_fingerprint",
        "----:com.apple.iTunes:Acoustid Id": "acoustid_id",
        "----:com.apple.iTunes:ALBUMARTISTS": "albumartists",
        "----:com.apple.iTunes:AlbumGenre": "albumgenre",
        "----:com.apple.iTunes:AlbumRating": "albumrating",
        "----:com.apple.iTunes:ARTISTS": "artists",
        "----:com.apple.iTunes:ASIN": "asin",
        "----:com.apple.iTunes:BARCODE": "barcode",
        "----:com.apple.iTunes:CATALOGNUMBER": "catalognumber",
        "----:com.apple.iTunes:Country": "country",
        "----:com.apple.iTunes:DISCSUBTITLE": "discsubtitle",
        "----:com.apple.iTunes:DJMIXER": "djmixer",
        "----:com.apple.iTunes:EncodingTime": "encodingtime",
        "----:com.apple.iTunes:fingerprint": "musicip_fingerprint",
        "----:com.apple.iTunes:fBPM": "bpm",
        "----:com.apple.iTunes:initialkey": "key",
        "----:com.apple.iTunes:ISRC": "isrc",
        "----:com.apple.iTunes:LANGUAGE": "language",
        "----:com.apple.iTunes:LICENSE": "license",
        "----:com.apple.iTunes:LYRICIST": "lyricist",
        "----:com.apple.iTunes:MEDIA": "media",
        "----:com.apple.iTunes:MIXER": "mixer",
        "----:com.apple.iTunes:MOOD": "mood",
        "----:com.apple.iTunes:MusicBrainz Album Artist Id": "musicbrainz_albumartistid",
        "----:com.apple.iTunes:MusicBrainz Album Id": "musicbrainz_albumid",
        "----:com.apple.iTunes:MusicBrainz Album Release Country": "releasecountry",
        "----:com.apple.iTunes:MusicBrainz Album Status": "releasestatus",
        "----:com.apple.iTunes:MusicBrainz Album Type": "releasetype",
        "----:com.apple.iTunes:MusicBrainz Artist Id": "musicbrainz_artistid",
        "----:com.apple.iTunes:MusicBrainz Disc Id": "musicbrainz_discid",
        "----:com.apple.iTunes:MusicBrainz Label Id": "musicbrainz_labelid",
        "----:com.apple.iTunes:MusicBrainz Original Album Id": "musicbrainz_original_albumid",
        "----:com.apple.iTunes:MusicBrainz Original Artist Id": "musicbrainz_original_artistid",
        "----:com.apple.iTunes:MusicBrainz Recording Id": "musicbrainz_recordingid",
        "----:com.apple.iTunes:MusicBrainz Release Group Id": "musicbrainz_releasegroupid",
        "----:com.apple.iTunes:MusicBrainz Track Id": "musicbrainz_trackid",
        "----:com.apple.iTunes:MusicBrainz Work Id": "musicbrainz_workid",
        "----:com.apple.iTunes:MusicIP PUID": "musicip_puid",
        "----:com.apple.iTunes:OCCASION": "occasion",
        "----:com.apple.iTunes:ORIGINAL ALBUM": "originalalbum",
        "----:com.apple.iTunes:ORIGINAL LYRICIST": "originallyricist",
        "----:com.apple.iTunes:ORIGINAL YEAR": "originaldate",
        "----:com.apple.iTunes:OriginalYear": "originalyear",
        "----:com.apple.iTunes:PlayDelay": "playdelay",
        "----:com.apple.iTunes:QUALITY": "quality",
        "----:com.apple.iTunes:RecordingDate": "recordingdate",
        "----:com.apple.iTunes:RecordingLocation": "recordinglocation",
        "----:com.apple.iTunes:REMIXER": "remixer",
        "----:com.apple.iTunes:SCRIPT": "script",
        "----:com.apple.iTunes:TaggedDate": "~tagtime",
        "----:com.apple.iTunes:TEMPO": "tempo",
        "----:com.apple.iTunes:WORK": "work",
        "----:com.apple.iTunes:WRITER": "writer",
        "----:com.apple.iTunes:YEAR": "year",
        "----:com.apple.iTunes:URL_COVERART_SITE": "web_coverart",
        "----:com.apple.iTunes:URL_DISCOGS_ARTIST_SITE": "web_discogs_artist",
        "----:com.apple.iTunes:URL_DISCOGS_LABEL_SITE": "web_discogs_label",
        "----:com.apple.iTunes:URL_DISCOGS_RELEASE_SITE": "web_discogs_release",
        "----:com.apple.iTunes:URL_DISCOGS_MASTER_SITE": "web_discogs_releasegroup",
        "----:com.apple.iTunes:URL_LYRICS_SITE": "web_lyrics",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_ARTIST_SITE": "web_musicbrainz_artist",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_LABEL_SITE": "web_musicbrainz_label",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_RECORDING_SITE": "web_musicbrainz_recording",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_RELEASE_SITE": "web_musicbrainz_release",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_RELEASEGROUP_SITE": "web_musicbrainz_releasegroup",
        "----:com.apple.iTunes:URL_MUSICBRAINZ_WORK_SITE": "web_musicbrainz_work",
        "----:com.apple.iTunes:URL_OFFICIAL_ARTIST_SITE": "web_official_artist",
        "----:com.apple.iTunes:URL_OFFICIAL_LABEL_SITE": "web_official_label",
        "----:com.apple.iTunes:URL_OFFICIAL_RELEASE_SITE": "web_official_release",
        "----:com.apple.iTunes:URL_WIKIPEDIA_ARTIST_SITE": "web_wikipedia_artist",
        "----:com.apple.iTunes:URL_WIKIPEDIA_LABEL_SITE": "web_wikipedia_label",
        "----:com.apple.iTunes:URL_WIKIPEDIA_RELEASE_SITE": "web_wikipedia_release",
        "----:com.apple.iTunes:URL_WIKIPEDIA_WORK_SITE": "web_wikipedia_work",
    }
    __save_freetext_tags = dict([(v, k) for k, v in __load_freetext_tags.iteritems()])

    __load_tags_with_description = {
        "\xa9lyr": "lyrics",
        "\xa9cmt": "comment",
        "\xa9prf": "performer",
    }
    __save_tags_with_description = dict([(v, k) for k, v in __load_tags_with_description.iteritems()])

    __other_supported_tags = ["discnumber", "tracknumber",
                              "totaldiscs", "totaltracks"]

    _supported_tags = __save_text_tags.keys() + __save_bool_tags.keys() \
        + __save_freetext_tags.keys() + __other_supported_tags

    __compatibility = {
        "----:com.apple.iTunes:ARRANGER": "\xa9arg", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:CONDUCTOR": "\xa9con", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:ENGINEER": "\xa9sne", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:LABEL": "\xa9mak", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:ORIGINAL ARTIST": "\xa9ope", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:PRODUCER": "\xa9prd", # iTunes Metadata spec. rather than Jaikoz
        "----:com.apple.iTunes:SUBTITLE": "\xa9st3", # iTunes Metadata spec. rather than Jaikoz

        "----:com.apple.iTunes:DISCNUMBER": "disk", # mediamonkey compatibility
        "----:com.apple.iTunes:TRACKNUMBER": "trkn", # mediamonkey compatibility
        "----:com.apple.iTunes:INVOLVED PEOPLE": "\xa9prf", # mediamonkey compatibility
        "----:com.apple.iTunes:KEYWORDS": "keyw", # mediamonkey compatibility
        "----:com.apple.iTunes:ORGANIZATION": "\xa9mak", # mediamonkey compatibility
        "----:com.apple.iTunes:ORIGINAL DATE": "----:com.apple.iTunes:ORIGINAL YEAR", # mediamonkey compatibility
        "----:com.apple.iTunes:PUBLISHER": "\xa9mak", # mediamonkey compatibility

        '----:com.apple.iTunes:MusicBrainz TRM Id': "", # Obsolete Picard Tag
        '----:com.apple.iTunes:MusicBrainz Album Artist Sortname': "soaa", # Picard 0.70
        '----:com.apple.iTunes:MusicBrainz Album Artist': "aART", # Picard 0.70
        '----:com.apple.iTunes:MusicBrainz Album Release Date': "\xa9day", # Picard 0.70
        '----:com.apple.iTunes:MusicBrainz Sortname': "soar", # Picard 0.70
        '----:com.apple.iTunes:MusicBrainz Non-Album': "", # Picard 0.70
        #'----:com.apple.iTunes:fingerprint': "", # Obsolete Picard Tag
    }

    __prefix = '----:com.apple.iTunes:'
    for new_key in __load_freetext_tags:
        key = new_key[len(__prefix):]
        if key.lower() != key and __prefix + key.lower() not in __compatibility:
            __compatibility[__prefix + key.lower()] = new_key
        if key.upper() != key and __prefix + key.upper() not in __compatibility:
            __compatibility[__prefix + key.upper()] = new_key
        if key.title() != key and __prefix + key.title() not in __compatibility:
            __compatibility[__prefix + key.title()] = new_key

    __load_date_tags = [
        "\xa9day",
        "----:com.apple.iTunes:ORIGINAL YEAR",
        "----:com.apple.iTunes:RecordingDate",
        "----:com.apple.iTunes:TaggedDate",
    ]

    def _load(self, filename):
        log.debug("Loading file: %r", filename)
        file = MP4(encode_filename(filename))
        if file.tags is None:
            file.add_tags()
        tags = file.tags

        # Fix old tag naming and make it compatible with Jaikoz
        # From 1.3 ReleaseTrackID exists - before 1.3 only TrackID
        if ('----:com.apple.iTunes:MusicBrainz Recording Id' not in tags
                and '----:com.apple.iTunes:MusicBrainz Track Id' in tags):
            tags['----:com.apple.iTunes:MusicBrainz Recording Id'] = tags['----:com.apple.iTunes:MusicBrainz Track Id']
            if '----:com.apple.iTunes:MusicBrainz Release Track Id' in tags:
                log.info('MP4: File %r: Upgrading obsolete MBID tags ReleaseTrackId->TrackId->RecordingID',
                    path.split(filename)[1])
                tags['----:com.apple.iTunes:MusicBrainz Track Id'] = tags['----:com.apple.iTunes:MusicBrainz Release Track Id']
            else:
                log.info('MP4: File %r: Upgrading obsolete MBID tags TrackId->RecordingID',
                    path.split(filename)[1])
                del tags['----:com.apple.iTunes:MusicBrainz Track Id']
        # Delete releasetrackid if it still exists since recordingid, trackid will be populated from MB
        if '----:com.apple.iTunes:MusicBrainz Release Track Id'in tags:
            del tags['----:com.apple.iTunes:MusicBrainz Release Track Id']

        for old, new in self.__compatibility.iteritems():
            if old not in tags:
                continue
            if new:
                if (new in tags
                        and old != '----:com.apple.iTunes:MusicBrainz Album Release Date'
                        and new != "\xa9day"): # Picard 0.70 has Year in \xa9da
                    log.warning('MP4: File %r: Cannot upgrade tag - new tag already exists: %r=>%r',
                        path.split(filename)[1], old, new)
                    continue
                tags[new] = tags[old]
                log.info('MP4: File %r: Upgrading tag: %r=>%r',
                    path.split(filename)[1], old, new)
            del tags[old]

        metadata = Metadata()
        for name, values in tags.items():
            if name in self.__load_date_tags:
                values = [sanitize_date(v) for v in values]
            if name == "covr":
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
                        log.error('MP4: File %r: Cannot load image: %s', filename, e)
                    else:
                        metadata.append_image(coverartimage)
            elif name == "trkn":
                metadata["tracknumber"] = str(values[0][0])
                if len(values[0]) > 1:
                    metadata["totaltracks"] = str(values[0][1])
            elif name == "disk":
                metadata["discnumber"] = str(values[0][0])
                if len(values[0]) > 1:
                    metadata["totaldiscs"] = str(values[0][1])
            elif name == 'rate':
                # Unclear what should happen if config.setting['enable_ratings'] == False
                # Rating in WMA ranges from 0 to 99, normalize this to the range 0 to 5
                metadata["~rating"] = int(round(float(unicode(values[0])) / 99.0 * (config.setting['rating_steps'] - 1)))
            elif name in self.__load_tags_with_description:
                tag = self.__load_tags_with_description[name]
                for value in values:
                    desc, value = unpack_performer(value)
                    if desc or tag == 'performer':
                        metadata.add('%s:%s' % (tag, desc), value)
                    else:
                        metadata.add(tag, value)
            elif name in self.__load_text_tags:
                metadata[self.__load_text_tags[name]] = \
                    [v.strip("\x00").decode("utf-8", "replace") for v in values]
            elif name == "----:com.apple.iTunes:fingerprint":
                name = self.__load_freetext_tags[name]
                for value in values:
                    value = value.strip("\x00").decode("utf-8", "replace")
                    if value.startswith("MusicMagic Fingerprint"):
                        metadata.add("musicip_fingerprint", value[22:])
                    else:
                        metadata.add('~mp4:%s' % name, value)
                        log.info('MP4: File %r: Loading MP4 specific fingerprint: %s=%r',
                            path.split(filename)[1], name[22:], values)
            elif name in self.__load_bool_tags:
                if name == 'pgap':
                    # gapless == true => playdelay = 0
                    # gapless == false does not tell us the gap length
                    if values and 'playdelay' not in metadata:
                        metadata['playdelay'] = '0'
                    continue
                metadata[self.__load_bool_tags[name]] = values and '1' or '0'
            elif name in self.__load_int_tags:
                name = self.__load_int_tags[name]
                if name not in metadata:
                    metadata[name] = values
            elif name.startswith('----:com.apple.iTunes:'):
                values = [v.strip("\x00").decode("utf-8", "replace") for v in values]
                if name in self.__load_freetext_tags:
                    name = self.__load_freetext_tags[name]
                elif name[22:].lower() not in self._supported_tags:
                    log.info('MP4: File %r: Loading user metadata: %s=%r', path.split(filename)[1], name, values)
                    name = name[22:].lower()
                else:
                    log.info('MP4: File %r: Loading MP4 specific metadata which conflicts with known Picard tag: %s=%r',
                        path.split(filename)[1], name[22:], values)
                    name = '~mp4:%s' % name
                metadata[name] = values
            else:
                values = [v.strip("\x00").decode("utf-8", "replace") for v in values]
                log.info('MP4: File %r: Loading unknown MP4 metadata: %s=%r',
                    path.split(filename)[1], name, values)
                metadata['~mp4:%s' % name] = values

        self._info(metadata, file)
        return metadata

    def _save(self, filename, metadata):
        log.debug("Saving file: %r", filename)
        file = MP4(encode_filename(self.filename))
        if file.tags is None:
            file.add_tags()
        tags = file.tags

        if config.setting["clear_existing_tags"]:
            tags.clear()

        performers = []
        comments = []
        lyrics = []
        for name, values in metadata.rawitems():
            if name == "musicip_fingerprint":
                tags["----:com.apple.iTunes:fingerprint"] = ["MusicMagic Fingerprint%s" % str(v) for v in values]
            elif name == "~rating":
                # Unclear what should happen if config.setting['enable_ratings'] == False
                tags["rate"] = str(float(values[0]) * 99.0 / (config.setting['rating_steps'] - 1))
            elif name.startswith("comment:") or name == "comment":
                name, desc = name.split(':', 1) if ':' in name else (name, '')
                for value in values:
                    if desc:
                        comments.append('%s=%s' % (desc, value))
                    else:
                        comments.insert(0, value)
            elif name.startswith("lyrics:") or name == "lyrics":
                name, desc = name.split(':', 1) if ':' in name else (name, '')
                for value in values:
                    if desc:
                        lyrics.append('%s=%s' % (desc, value))
                    else:
                        lyrics.insert(0, value)
            elif name.startswith("performer:"):
                name, role = name.split(':', 1)
                for value in values:
                    if 'vocal' in role:
                        performers.insert(0, pack_performer(role, value))
                    else:
                        performers.append(pack_performer(role, value))
            else:
                if name in self.__save_text_tags:
                    tags[self.__save_text_tags[name]] = values
                if name in self.__save_freetext_tags:
                    tag = self.__save_freetext_tags[name]
                    values = [v.encode("utf-8") for v in values]
                    tags[tag] = values
                if name in self.__save_bool_tags:
                    if name == 'playdelay':
                        # convert to gapless boolean
                        values = ['1' if values[0] == '0' else '0']
                    tags[self.__save_bool_tags[name]] = (values[0] == '1')
                if name in self.__save_int_tags:
                    try:
                        tags[self.__save_int_tags[name]] = [int(float(value)) for value in values]
                    except ValueError:
                        pass
                if name not in self._supported_tags and not name.startswith('~'):
                    tag = "----:com.apple.iTunes:%s" % name.upper()
                    values = [v.encode("utf-8") for v in values]
                    tags[tag] = values
                    log.info('MP4: File %r: Saving user metadata: %s=%r', path.split(filename)[1], name, values)
                if name.startswith('~mp4:'):
                    values = [v.encode("utf-8") for v in values]
                    name = name[5:]
                    tags[name] = (tags[name] + values) if name in tags else values
                    log.info('MP4: File %r: Saving unknown MP4 metadata: %s=%r',
                        path.split(filename)[1], name, tags[name])

        if comments:
            tags["\xa9cmt"] = comments
        if lyrics:
            tags["\xa9lyr"] = lyrics
        if performers:
            tags["\xa9prf"] = performers

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
        for image in metadata.images_to_be_saved_to_tags:
            if image.mimetype == "image/jpeg":
                covr.append(MP4Cover(image.data, MP4Cover.FORMAT_JPEG))
            elif image.mimetype == "image/png":
                covr.append(MP4Cover(image.data, MP4Cover.FORMAT_PNG))
        if covr:
            tags["covr"] = covr

        tags[self.__save_freetext_tags["~tagtime"]] = strftime(TIMESTAMP_FORMAT, gmtime())

        file.save()


    def _info(self, metadata, file):
        super(MP4File, self)._info(metadata, file)
        if hasattr(file.info, 'codec') and file.info.codec_description:
            metadata['~format'] = "%s (%s)" % (metadata['~format'], file.info.codec_description)
        if hasattr(file.info, 'codec_description') and file.info.codec:
            metadata['~codec'] = file.info.codec
